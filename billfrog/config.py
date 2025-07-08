"""Configuration management for Billfrog."""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, EmailStr, Field
from cryptography.fernet import Fernet
import base64


class AgentConfig(BaseModel):
    """Configuration for an AI agent."""
    name: str
    provider: str = "openai"
    api_key_encrypted: str
    email: EmailStr
    schedule: str = Field(default="weekly", pattern="^(daily|weekly|monthly)$")
    created_at: str
    last_receipt_sent: Optional[str] = None


class BillfrogConfig(BaseModel):
    """Main configuration for Billfrog."""
    agents: Dict[str, AgentConfig] = {}
    supabase_url: Optional[str] = None
    supabase_key_encrypted: Optional[str] = None
    encryption_key: Optional[str] = None


class ConfigManager:
    """Manages Billfrog configuration."""
    
    def __init__(self):
        self.config_dir = Path.home() / ".billfrog"
        self.config_file = self.config_dir / "config.json"
        self.config_dir.mkdir(exist_ok=True)
        self._ensure_encryption_key()
        
    def _ensure_encryption_key(self) -> None:
        """Ensure encryption key exists."""
        key_file = self.config_dir / ".key"
        if not key_file.exists():
            key = Fernet.generate_key()
            key_file.write_bytes(key)
            key_file.chmod(0o600)  # Read/write for owner only
        
        self._encryption_key = key_file.read_bytes()
    
    def _encrypt(self, data: str) -> str:
        """Encrypt sensitive data."""
        f = Fernet(self._encryption_key)
        encrypted = f.encrypt(data.encode())
        return base64.b64encode(encrypted).decode()
    
    def _decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive data."""
        f = Fernet(self._encryption_key)
        encrypted_bytes = base64.b64decode(encrypted_data.encode())
        return f.decrypt(encrypted_bytes).decode()
    
    def load_config(self) -> BillfrogConfig:
        """Load configuration from file."""
        if not self.config_file.exists():
            return BillfrogConfig()
        
        with open(self.config_file, 'r') as f:
            data = json.load(f)
        
        return BillfrogConfig(**data)
    
    def save_config(self, config: BillfrogConfig) -> None:
        """Save configuration to file."""
        with open(self.config_file, 'w') as f:
            json.dump(config.model_dump(), f, indent=2)
        
        # Secure file permissions
        self.config_file.chmod(0o600)
    
    def add_agent(self, name: str, provider: str, api_key: str, 
                  email: str, schedule: str) -> None:
        """Add a new AI agent configuration."""
        from datetime import datetime
        
        config = self.load_config()
        
        agent_config = AgentConfig(
            name=name,
            provider=provider,
            api_key_encrypted=self._encrypt(api_key),
            email=email,
            schedule=schedule,
            created_at=datetime.now().isoformat()
        )
        
        config.agents[name] = agent_config
        self.save_config(config)
    
    def get_agent_api_key(self, agent_name: str) -> Optional[str]:
        """Get decrypted API key for an agent."""
        config = self.load_config()
        if agent_name in config.agents:
            return self._decrypt(config.agents[agent_name].api_key_encrypted)
        return None
    
    def set_supabase_config(self, url: str, key: str) -> None:
        """Set Supabase configuration."""
        config = self.load_config()
        config.supabase_url = url
        config.supabase_key_encrypted = self._encrypt(key)
        self.save_config(config)
    
    def get_supabase_config(self) -> tuple[Optional[str], Optional[str]]:
        """Get Supabase configuration."""
        config = self.load_config()
        url = config.supabase_url
        key = None
        if config.supabase_key_encrypted:
            key = self._decrypt(config.supabase_key_encrypted)
        return url, key
    
    def list_agents(self) -> Dict[str, AgentConfig]:
        """List all configured agents."""
        config = self.load_config()
        return config.agents
    
    def remove_agent(self, name: str) -> bool:
        """Remove an agent configuration."""
        config = self.load_config()
        if name in config.agents:
            del config.agents[name]
            self.save_config(config)
            return True
        return False