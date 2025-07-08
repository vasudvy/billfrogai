"""Local database for storing usage data and receipt history."""

import sqlite3
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class LocalDatabase:
    """Local SQLite database for storing Billfrog data."""
    
    def __init__(self, db_path: Optional[Path] = None):
        """Initialize the local database."""
        if db_path is None:
            db_path = Path.home() / ".billfrog" / "data.db"
        
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize the database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Usage records table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usage_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_name TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    model TEXT NOT NULL,
                    prompt_tokens INTEGER NOT NULL,
                    completion_tokens INTEGER NOT NULL,
                    total_tokens INTEGER NOT NULL,
                    cost_usd REAL NOT NULL,
                    request_type TEXT DEFAULT 'chat_completion',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Receipt history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS receipt_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_name TEXT NOT NULL,
                    receipt_id TEXT UNIQUE NOT NULL,
                    period_start TEXT NOT NULL,
                    period_end TEXT NOT NULL,
                    total_cost_usd REAL NOT NULL,
                    total_requests INTEGER NOT NULL,
                    total_tokens INTEGER NOT NULL,
                    email_sent_to TEXT NOT NULL,
                    email_sent_at TEXT NOT NULL,
                    schedule_type TEXT NOT NULL,
                    usage_data_json TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Email logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS email_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_name TEXT,
                    to_email TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    success BOOLEAN NOT NULL,
                    error_message TEXT,
                    timestamp TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Agent statistics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_name TEXT NOT NULL,
                    date TEXT NOT NULL,
                    total_requests INTEGER DEFAULT 0,
                    total_tokens INTEGER DEFAULT 0,
                    total_cost_usd REAL DEFAULT 0.0,
                    models_used_json TEXT DEFAULT '{}',
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(agent_name, date)
                )
            """)
            
            conn.commit()
            logger.info("Database initialized successfully")
    
    def record_usage(self, agent_name: str, model: str, prompt_tokens: int, 
                    completion_tokens: int, cost_usd: float, 
                    request_type: str = "chat_completion") -> bool:
        """Record a single usage event."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO usage_records 
                    (agent_name, timestamp, model, prompt_tokens, completion_tokens, 
                     total_tokens, cost_usd, request_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    agent_name,
                    datetime.now().isoformat(),
                    model,
                    prompt_tokens,
                    completion_tokens,
                    prompt_tokens + completion_tokens,
                    cost_usd,
                    request_type
                ))
                
                conn.commit()
                
                # Update daily statistics
                self._update_daily_stats(agent_name, model, 1, 
                                       prompt_tokens + completion_tokens, cost_usd)
                
                return True
        except Exception as e:
            logger.error(f"Error recording usage: {e}")
            return False
    
    def get_usage_data(self, agent_name: str, days_back: int = 7) -> Dict[str, Any]:
        """Get aggregated usage data for an agent."""
        try:
            start_date = (datetime.now() - 
                         timedelta(days=days_back)).strftime("%Y-%m-%d")
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get total usage statistics
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_requests,
                        SUM(prompt_tokens) as total_prompt_tokens,
                        SUM(completion_tokens) as total_completion_tokens,
                        SUM(total_tokens) as total_tokens,
                        SUM(cost_usd) as total_cost
                    FROM usage_records 
                    WHERE agent_name = ? AND date(timestamp) >= ?
                """, (agent_name, start_date))
                
                totals = cursor.fetchone()
                
                # Get model breakdown
                cursor.execute("""
                    SELECT model, COUNT(*) as requests
                    FROM usage_records 
                    WHERE agent_name = ? AND date(timestamp) >= ?
                    GROUP BY model
                """, (agent_name, start_date))
                
                models_used = dict(cursor.fetchall())
                
                # Get daily breakdown
                cursor.execute("""
                    SELECT 
                        date(timestamp) as date,
                        COUNT(*) as requests,
                        SUM(prompt_tokens) as prompt_tokens,
                        SUM(completion_tokens) as completion_tokens,
                        SUM(cost_usd) as cost_usd
                    FROM usage_records 
                    WHERE agent_name = ? AND date(timestamp) >= ?
                    GROUP BY date(timestamp)
                    ORDER BY date(timestamp)
                """, (agent_name, start_date))
                
                daily_breakdown = []
                for row in cursor.fetchall():
                    daily_breakdown.append({
                        "date": row[0],
                        "requests": row[1],
                        "prompt_tokens": row[2],
                        "completion_tokens": row[3],
                        "cost_usd": row[4]
                    })
                
                return {
                    "period_start": start_date,
                    "period_end": datetime.now().strftime("%Y-%m-%d"),
                    "total_requests": totals[0] or 0,
                    "total_prompt_tokens": totals[1] or 0,
                    "total_completion_tokens": totals[2] or 0,
                    "total_tokens": totals[3] or 0,
                    "total_cost_usd": totals[4] or 0.0,
                    "models_used": models_used,
                    "daily_breakdown": daily_breakdown
                }
                
        except Exception as e:
            logger.error(f"Error getting usage data: {e}")
            return {}
    
    def save_receipt(self, agent_name: str, receipt_id: str, period_start: str,
                    period_end: str, total_cost: float, total_requests: int,
                    total_tokens: int, email_sent_to: str, schedule_type: str,
                    usage_data: Dict[str, Any]) -> bool:
        """Save receipt information to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO receipt_history 
                    (agent_name, receipt_id, period_start, period_end, 
                     total_cost_usd, total_requests, total_tokens, 
                     email_sent_to, email_sent_at, schedule_type, usage_data_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    agent_name,
                    receipt_id,
                    period_start,
                    period_end,
                    total_cost,
                    total_requests,
                    total_tokens,
                    email_sent_to,
                    datetime.now().isoformat(),
                    schedule_type,
                    json.dumps(usage_data)
                ))
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving receipt: {e}")
            return False
    
    def get_receipt_history(self, agent_name: Optional[str] = None, 
                          limit: int = 50) -> List[Dict[str, Any]]:
        """Get receipt history."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if agent_name:
                    cursor.execute("""
                        SELECT * FROM receipt_history 
                        WHERE agent_name = ?
                        ORDER BY created_at DESC 
                        LIMIT ?
                    """, (agent_name, limit))
                else:
                    cursor.execute("""
                        SELECT * FROM receipt_history 
                        ORDER BY created_at DESC 
                        LIMIT ?
                    """, (limit,))
                
                columns = [desc[0] for desc in cursor.description]
                receipts = []
                
                for row in cursor.fetchall():
                    receipt = dict(zip(columns, row))
                    receipt['usage_data_json'] = json.loads(receipt['usage_data_json'])
                    receipts.append(receipt)
                
                return receipts
        except Exception as e:
            logger.error(f"Error getting receipt history: {e}")
            return []
    
    def log_email(self, agent_name: Optional[str], to_email: str, subject: str,
                 success: bool, error_message: Optional[str] = None) -> bool:
        """Log email sending activity."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO email_logs 
                    (agent_name, to_email, subject, success, error_message, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    agent_name,
                    to_email,
                    subject,
                    success,
                    error_message,
                    datetime.now().isoformat()
                ))
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error logging email: {e}")
            return False
    
    def _update_daily_stats(self, agent_name: str, model: str, requests: int,
                           tokens: int, cost: float) -> None:
        """Update daily statistics for an agent."""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get existing stats for today
                cursor.execute("""
                    SELECT total_requests, total_tokens, total_cost_usd, models_used_json
                    FROM agent_stats 
                    WHERE agent_name = ? AND date = ?
                """, (agent_name, today))
                
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing record
                    new_requests = existing[0] + requests
                    new_tokens = existing[1] + tokens
                    new_cost = existing[2] + cost
                    
                    models_used = json.loads(existing[3])
                    models_used[model] = models_used.get(model, 0) + requests
                    
                    cursor.execute("""
                        UPDATE agent_stats 
                        SET total_requests = ?, total_tokens = ?, 
                            total_cost_usd = ?, models_used_json = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE agent_name = ? AND date = ?
                    """, (new_requests, new_tokens, new_cost, 
                         json.dumps(models_used), agent_name, today))
                else:
                    # Create new record
                    models_used = {model: requests}
                    cursor.execute("""
                        INSERT INTO agent_stats 
                        (agent_name, date, total_requests, total_tokens, 
                         total_cost_usd, models_used_json)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (agent_name, today, requests, tokens, cost, 
                         json.dumps(models_used)))
                
                conn.commit()
        except Exception as e:
            logger.error(f"Error updating daily stats: {e}")
    
    def get_agent_summary(self, agent_name: str, days: int = 30) -> Dict[str, Any]:
        """Get summary statistics for an agent."""
        try:
            start_date = (datetime.now() - 
                         timedelta(days=days)).strftime("%Y-%m-%d")
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        SUM(total_requests) as total_requests,
                        SUM(total_tokens) as total_tokens,
                        SUM(total_cost_usd) as total_cost,
                        COUNT(*) as active_days
                    FROM agent_stats 
                    WHERE agent_name = ? AND date >= ?
                """, (agent_name, start_date))
                
                summary = cursor.fetchone()
                
                return {
                    "agent_name": agent_name,
                    "period_days": days,
                    "total_requests": summary[0] or 0,
                    "total_tokens": summary[1] or 0,
                    "total_cost_usd": summary[2] or 0.0,
                    "active_days": summary[3] or 0,
                    "avg_daily_cost": (summary[2] or 0) / max(1, summary[3] or 1)
                }
        except Exception as e:
            logger.error(f"Error getting agent summary: {e}")
            return {}
    
    def cleanup_old_data(self, days_to_keep: int = 90) -> bool:
        """Clean up old usage records to manage database size."""
        try:
            cutoff_date = (datetime.now() - 
                          timedelta(days=days_to_keep)).strftime("%Y-%m-%d")
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Remove old usage records
                cursor.execute("""
                    DELETE FROM usage_records 
                    WHERE date(timestamp) < ?
                """, (cutoff_date,))
                
                # Remove old email logs
                cursor.execute("""
                    DELETE FROM email_logs 
                    WHERE date(timestamp) < ?
                """, (cutoff_date,))
                
                # Remove old daily stats
                cursor.execute("""
                    DELETE FROM agent_stats 
                    WHERE date < ?
                """, (cutoff_date,))
                
                conn.commit()
                logger.info(f"Cleaned up data older than {cutoff_date}")
                return True
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            return False