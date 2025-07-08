"""Receipt generator for creating beautiful HTML receipts."""

from jinja2 import Template
from datetime import datetime, timedelta
from typing import Dict, Any, List
import uuid
from ..ai_providers.openai_provider import UsageData


class ReceiptGenerator:
    """Generates beautiful HTML receipts for AI usage."""
    
    def __init__(self):
        """Initialize the receipt generator."""
        self.receipt_template = self._create_receipt_template()
    
    def generate_receipt(self, agent_name: str, usage_data: UsageData, 
                        schedule: str) -> str:
        """Generate a complete HTML receipt."""
        
        # Calculate period based on schedule
        period_info = self._get_period_info(schedule)
        
        # Prepare receipt data
        receipt_data = {
            "agent_name": agent_name,
            "receipt_id": self._generate_receipt_id(),
            "date_generated": datetime.now().strftime("%B %d, %Y"),
            "period": period_info,
            "usage_summary": self._format_usage_summary(usage_data),
            "cost_breakdown": self._format_cost_breakdown(usage_data),
            "daily_usage": self._format_daily_usage(usage_data.daily_breakdown),
            "models_breakdown": self._format_models_breakdown(usage_data.models_used),
            "total_cost": usage_data.total_cost_usd,
            "schedule": schedule.title(),
            "next_receipt": self._calculate_next_receipt_date(schedule)
        }
        
        # Render template
        template = Template(self.receipt_template)
        html_receipt = template.render(**receipt_data)
        
        return html_receipt
    
    def _create_receipt_template(self) -> str:
        """Create the HTML template for receipts."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Usage Receipt - {{ agent_name }}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #374151;
            background-color: #f9fafb;
            padding: 20px;
        }
        
        .receipt-container {
            max-width: 700px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            padding: 40px 40px 30px;
            text-align: center;
        }
        
        .logo {
            font-size: 48px;
            margin-bottom: 10px;
        }
        
        .company-name {
            font-size: 32px;
            font-weight: 700;
            margin-bottom: 8px;
            letter-spacing: -0.025em;
        }
        
        .tagline {
            font-size: 16px;
            opacity: 0.9;
            font-weight: 400;
        }
        
        .receipt-info {
            background: #f8fafc;
            padding: 30px 40px;
            border-bottom: 1px solid #e5e7eb;
        }
        
        .receipt-meta {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 20px;
        }
        
        .meta-item h3 {
            font-size: 14px;
            font-weight: 600;
            color: #6b7280;
            text-transform: uppercase;
            letter-spacing: 0.025em;
            margin-bottom: 4px;
        }
        
        .meta-item p {
            font-size: 16px;
            font-weight: 500;
            color: #111827;
        }
        
        .receipt-id {
            font-family: 'Courier New', monospace;
            background: #e5e7eb;
            padding: 12px 16px;
            border-radius: 6px;
            text-align: center;
            font-size: 14px;
            color: #374151;
            font-weight: 600;
        }
        
        .content {
            padding: 40px;
        }
        
        .section {
            margin-bottom: 40px;
        }
        
        .section-title {
            font-size: 20px;
            font-weight: 700;
            color: #111827;
            margin-bottom: 20px;
            padding-bottom: 8px;
            border-bottom: 2px solid #10b981;
        }
        
        .usage-summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .usage-card {
            background: #f8fafc;
            padding: 24px;
            border-radius: 8px;
            border: 1px solid #e5e7eb;
            text-align: center;
        }
        
        .usage-card .value {
            font-size: 28px;
            font-weight: 700;
            color: #10b981;
            margin-bottom: 4px;
        }
        
        .usage-card .label {
            font-size: 14px;
            color: #6b7280;
            font-weight: 500;
        }
        
        .cost-total {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            padding: 30px;
            border-radius: 12px;
            text-align: center;
            margin: 30px 0;
        }
        
        .cost-total .amount {
            font-size: 48px;
            font-weight: 700;
            margin-bottom: 8px;
        }
        
        .cost-total .label {
            font-size: 18px;
            opacity: 0.9;
        }
        
        .breakdown-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 16px;
        }
        
        .breakdown-table th,
        .breakdown-table td {
            padding: 12px 16px;
            text-align: left;
            border-bottom: 1px solid #e5e7eb;
        }
        
        .breakdown-table th {
            background: #f8fafc;
            font-weight: 600;
            color: #374151;
            font-size: 14px;
        }
        
        .breakdown-table td {
            font-size: 14px;
        }
        
        .breakdown-table .amount {
            font-weight: 600;
            color: #10b981;
        }
        
        .models-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-top: 16px;
        }
        
        .model-card {
            background: #f8fafc;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #10b981;
        }
        
        .model-card .model-name {
            font-weight: 600;
            color: #111827;
            margin-bottom: 8px;
        }
        
        .model-card .model-usage {
            font-size: 24px;
            font-weight: 700;
            color: #10b981;
        }
        
        .model-card .model-label {
            font-size: 12px;
            color: #6b7280;
            text-transform: uppercase;
            letter-spacing: 0.025em;
        }
        
        .footer {
            background: #f8fafc;
            padding: 30px 40px;
            text-align: center;
            border-top: 1px solid #e5e7eb;
        }
        
        .footer p {
            color: #6b7280;
            font-size: 14px;
            margin-bottom: 8px;
        }
        
        .footer .next-receipt {
            color: #10b981;
            font-weight: 600;
        }
        
        @media (max-width: 600px) {
            body {
                padding: 10px;
            }
            
            .header {
                padding: 30px 20px 20px;
            }
            
            .company-name {
                font-size: 24px;
            }
            
            .receipt-info,
            .content {
                padding: 20px;
            }
            
            .receipt-meta {
                grid-template-columns: 1fr;
                gap: 20px;
            }
            
            .usage-summary {
                grid-template-columns: 1fr;
            }
            
            .cost-total .amount {
                font-size: 36px;
            }
        }
    </style>
</head>
<body>
    <div class="receipt-container">
        <div class="header">
            <div class="logo">🐸</div>
            <h1 class="company-name">Billfrog</h1>
            <p class="tagline">AI Usage Receipt</p>
        </div>
        
        <div class="receipt-info">
            <div class="receipt-meta">
                <div class="meta-item">
                    <h3>Agent Name</h3>
                    <p>{{ agent_name }}</p>
                </div>
                <div class="meta-item">
                    <h3>Date Generated</h3>
                    <p>{{ date_generated }}</p>
                </div>
                <div class="meta-item">
                    <h3>Billing Period</h3>
                    <p>{{ period.start }} - {{ period.end }}</p>
                </div>
                <div class="meta-item">
                    <h3>Schedule</h3>
                    <p>{{ schedule }}</p>
                </div>
            </div>
            <div class="receipt-id">
                Receipt ID: {{ receipt_id }}
            </div>
        </div>
        
        <div class="content">
            <div class="section">
                <h2 class="section-title">📊 Usage Summary</h2>
                <div class="usage-summary">
                    <div class="usage-card">
                        <div class="value">{{ usage_summary.total_requests }}</div>
                        <div class="label">Total Requests</div>
                    </div>
                    <div class="usage-card">
                        <div class="value">{{ usage_summary.total_tokens }}</div>
                        <div class="label">Total Tokens</div>
                    </div>
                    <div class="usage-card">
                        <div class="value">{{ usage_summary.prompt_tokens }}</div>
                        <div class="label">Prompt Tokens</div>
                    </div>
                    <div class="usage-card">
                        <div class="value">{{ usage_summary.completion_tokens }}</div>
                        <div class="label">Completion Tokens</div>
                    </div>
                </div>
            </div>
            
            <div class="cost-total">
                <div class="amount">${{ "%.4f"|format(total_cost) }}</div>
                <div class="label">Total Usage Cost</div>
            </div>
            
            <div class="section">
                <h2 class="section-title">🤖 Models Used</h2>
                <div class="models-grid">
                    {% for model in models_breakdown %}
                    <div class="model-card">
                        <div class="model-name">{{ model.name }}</div>
                        <div class="model-usage">{{ model.requests }}</div>
                        <div class="model-label">Requests</div>
                    </div>
                    {% endfor %}
                </div>
            </div>
            
            <div class="section">
                <h2 class="section-title">📅 Daily Breakdown</h2>
                <table class="breakdown-table">
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Requests</th>
                            <th>Tokens</th>
                            <th>Cost</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for day in daily_usage %}
                        <tr>
                            <td>{{ day.date }}</td>
                            <td>{{ day.requests }}</td>
                            <td>{{ day.total_tokens }}</td>
                            <td class="amount">${{ "%.4f"|format(day.cost) }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="footer">
            <p>Thank you for using Billfrog for your AI usage tracking!</p>
            <p>Next receipt will be generated: <span class="next-receipt">{{ next_receipt }}</span></p>
            <p>Questions? Contact us at support@billfrog.dev</p>
        </div>
    </div>
</body>
</html>
        """
    
    def _generate_receipt_id(self) -> str:
        """Generate a unique receipt ID."""
        return f"BF-{datetime.now().strftime('%Y%m')}-{str(uuid.uuid4())[:8].upper()}"
    
    def _get_period_info(self, schedule: str) -> Dict[str, str]:
        """Get period information based on schedule."""
        now = datetime.now()
        
        if schedule == "daily":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1) - timedelta(seconds=1)
        elif schedule == "weekly":
            days_since_monday = now.weekday()
            start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days_since_monday)
            end = start + timedelta(days=7) - timedelta(seconds=1)
        else:  # monthly
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if now.month == 12:
                end = start.replace(year=now.year + 1, month=1) - timedelta(seconds=1)
            else:
                end = start.replace(month=now.month + 1) - timedelta(seconds=1)
        
        return {
            "start": start.strftime("%B %d, %Y"),
            "end": end.strftime("%B %d, %Y")
        }
    
    def _format_usage_summary(self, usage_data: UsageData) -> Dict[str, Any]:
        """Format usage summary for display."""
        return {
            "total_requests": f"{usage_data.total_requests:,}",
            "total_tokens": f"{usage_data.total_tokens:,}",
            "prompt_tokens": f"{usage_data.total_prompt_tokens:,}",
            "completion_tokens": f"{usage_data.total_completion_tokens:,}"
        }
    
    def _format_cost_breakdown(self, usage_data: UsageData) -> List[Dict[str, Any]]:
        """Format cost breakdown by model."""
        breakdown = []
        for model, requests in usage_data.models_used.items():
            # Calculate approximate cost for this model
            # This is simplified - in practice you'd need more detailed tracking
            model_percentage = requests / usage_data.total_requests
            model_cost = usage_data.total_cost_usd * model_percentage
            
            breakdown.append({
                "model": model,
                "requests": requests,
                "cost": model_cost
            })
        
        return sorted(breakdown, key=lambda x: x["cost"], reverse=True)
    
    def _format_daily_usage(self, daily_breakdown: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format daily usage for display."""
        formatted = []
        for day in daily_breakdown:
            formatted.append({
                "date": datetime.fromisoformat(day["date"]).strftime("%b %d"),
                "requests": day["requests"],
                "total_tokens": day["prompt_tokens"] + day["completion_tokens"],
                "cost": day["cost_usd"]
            })
        
        return formatted
    
    def _format_models_breakdown(self, models_used: Dict[str, int]) -> List[Dict[str, Any]]:
        """Format models breakdown for display."""
        breakdown = []
        for model, requests in models_used.items():
            breakdown.append({
                "name": model.replace("-", " ").title(),
                "requests": f"{requests:,}"
            })
        
        return sorted(breakdown, key=lambda x: int(x["requests"].replace(",", "")), reverse=True)
    
    def _calculate_next_receipt_date(self, schedule: str) -> str:
        """Calculate the next receipt generation date."""
        now = datetime.now()
        
        if schedule == "daily":
            next_date = now + timedelta(days=1)
        elif schedule == "weekly":
            days_until_next_monday = 7 - now.weekday()
            if days_until_next_monday == 7:
                days_until_next_monday = 0
            next_date = now + timedelta(days=days_until_next_monday)
        else:  # monthly
            if now.month == 12:
                next_date = now.replace(year=now.year + 1, month=1, day=1)
            else:
                next_date = now.replace(month=now.month + 1, day=1)
        
        return next_date.strftime("%B %d, %Y")