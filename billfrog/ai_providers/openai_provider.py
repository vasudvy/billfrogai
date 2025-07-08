"""OpenAI provider integration for tracking AI usage."""

import openai
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import time
from pydantic import BaseModel


class UsageRecord(BaseModel):
    """Represents a usage record for AI services."""
    timestamp: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    request_type: str = "chat_completion"


class UsageData(BaseModel):
    """Aggregated usage data for a time period."""
    period_start: str
    period_end: str
    total_requests: int
    total_prompt_tokens: int
    total_completion_tokens: int
    total_tokens: int
    total_cost_usd: float
    models_used: Dict[str, int]
    daily_breakdown: List[Dict[str, Any]]


class OpenAIProvider:
    """OpenAI provider for tracking AI usage and costs."""
    
    # Current OpenAI pricing (as of latest update)
    # These should be kept updated with OpenAI's pricing
    MODEL_PRICING = {
        "gpt-4": {
            "prompt": 0.03 / 1000,      # $0.03 per 1K prompt tokens
            "completion": 0.06 / 1000,   # $0.06 per 1K completion tokens
        },
        "gpt-4-0613": {
            "prompt": 0.03 / 1000,
            "completion": 0.06 / 1000,
        },
        "gpt-4-32k": {
            "prompt": 0.06 / 1000,      # $0.06 per 1K prompt tokens
            "completion": 0.12 / 1000,   # $0.12 per 1K completion tokens
        },
        "gpt-4-turbo": {
            "prompt": 0.01 / 1000,      # $0.01 per 1K prompt tokens
            "completion": 0.03 / 1000,   # $0.03 per 1K completion tokens
        },
        "gpt-4-turbo-preview": {
            "prompt": 0.01 / 1000,
            "completion": 0.03 / 1000,
        },
        "gpt-3.5-turbo": {
            "prompt": 0.0015 / 1000,    # $0.0015 per 1K prompt tokens
            "completion": 0.002 / 1000,  # $0.002 per 1K completion tokens
        },
        "gpt-3.5-turbo-0125": {
            "prompt": 0.0005 / 1000,    # $0.0005 per 1K prompt tokens
            "completion": 0.0015 / 1000, # $0.0015 per 1K completion tokens
        },
        "gpt-3.5-turbo-instruct": {
            "prompt": 0.0015 / 1000,
            "completion": 0.002 / 1000,
        },
        "text-davinci-003": {
            "prompt": 0.02 / 1000,
            "completion": 0.02 / 1000,
        },
        "text-davinci-002": {
            "prompt": 0.02 / 1000,
            "completion": 0.02 / 1000,
        },
        "davinci": {
            "prompt": 0.02 / 1000,
            "completion": 0.02 / 1000,
        },
        "curie": {
            "prompt": 0.002 / 1000,
            "completion": 0.002 / 1000,
        },
        "babbage": {
            "prompt": 0.0005 / 1000,
            "completion": 0.0005 / 1000,
        },
        "ada": {
            "prompt": 0.0004 / 1000,
            "completion": 0.0004 / 1000,
        },
        # Embedding models
        "text-embedding-ada-002": {
            "prompt": 0.0001 / 1000,
            "completion": 0,
        },
        "text-embedding-3-small": {
            "prompt": 0.00002 / 1000,
            "completion": 0,
        },
        "text-embedding-3-large": {
            "prompt": 0.00013 / 1000,
            "completion": 0,
        },
    }
    
    def __init__(self, api_key: str):
        """Initialize OpenAI provider with API key."""
        self.client = openai.OpenAI(api_key=api_key)
        self.api_key = api_key
    
    def test_connection(self) -> bool:
        """Test if the API key is valid."""
        try:
            # Try to list models as a test
            self.client.models.list()
            return True
        except Exception:
            return False
    
    def calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate cost for a specific usage."""
        # Normalize model name for pricing lookup
        model_key = self._normalize_model_name(model)
        
        if model_key not in self.MODEL_PRICING:
            # Default to GPT-3.5-turbo pricing for unknown models
            model_key = "gpt-3.5-turbo"
        
        pricing = self.MODEL_PRICING[model_key]
        
        prompt_cost = prompt_tokens * pricing["prompt"]
        completion_cost = completion_tokens * pricing["completion"]
        
        return prompt_cost + completion_cost
    
    def _normalize_model_name(self, model: str) -> str:
        """Normalize model name for pricing lookup."""
        # Handle model names that might have additional suffixes
        model_lower = model.lower()
        
        # Direct matches first
        if model_lower in self.MODEL_PRICING:
            return model_lower
        
        # Pattern matching for variants
        if "gpt-4-turbo" in model_lower:
            return "gpt-4-turbo"
        elif "gpt-4-32k" in model_lower:
            return "gpt-4-32k"
        elif "gpt-4" in model_lower:
            return "gpt-4"
        elif "gpt-3.5-turbo-0125" in model_lower:
            return "gpt-3.5-turbo-0125"
        elif "gpt-3.5-turbo-instruct" in model_lower:
            return "gpt-3.5-turbo-instruct"
        elif "gpt-3.5-turbo" in model_lower:
            return "gpt-3.5-turbo"
        elif "text-davinci" in model_lower:
            return "text-davinci-003"
        elif "text-embedding-3-large" in model_lower:
            return "text-embedding-3-large"
        elif "text-embedding-3-small" in model_lower:
            return "text-embedding-3-small"
        elif "text-embedding" in model_lower:
            return "text-embedding-ada-002"
        
        return model_lower
    
    def get_usage_data(self, days_back: int = 7) -> UsageData:
        """
        Get usage data for the specified period.
        
        Note: OpenAI doesn't provide detailed usage API, so this is a simulation
        based on typical usage patterns. In a real implementation, you'd need to:
        1. Store usage data locally as API calls are made
        2. Use OpenAI's billing API if available
        3. Parse usage from OpenAI dashboard exports
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # This is a simulation - in practice, you'd track real usage
        usage_data = self._simulate_usage_data(start_date, end_date)
        
        return usage_data
    
    def _simulate_usage_data(self, start_date: datetime, end_date: datetime) -> UsageData:
        """
        Simulate usage data for demonstration.
        
        In a real implementation, this would:
        1. Read from local usage tracking database
        2. Query OpenAI's usage API if available
        3. Import from usage logs
        """
        import random
        
        # Simulate some realistic usage patterns
        total_requests = random.randint(50, 300)
        models_used = {
            "gpt-3.5-turbo": random.randint(20, 150),
            "gpt-4": random.randint(10, 50),
            "text-embedding-ada-002": random.randint(5, 30),
        }
        
        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_cost = 0.0
        daily_breakdown = []
        
        # Generate daily breakdown
        current_date = start_date
        while current_date <= end_date:
            daily_requests = random.randint(5, 20)
            daily_prompt_tokens = random.randint(1000, 5000)
            daily_completion_tokens = random.randint(500, 2500)
            
            # Calculate daily cost based on model distribution
            daily_cost = 0.0
            for model, count in models_used.items():
                if daily_requests > 0:
                    model_requests = max(1, count * daily_requests // total_requests)
                    model_prompt_tokens = daily_prompt_tokens * model_requests // daily_requests
                    model_completion_tokens = daily_completion_tokens * model_requests // daily_requests
                    
                    daily_cost += self.calculate_cost(model, model_prompt_tokens, model_completion_tokens)
            
            daily_breakdown.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "requests": daily_requests,
                "prompt_tokens": daily_prompt_tokens,
                "completion_tokens": daily_completion_tokens,
                "cost_usd": round(daily_cost, 4),
                "models": dict(models_used)  # Copy models for this day
            })
            
            total_prompt_tokens += daily_prompt_tokens
            total_completion_tokens += daily_completion_tokens
            total_cost += daily_cost
            
            current_date += timedelta(days=1)
        
        return UsageData(
            period_start=start_date.isoformat(),
            period_end=end_date.isoformat(),
            total_requests=total_requests,
            total_prompt_tokens=total_prompt_tokens,
            total_completion_tokens=total_completion_tokens,
            total_tokens=total_prompt_tokens + total_completion_tokens,
            total_cost_usd=round(total_cost, 4),
            models_used=models_used,
            daily_breakdown=daily_breakdown
        )
    
    def get_models(self) -> List[str]:
        """Get available models from OpenAI."""
        try:
            models = self.client.models.list()
            return [model.id for model in models.data]
        except Exception as e:
            # Return common models if API call fails
            return [
                "gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", 
                "text-embedding-ada-002", "text-davinci-003"
            ]
    
    def track_usage(self, model: str, prompt_tokens: int, completion_tokens: int, 
                   request_type: str = "chat_completion") -> UsageRecord:
        """
        Track a single usage record.
        
        This would be called after each API request to log usage.
        """
        cost = self.calculate_cost(model, prompt_tokens, completion_tokens)
        
        return UsageRecord(
            timestamp=datetime.now().isoformat(),
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            cost_usd=cost,
            request_type=request_type
        )