# 🔧 Supabase Setup Guide for Billfrog

This guide will walk you through setting up Supabase for email delivery with Billfrog.

## Prerequisites

- A Supabase account ([supabase.com](https://supabase.com))
- An email service provider (Resend, SendGrid, Mailgun, etc.)

## Step 1: Create Supabase Project

1. Go to [supabase.com](https://supabase.com) and sign in
2. Click "New Project"
3. Choose your organization and set project details:
   - **Name**: `billfrog-email`
   - **Database Password**: Generate a secure password
   - **Region**: Choose closest to your location
4. Click "Create new project"

## Step 2: Get Project Credentials

1. In your Supabase dashboard, go to **Settings** > **API**
2. Copy the following values:
   - **Project URL** (looks like `https://xxx.supabase.co`)
   - **Service Role Key** (starts with `eyJ...`)

⚠️ **Important**: Use the **service role key**, not the anon public key!

## Step 3: Choose Email Provider

Billfrog supports any email provider through Supabase Edge Functions. Here are popular options:

### Option A: Resend (Recommended)

1. Sign up at [resend.com](https://resend.com)
2. Get your API key from the dashboard
3. Add your domain (or use their test domain)

### Option B: SendGrid

1. Sign up at [sendgrid.com](https://sendgrid.com)
2. Create an API key with "Mail Send" permissions
3. Verify your sender identity

### Option C: Mailgun

1. Sign up at [mailgun.com](https://mailgun.com)
2. Add and verify your domain
3. Get your API key from the dashboard

## Step 4: Deploy Email Edge Function

Create a new Edge Function in your Supabase project:

### Using Supabase CLI

1. Install Supabase CLI:
```bash
npm install -g supabase
```

2. Login and link your project:
```bash
supabase login
supabase link --project-ref YOUR_PROJECT_ID
```

3. Create the email function:
```bash
supabase functions new send-email
```

4. Replace the content of `supabase/functions/send-email/index.ts`:

```typescript
import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  // Handle CORS
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const { to, subject, html, from } = await req.json()

    // Choose your email provider:
    
    // OPTION 1: Resend
    const response = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${Deno.env.get('RESEND_API_KEY')}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        from: `${from.name} <${from.email}>`,
        to: to.map(t => t.email),
        subject,
        html,
      }),
    })

    /* OPTION 2: SendGrid
    const response = await fetch('https://api.sendgrid.com/v3/mail/send', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${Deno.env.get('SENDGRID_API_KEY')}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        personalizations: [{
          to: to.map(t => ({ email: t.email })),
        }],
        from: { email: from.email, name: from.name },
        subject,
        content: [{ type: 'text/html', value: html }],
      }),
    })
    */

    /* OPTION 3: Mailgun
    const formData = new FormData()
    formData.append('from', `${from.name} <${from.email}>`)
    formData.append('to', to.map(t => t.email).join(','))
    formData.append('subject', subject)
    formData.append('html', html)

    const response = await fetch(`https://api.mailgun.net/v3/${Deno.env.get('MAILGUN_DOMAIN')}/messages`, {
      method: 'POST',
      headers: {
        'Authorization': `Basic ${btoa(`api:${Deno.env.get('MAILGUN_API_KEY')}`)}`,
      },
      body: formData,
    })
    */

    const result = await response.json()

    return new Response(
      JSON.stringify({ 
        success: response.ok, 
        data: result 
      }),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: response.ok ? 200 : 400,
      },
    )

  } catch (error) {
    return new Response(
      JSON.stringify({ 
        success: false, 
        error: error.message 
      }),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 500,
      },
    )
  }
})
```

5. Deploy the function:
```bash
supabase functions deploy send-email --no-verify-jwt
```

6. Set your email provider's API key as a secret:

For Resend:
```bash
supabase secrets set RESEND_API_KEY=re_your_api_key_here
```

For SendGrid:
```bash
supabase secrets set SENDGRID_API_KEY=SG.your_api_key_here
```

For Mailgun:
```bash
supabase secrets set MAILGUN_API_KEY=your_api_key_here
supabase secrets set MAILGUN_DOMAIN=your_domain.com
```

### Using Supabase Dashboard

1. Go to **Edge Functions** in your Supabase dashboard
2. Click "Create a new function"
3. Name it `send-email`
4. Paste the TypeScript code from above
5. Click "Deploy"
6. Go to **Settings** > **Edge Functions** and add your secrets

## Step 5: Test Email Function

Test your email function using the Supabase dashboard:

1. Go to **Edge Functions** > **send-email**
2. Click "Invoke function"
3. Use this test payload:

```json
{
  "to": [{"email": "your-email@example.com"}],
  "subject": "Billfrog Test Email",
  "html": "<h1>Test from Billfrog!</h1><p>If you receive this, your setup is working!</p>",
  "from": {
    "email": "receipts@yourdomain.com",
    "name": "Billfrog Receipts"
  }
}
```

4. Click "Send Request"
5. Check your email for the test message

## Step 6: Configure Billfrog

Now configure Billfrog with your Supabase credentials:

```bash
billfrog setup
```

Enter:
- **Supabase URL**: Your project URL from Step 2
- **Supabase Service Key**: Your service role key from Step 2

## Step 7: Test Billfrog Email

Test the complete flow:

```bash
# Add a test agent
billfrog agent add \
  --name "test-agent" \
  --provider openai \
  --api-key "sk-your-openai-key" \
  --email "your-email@example.com" \
  --schedule weekly

# Generate a test receipt
billfrog generate
```

Check your email for the receipt!

## Troubleshooting

### Common Issues

**Error: "Function not found"**
- Make sure the function is deployed and named exactly `send-email`
- Check that you're using the correct Supabase URL

**Error: "Invalid API key"**
- Verify your email provider API key is correct
- Make sure secrets are properly set in Supabase

**Error: "Authentication failed"**
- Ensure you're using the service role key, not the anon key
- Check that the key has the correct permissions

**Emails not being delivered**
- Check your email provider's dashboard for delivery logs
- Verify your sender domain is properly configured
- Check spam/junk folders

### Enable Edge Function Logs

To debug issues, enable logs in Supabase:

1. Go to **Edge Functions** > **send-email**
2. Click on **Logs** tab
3. Invoke the function and check for error messages

### Test Email Providers Directly

Test your email provider setup independently:

```bash
# For Resend
curl -X POST 'https://api.resend.com/emails' \
  -H 'Authorization: Bearer re_your_api_key' \
  -H 'Content-Type: application/json' \
  -d '{
    "from": "receipts@yourdomain.com",
    "to": ["your-email@example.com"],
    "subject": "Test",
    "html": "<p>Test email</p>"
  }'
```

## Security Best Practices

1. **Use Environment Variables**: Never hardcode API keys
2. **Restrict Edge Function Access**: Consider adding authentication
3. **Rotate Keys Regularly**: Change API keys periodically
4. **Monitor Usage**: Watch for unexpected email sending patterns
5. **Use HTTPS**: Always use secure connections

## Cost Considerations

- **Supabase**: Edge Functions have generous free tier
- **Email Providers**: 
  - Resend: 3,000 emails/month free
  - SendGrid: 100 emails/day free
  - Mailgun: 5,000 emails/month free (first 3 months)

## Next Steps

Once setup is complete:

1. Add your production AI agents
2. Set appropriate schedules
3. Start the Billfrog scheduler: `billfrog start`
4. Monitor email delivery in your provider's dashboard

Need help? Join our [Discord](https://discord.gg/billfrog) or email support@billfrog.dev!