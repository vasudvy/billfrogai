# 🐸 Billfrog

> Generate and email beautiful AI usage receipts automatically

Billfrog is a CLI tool that tracks your AI usage across providers (starting with OpenAI) and generates clean, Stripe-like receipts delivered to your email on a schedule. Perfect for freelancers, agencies, and teams who need to track and bill AI costs.

## ✨ Features

- 🤖 **Multi-Agent Support**: Track multiple AI agents separately
- 📊 **Beautiful Receipts**: Stripe-inspired HTML receipts with detailed breakdowns
- 📧 **Email Delivery**: Automatic email delivery via Supabase
- 📅 **Flexible Scheduling**: Daily, weekly, or monthly receipt generation
- 🔐 **Secure Storage**: Encrypted API keys and local data storage
- 🎨 **Rich CLI**: Beautiful terminal interface with colors and emojis
- 📈 **Usage Analytics**: Track tokens, costs, and model usage over time
- 🔄 **Background Scheduler**: Runs in the background to generate receipts automatically

## 🚀 Quick Start

### Installation

```bash
pip install billfrog
```

### Setup

1. **Configure Supabase for email delivery:**
```bash
billfrog setup
```

2. **Add your first AI agent:**
```bash
billfrog agent add \
  --name "my-assistant" \
  --provider openai \
  --api-key "sk-..." \
  --email "your@email.com" \
  --schedule weekly
```

3. **Start the scheduler:**
```bash
billfrog start
```

That's it! Billfrog will now track usage and send receipts according to your schedule.

## 📋 Commands

### Setup & Configuration

```bash
# Initial setup
billfrog setup

# Check status
billfrog status
```

### Agent Management

```bash
# Add an agent
billfrog agent add --name "gpt-assistant" --provider openai --api-key "sk-..." --email "billing@company.com" --schedule weekly

# List all agents
billfrog agent list

# Remove an agent
billfrog agent remove gpt-assistant
```

### Receipt Generation

```bash
# Generate receipts now (manual trigger)
billfrog generate

# Start background scheduler
billfrog start
```

## 🎨 Example Receipt

Billfrog generates beautiful, professional receipts that look like this:

```
🐸 Billfrog
AI Usage Receipt

Agent Name: GPT Assistant
Date Generated: December 15, 2024
Billing Period: December 8, 2024 - December 15, 2024
Schedule: Weekly

📊 Usage Summary
┌─────────────────┬──────────────┬──────────────┬──────────────┐
│ Total Requests  │ Total Tokens │ Prompt Tokens│Completion Tkns│
│      156        │    45,230    │    28,450    │    16,780    │
└─────────────────┴──────────────┴──────────────┴──────────────┘

💰 Total Usage Cost: $12.45

🤖 Models Used
• GPT-3.5-turbo: 98 requests
• GPT-4: 45 requests  
• Text-embedding-ada-002: 13 requests

📅 Daily Breakdown
Dec 8:  18 requests, 4,203 tokens, $1.85
Dec 9:  22 requests, 5,891 tokens, $2.12
...
```

## ⚙️ Configuration

Billfrog stores configuration in `~/.billfrog/`:

- `config.json` - Agent configurations
- `.key` - Encryption key for API keys
- `data.db` - Local usage database

### Supported Providers

- ✅ **OpenAI** (GPT-3.5, GPT-4, Embeddings, etc.)
- 🔄 **Anthropic** (Coming soon)
- 🔄 **Google AI** (Coming soon)

### Scheduling Options

- **Daily**: Receipts at 9:00 AM every day
- **Weekly**: Receipts at 9:00 AM every Monday
- **Monthly**: Receipts at 9:00 AM on the 1st of each month

## 🔧 Supabase Setup

Billfrog uses Supabase for email delivery. You'll need:

1. A Supabase project
2. An email delivery edge function deployed
3. Your Supabase URL and service key

### Edge Function for Email

Deploy this edge function to your Supabase project:

```typescript
// supabase/functions/send-email/index.ts
import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

serve(async (req) => {
  const { to, subject, html, from } = await req.json()
  
  // Use your preferred email service (Resend, SendGrid, etc.)
  // This is a simplified example
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

  return new Response(JSON.stringify({ success: response.ok }), {
    headers: { 'Content-Type': 'application/json' },
  })
})
```

## 🔒 Security

- API keys are encrypted using Fernet (AES 128)
- Local database uses secure file permissions (600)
- Configuration files are stored in user's home directory only

## 🤝 Contributing

Billfrog is open source! Contributions are welcome.

### Development Setup

```bash
git clone https://github.com/vasudvy/billfrogai
cd billfrogai
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Code Quality

```bash
black billfrog/
isort billfrog/
flake8 billfrog/
mypy billfrog/
```

## 📄 License

MIT License - see [LICENSE](LICENSE) file.

## 🐛 Issues & Support

- 🐛 [Report bugs](https://github.com/billfrog-dev/billfrog/issues)
- 💬 [Discussions](https://github.com/billfrog-dev/billfrog/discussions)
- 📧 Email: support@billfrog.dev

## 🗺️ Roadmap

- [ ] Support for Anthropic Claude
- [ ] Support for Google Gemini
- [ ] Web dashboard (optional)
- [ ] Slack/Discord notifications
- [ ] Team management features
- [ ] Advanced cost analytics
- [ ] Custom receipt templates
- [ ] Integration with billing systems

---

Made with 💚 by the Billfrog team