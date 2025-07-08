"""Main CLI interface for Billfrog."""

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.text import Text
from typing import Optional
import sys
from email_validator import validate_email, EmailNotValidError

from .config import ConfigManager
from .ai_providers.openai_provider import OpenAIProvider
from .email.sender import EmailSender
from .receipts.generator import ReceiptGenerator
from .scheduler.task_scheduler import TaskScheduler

app = typer.Typer(
    name="billfrog",
    help="🐸 Generate and email AI usage receipts",
    rich_markup_mode="rich",
)
console = Console()


def version_callback(value: bool):
    """Show version information."""
    if value:
        from . import __version__
        console.print(f"Billfrog version: [bold green]{__version__}[/bold green]")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None, 
        "--version", 
        callback=version_callback,
        help="Show version and exit"
    )
):
    """
    🐸 [bold green]Billfrog[/bold green] - Generate and email AI usage receipts
    
    A CLI tool that tracks AI usage and generates clean, Stripe-like receipts
    delivered to your email on a schedule.
    """
    pass


@app.command()
def setup():
    """🔧 Setup Billfrog configuration."""
    console.print(Panel.fit(
        "🐸 [bold green]Welcome to Billfrog![/bold green]\n"
        "Let's set up your AI receipt generation system.",
        title="Setup",
        border_style="green"
    ))
    
    config_manager = ConfigManager()
    
    # Setup Supabase for email delivery
    console.print("\n📧 [bold blue]Email Configuration[/bold blue]")
    console.print("Billfrog uses Supabase for email delivery.")
    
    supabase_url = Prompt.ask("Enter your Supabase URL")
    supabase_key = Prompt.ask("Enter your Supabase service key", password=True)
    
    try:
        config_manager.set_supabase_config(supabase_url, supabase_key)
        console.print("✅ Supabase configuration saved!")
    except Exception as e:
        console.print(f"❌ Error saving configuration: {e}")
        raise typer.Exit(1)
    
    console.print("\n🎉 Setup complete! You can now add AI agents.")
    console.print("Run [bold]billfrog agent add[/bold] to get started.")


@app.group()
def agent():
    """👤 Manage AI agents."""
    pass


@agent.command("add")
def add_agent(
    name: str = typer.Option(..., "--name", "-n", help="Agent name"),
    provider: str = typer.Option("openai", "--provider", "-p", help="AI provider (currently supports: openai)"),
    api_key: str = typer.Option(..., "--api-key", "-k", help="API key for the provider"),
    email: str = typer.Option(..., "--email", "-e", help="Email address for receipts"),
    schedule: str = typer.Option("weekly", "--schedule", "-s", help="Receipt schedule (daily/weekly/monthly)")
):
    """➕ Add a new AI agent."""
    
    # Validate inputs
    if provider not in ["openai"]:
        console.print(f"❌ Unsupported provider: {provider}")
        console.print("Currently supported providers: openai")
        raise typer.Exit(1)
    
    if schedule not in ["daily", "weekly", "monthly"]:
        console.print(f"❌ Invalid schedule: {schedule}")
        console.print("Valid schedules: daily, weekly, monthly")
        raise typer.Exit(1)
    
    try:
        validate_email(email)
    except EmailNotValidError:
        console.print(f"❌ Invalid email address: {email}")
        raise typer.Exit(1)
    
    config_manager = ConfigManager()
    
    # Check if agent already exists
    agents = config_manager.list_agents()
    if name in agents:
        console.print(f"❌ Agent '{name}' already exists!")
        raise typer.Exit(1)
    
    # Test API key
    console.print(f"🔍 Testing {provider.upper()} API key...")
    
    if provider == "openai":
        openai_provider = OpenAIProvider(api_key)
        if not openai_provider.test_connection():
            console.print("❌ Invalid OpenAI API key!")
            raise typer.Exit(1)
    
    # Save configuration
    try:
        config_manager.add_agent(name, provider, api_key, email, schedule)
        
        console.print(Panel.fit(
            f"✅ Agent '[bold green]{name}[/bold green]' added successfully!\n\n"
            f"📧 Email: {email}\n"
            f"🤖 Provider: {provider.upper()}\n"
            f"📅 Schedule: {schedule}\n\n"
            f"Run [bold]billfrog start[/bold] to begin tracking usage.",
            title="Agent Added",
            border_style="green"
        ))
        
    except Exception as e:
        console.print(f"❌ Error adding agent: {e}")
        raise typer.Exit(1)


@agent.command("list")
def list_agents():
    """📋 List all configured agents."""
    config_manager = ConfigManager()
    agents = config_manager.list_agents()
    
    if not agents:
        console.print("📭 No agents configured yet.")
        console.print("Run [bold]billfrog agent add[/bold] to add your first agent.")
        return
    
    table = Table(title="🤖 Configured AI Agents")
    table.add_column("Name", style="bold green")
    table.add_column("Provider", style="blue")
    table.add_column("Email", style="cyan")
    table.add_column("Schedule", style="yellow")
    table.add_column("Created", style="dim")
    table.add_column("Last Receipt", style="dim")
    
    for agent in agents.values():
        last_receipt = agent.last_receipt_sent or "Never"
        table.add_row(
            agent.name,
            agent.provider.upper(),
            agent.email,
            agent.schedule,
            agent.created_at[:10],  # Just the date
            last_receipt
        )
    
    console.print(table)


@agent.command("remove")
def remove_agent(
    name: str = typer.Argument(..., help="Name of the agent to remove")
):
    """🗑️ Remove an AI agent."""
    config_manager = ConfigManager()
    
    agents = config_manager.list_agents()
    if name not in agents:
        console.print(f"❌ Agent '{name}' not found!")
        raise typer.Exit(1)
    
    if Confirm.ask(f"Are you sure you want to remove agent '{name}'?"):
        if config_manager.remove_agent(name):
            console.print(f"✅ Agent '[bold red]{name}[/bold red]' removed successfully!")
        else:
            console.print(f"❌ Failed to remove agent '{name}'")
            raise typer.Exit(1)


@app.command()
def start():
    """🚀 Start the background scheduler for receipt generation."""
    console.print("🚀 Starting Billfrog scheduler...")
    
    config_manager = ConfigManager()
    agents = config_manager.list_agents()
    
    if not agents:
        console.print("❌ No agents configured!")
        console.print("Run [bold]billfrog agent add[/bold] to add an agent first.")
        raise typer.Exit(1)
    
    # Check Supabase configuration
    supabase_url, supabase_key = config_manager.get_supabase_config()
    if not supabase_url or not supabase_key:
        console.print("❌ Supabase not configured!")
        console.print("Run [bold]billfrog setup[/bold] first.")
        raise typer.Exit(1)
    
    scheduler = TaskScheduler(config_manager)
    
    try:
        console.print(f"📅 Scheduled {len(agents)} agents for receipt generation.")
        console.print("🔄 Scheduler running... Press Ctrl+C to stop.")
        scheduler.start()
    except KeyboardInterrupt:
        console.print("\n⏹️ Scheduler stopped.")
    except Exception as e:
        console.print(f"❌ Scheduler error: {e}")
        raise typer.Exit(1)


@app.command()
def status():
    """📊 Show current status and configuration."""
    config_manager = ConfigManager()
    agents = config_manager.list_agents()
    supabase_url, _ = config_manager.get_supabase_config()
    
    # Main status panel
    status_text = f"🤖 Agents: {len(agents)}\n"
    status_text += f"📧 Email: {'✅ Configured' if supabase_url else '❌ Not configured'}\n"
    
    if agents:
        status_text += f"\n📈 Recent Activity:\n"
        for agent in list(agents.values())[:3]:  # Show last 3 agents
            last_receipt = agent.last_receipt_sent or "Never"
            status_text += f"  • {agent.name}: {last_receipt}\n"
    
    console.print(Panel.fit(
        status_text,
        title="📊 Billfrog Status",
        border_style="blue"
    ))


@app.command()
def generate():
    """📄 Generate receipts now for all agents (manual trigger)."""
    console.print("📄 Generating receipts for all agents...")
    
    config_manager = ConfigManager()
    agents = config_manager.list_agents()
    
    if not agents:
        console.print("❌ No agents configured!")
        raise typer.Exit(1)
    
    # Check Supabase configuration
    supabase_url, supabase_key = config_manager.get_supabase_config()
    if not supabase_url or not supabase_key:
        console.print("❌ Supabase not configured!")
        console.print("Run [bold]billfrog setup[/bold] first.")
        raise typer.Exit(1)
    
    email_sender = EmailSender(supabase_url, supabase_key)
    receipt_generator = ReceiptGenerator()
    
    for agent_name, agent_config in agents.items():
        try:
            console.print(f"🔄 Processing {agent_name}...")
            
            # Get usage data
            if agent_config.provider == "openai":
                api_key = config_manager.get_agent_api_key(agent_name)
                provider = OpenAIProvider(api_key)
                usage_data = provider.get_usage_data()
            else:
                console.print(f"❌ Unsupported provider for {agent_name}")
                continue
            
            # Generate receipt
            receipt_html = receipt_generator.generate_receipt(
                agent_name, usage_data, agent_config.schedule
            )
            
            # Send email
            success = email_sender.send_receipt(
                agent_config.email, 
                f"AI Usage Receipt for {agent_name}",
                receipt_html
            )
            
            if success:
                console.print(f"✅ Receipt sent to {agent_config.email}")
                # Update last receipt sent timestamp
                # TODO: Implement this in config manager
            else:
                console.print(f"❌ Failed to send receipt for {agent_name}")
                
        except Exception as e:
            console.print(f"❌ Error processing {agent_name}: {e}")
    
    console.print("📄 Receipt generation complete!")


def main():
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()