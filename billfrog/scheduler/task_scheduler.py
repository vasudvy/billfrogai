"""Task scheduler for automated receipt generation."""

import schedule
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any
import logging
from ..config import ConfigManager
from ..ai_providers.openai_provider import OpenAIProvider
from ..email.sender import EmailSender
from ..receipts.generator import ReceiptGenerator

logger = logging.getLogger(__name__)


class TaskScheduler:
    """Handles scheduling of receipt generation tasks."""
    
    def __init__(self, config_manager: ConfigManager):
        """Initialize the task scheduler."""
        self.config_manager = config_manager
        self.running = False
        self.scheduler_thread = None
        
    def start(self) -> None:
        """Start the scheduler in a background thread."""
        if self.running:
            logger.warning("Scheduler is already running")
            return
        
        self.running = True
        self._setup_schedules()
        
        # Start the scheduler in a separate thread
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        # Keep the main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self) -> None:
        """Stop the scheduler."""
        self.running = False
        schedule.clear()
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        logger.info("Scheduler stopped")
    
    def _setup_schedules(self) -> None:
        """Set up schedules for all configured agents."""
        agents = self.config_manager.list_agents()
        
        for agent_name, agent_config in agents.items():
            if agent_config.schedule == "daily":
                schedule.every().day.at("09:00").do(
                    self._generate_receipt_for_agent, agent_name
                ).tag(agent_name)
            elif agent_config.schedule == "weekly":
                schedule.every().monday.at("09:00").do(
                    self._generate_receipt_for_agent, agent_name
                ).tag(agent_name)
            elif agent_config.schedule == "monthly":
                schedule.every().month.do(
                    self._generate_receipt_for_agent, agent_name
                ).tag(agent_name)
        
        logger.info(f"Set up schedules for {len(agents)} agents")
    
    def _run_scheduler(self) -> None:
        """Run the scheduler loop."""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                time.sleep(60)
    
    def _generate_receipt_for_agent(self, agent_name: str) -> None:
        """Generate and send receipt for a specific agent."""
        try:
            logger.info(f"Generating receipt for agent: {agent_name}")
            
            # Get agent configuration
            agents = self.config_manager.list_agents()
            if agent_name not in agents:
                logger.error(f"Agent {agent_name} not found")
                return
            
            agent_config = agents[agent_name]
            
            # Check if we should skip based on last receipt sent
            if self._should_skip_receipt(agent_config):
                logger.info(f"Skipping receipt for {agent_name} - too soon since last receipt")
                return
            
            # Get Supabase configuration
            supabase_url, supabase_key = self.config_manager.get_supabase_config()
            if not supabase_url or not supabase_key:
                logger.error("Supabase not configured")
                return
            
            # Initialize services
            email_sender = EmailSender(supabase_url, supabase_key)
            receipt_generator = ReceiptGenerator()
            
            # Get usage data based on provider
            if agent_config.provider == "openai":
                api_key = self.config_manager.get_agent_api_key(agent_name)
                if not api_key:
                    logger.error(f"No API key found for agent {agent_name}")
                    return
                
                provider = OpenAIProvider(api_key)
                
                # Determine days to look back based on schedule
                days_back = self._get_days_back(agent_config.schedule)
                usage_data = provider.get_usage_data(days_back)
            else:
                logger.error(f"Unsupported provider: {agent_config.provider}")
                return
            
            # Generate receipt
            receipt_html = receipt_generator.generate_receipt(
                agent_name, usage_data, agent_config.schedule
            )
            
            # Send email
            subject = f"🐸 AI Usage Receipt for {agent_name} - {datetime.now().strftime('%B %Y')}"
            success = email_sender.send_receipt(
                agent_config.email, 
                subject,
                receipt_html
            )
            
            if success:
                logger.info(f"Receipt sent successfully to {agent_config.email}")
                # Update last receipt sent timestamp
                self._update_last_receipt_sent(agent_name)
                
                # Log the email activity
                email_sender.log_email_sent(
                    agent_config.email, 
                    subject, 
                    True, 
                    agent_name
                )
            else:
                logger.error(f"Failed to send receipt for {agent_name}")
                email_sender.log_email_sent(
                    agent_config.email, 
                    subject, 
                    False, 
                    agent_name
                )
                
        except Exception as e:
            logger.error(f"Error generating receipt for {agent_name}: {e}")
    
    def _should_skip_receipt(self, agent_config) -> bool:
        """Check if we should skip generating a receipt based on timing."""
        if not agent_config.last_receipt_sent:
            return False
        
        try:
            last_sent = datetime.fromisoformat(agent_config.last_receipt_sent)
            now = datetime.now()
            
            if agent_config.schedule == "daily":
                return (now - last_sent).days < 1
            elif agent_config.schedule == "weekly":
                return (now - last_sent).days < 7
            elif agent_config.schedule == "monthly":
                return (now - last_sent).days < 30
            
        except Exception as e:
            logger.error(f"Error checking receipt timing: {e}")
        
        return False
    
    def _get_days_back(self, schedule: str) -> int:
        """Get the number of days to look back for usage data."""
        if schedule == "daily":
            return 1
        elif schedule == "weekly":
            return 7
        elif schedule == "monthly":
            return 30
        else:
            return 7  # Default to weekly
    
    def _update_last_receipt_sent(self, agent_name: str) -> None:
        """Update the last receipt sent timestamp for an agent."""
        try:
            config = self.config_manager.load_config()
            if agent_name in config.agents:
                config.agents[agent_name].last_receipt_sent = datetime.now().isoformat()
                self.config_manager.save_config(config)
        except Exception as e:
            logger.error(f"Error updating last receipt sent for {agent_name}: {e}")
    
    def generate_receipt_now(self, agent_name: str) -> bool:
        """Generate a receipt immediately for testing."""
        try:
            self._generate_receipt_for_agent(agent_name)
            return True
        except Exception as e:
            logger.error(f"Error generating immediate receipt for {agent_name}: {e}")
            return False
    
    def get_next_run_times(self) -> Dict[str, str]:
        """Get the next scheduled run times for all agents."""
        next_runs = {}
        agents = self.config_manager.list_agents()
        
        for agent_name, agent_config in agents.items():
            try:
                if agent_config.schedule == "daily":
                    next_run = "Daily at 9:00 AM"
                elif agent_config.schedule == "weekly":
                    next_run = "Weekly on Monday at 9:00 AM"
                elif agent_config.schedule == "monthly":
                    next_run = "Monthly on the 1st at 9:00 AM"
                else:
                    next_run = "Unknown schedule"
                
                next_runs[agent_name] = next_run
            except Exception as e:
                logger.error(f"Error calculating next run time for {agent_name}: {e}")
                next_runs[agent_name] = "Error calculating next run"
        
        return next_runs
    
    def reschedule_agent(self, agent_name: str) -> None:
        """Reschedule tasks for a specific agent (useful after config changes)."""
        # Remove existing schedule for this agent
        schedule.clear(agent_name)
        
        # Get updated agent configuration
        agents = self.config_manager.list_agents()
        if agent_name not in agents:
            logger.warning(f"Agent {agent_name} not found for rescheduling")
            return
        
        agent_config = agents[agent_name]
        
        # Set up new schedule
        if agent_config.schedule == "daily":
            schedule.every().day.at("09:00").do(
                self._generate_receipt_for_agent, agent_name
            ).tag(agent_name)
        elif agent_config.schedule == "weekly":
            schedule.every().monday.at("09:00").do(
                self._generate_receipt_for_agent, agent_name
            ).tag(agent_name)
        elif agent_config.schedule == "monthly":
            schedule.every().month.do(
                self._generate_receipt_for_agent, agent_name
            ).tag(agent_name)
        
        logger.info(f"Rescheduled agent {agent_name} for {agent_config.schedule} receipts")