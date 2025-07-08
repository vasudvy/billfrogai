#!/usr/bin/env python3
"""
Basic usage example for Billfrog API.

This example shows how to use Billfrog programmatically
instead of through the CLI interface.
"""

from billfrog.config import ConfigManager
from billfrog.ai_providers.openai_provider import OpenAIProvider
from billfrog.receipts.generator import ReceiptGenerator
from billfrog.email.sender import EmailSender

def main():
    """Example of programmatic billfrog usage."""
    
    # Initialize configuration manager
    config_manager = ConfigManager()
    
    # Check if we have any agents configured
    agents = config_manager.list_agents()
    if not agents:
        print("No agents configured. Use 'billfrog agent add' first.")
        return
    
    # Get the first agent
    agent_name = list(agents.keys())[0]
    agent_config = agents[agent_name]
    
    print(f"Generating receipt for agent: {agent_name}")
    
    # Get API key for the agent
    api_key = config_manager.get_agent_api_key(agent_name)
    if not api_key:
        print(f"No API key found for agent {agent_name}")
        return
    
    # Initialize OpenAI provider
    if agent_config.provider == "openai":
        provider = OpenAIProvider(api_key)
        
        # Get usage data for the last 7 days
        usage_data = provider.get_usage_data(days_back=7)
        
        # Generate receipt
        receipt_generator = ReceiptGenerator()
        receipt_html = receipt_generator.generate_receipt(
            agent_name, usage_data, agent_config.schedule
        )
        
        # Get Supabase configuration
        supabase_url, supabase_key = config_manager.get_supabase_config()
        
        if supabase_url and supabase_key:
            # Send email
            email_sender = EmailSender(supabase_url, supabase_key)
            success = email_sender.send_receipt(
                agent_config.email,
                f"Test Receipt for {agent_name}",
                receipt_html
            )
            
            if success:
                print(f"✅ Receipt sent to {agent_config.email}")
            else:
                print(f"❌ Failed to send receipt")
        else:
            print("📧 Supabase not configured, saving receipt to file")
            
            # Save to file instead
            with open(f"receipt_{agent_name}.html", "w") as f:
                f.write(receipt_html)
            print(f"💾 Receipt saved to receipt_{agent_name}.html")
    
    else:
        print(f"Unsupported provider: {agent_config.provider}")


if __name__ == "__main__":
    main()