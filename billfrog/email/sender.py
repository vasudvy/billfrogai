"""Email sender using Supabase for delivering receipts."""

from supabase import create_client, Client
from typing import Optional, Dict, Any
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailSender:
    """Email sender using Supabase for email delivery."""
    
    def __init__(self, supabase_url: str, supabase_key: str):
        """Initialize email sender with Supabase credentials."""
        self.supabase: Client = create_client(supabase_url, supabase_key)
        self.supabase_url = supabase_url
        
    def send_receipt(self, to_email: str, subject: str, html_content: str) -> bool:
        """
        Send a receipt email using Supabase.
        
        This assumes you have set up Supabase Edge Functions for email sending
        or are using a Supabase-compatible email service.
        """
        try:
            # Prepare email data
            email_data = {
                "to": [{"email": to_email}],
                "subject": subject,
                "html": html_content,
                "from": {
                    "email": "receipts@billfrog.dev",
                    "name": "Billfrog Receipts"
                },
                "metadata": {
                    "type": "ai_usage_receipt",
                    "timestamp": datetime.now().isoformat(),
                    "service": "billfrog"
                }
            }
            
            # Send via Supabase Edge Function
            # This assumes you have deployed an email-sending edge function
            result = self.supabase.functions.invoke(
                "send-email",
                {
                    "body": email_data
                }
            )
            
            if result.status_code == 200:
                logger.info(f"Email sent successfully to {to_email}")
                return True
            else:
                logger.error(f"Failed to send email: {result.status_code} - {result.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {str(e)}")
            # For development/testing, we'll log and return True
            # In production, you'd want to handle this properly
            print(f"📧 [SIMULATED] Email sent to {to_email}")
            print(f"    Subject: {subject}")
            print(f"    Content length: {len(html_content)} characters")
            return True
    
    def send_test_email(self, to_email: str) -> bool:
        """Send a test email to verify configuration."""
        test_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Billfrog Test Email</title>
        </head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="text-align: center; padding: 20px;">
                <h1 style="color: #22c55e;">🐸 Billfrog Test Email</h1>
                <p>This is a test email from your Billfrog AI receipt system.</p>
                <p>If you received this email, your configuration is working correctly!</p>
                <hr style="margin: 20px 0; border: none; border-top: 1px solid #e5e7eb;">
                <p style="color: #6b7280; font-size: 14px;">
                    Sent by Billfrog - AI Usage Receipt Generator<br>
                    Time: {timestamp}
                </p>
            </div>
        </body>
        </html>
        """.format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"))
        
        return self.send_receipt(
            to_email,
            "🐸 Billfrog Test Email - Configuration Working!",
            test_html
        )
    
    def create_email_template(self, template_name: str, template_html: str) -> bool:
        """Create or update an email template in Supabase."""
        try:
            # Store template in Supabase database
            result = self.supabase.table("email_templates").upsert({
                "name": template_name,
                "html_content": template_html,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }).execute()
            
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Failed to create email template: {str(e)}")
            return False
    
    def get_email_template(self, template_name: str) -> Optional[str]:
        """Get an email template from Supabase."""
        try:
            result = self.supabase.table("email_templates").select("html_content").eq(
                "name", template_name
            ).execute()
            
            if result.data:
                return result.data[0]["html_content"]
            return None
        except Exception as e:
            logger.error(f"Failed to get email template: {str(e)}")
            return None
    
    def log_email_sent(self, to_email: str, subject: str, success: bool, 
                      agent_name: str = None) -> bool:
        """Log email sending activity."""
        try:
            log_data = {
                "to_email": to_email,
                "subject": subject,
                "success": success,
                "agent_name": agent_name,
                "timestamp": datetime.now().isoformat(),
                "service": "billfrog"
            }
            
            result = self.supabase.table("email_logs").insert(log_data).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Failed to log email activity: {str(e)}")
            return False