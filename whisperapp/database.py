"""SQLite database for transcription history and statistics."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional


class Database:
    """
    SQLite database manager for WhisperApp.
    
    Stores transcription history and calculates usage statistics.
    Database location: ~/.whisperapp/history.db
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the database.
        
        Args:
            db_path: Custom database path (default: ~/.whisperapp/history.db)
        """
        if db_path:
            self.db_path = Path(db_path)
        else:
            self.db_path = Path.home() / ".whisperapp" / "history.db"
        
        # Ensure directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database schema
        self._init_db()
    
    def _init_db(self):
        """Create database tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS transcriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT NOT NULL,
                    raw_text TEXT,
                    word_count INTEGER DEFAULT 0,
                    duration_seconds REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            
            conn.commit()
    
    def save_transcription(
        self, 
        text: str, 
        raw_text: Optional[str] = None,
        duration: float = 0.0
    ) -> int:
        """
        Save a transcription to the database.
        
        Args:
            text: Cleaned transcription text
            raw_text: Original transcription before cleanup
            duration: Recording duration in seconds
            
        Returns:
            ID of the inserted record
        """
        word_count = len(text.split()) if text else 0
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """INSERT INTO transcriptions 
                   (text, raw_text, word_count, duration_seconds) 
                   VALUES (?, ?, ?, ?)""",
                (text, raw_text, word_count, duration)
            )
            conn.commit()
            return cursor.lastrowid
    
    def get_transcriptions(
        self, 
        limit: int = 50, 
        offset: int = 0
    ) -> List[Dict]:
        """
        Get recent transcriptions.
        
        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip (for pagination)
            
        Returns:
            List of transcription dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """SELECT id, text, raw_text, word_count, duration_seconds, created_at
                   FROM transcriptions 
                   ORDER BY created_at DESC 
                   LIMIT ? OFFSET ?""",
                (limit, offset)
            )
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_transcription(self, transcription_id: int) -> Optional[Dict]:
        """Get a single transcription by ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM transcriptions WHERE id = ?",
                (transcription_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def delete_transcription(self, transcription_id: int) -> bool:
        """Delete a transcription by ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM transcriptions WHERE id = ?",
                (transcription_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def get_statistics(self) -> Dict:
        """
        Calculate usage statistics.
        
        Returns:
            Dictionary with statistics:
            - total_transcriptions: Number of transcriptions
            - total_words: Total words transcribed
            - total_minutes: Total recording time in minutes
            - avg_wpm: Average words per minute (speaking speed)
            - today_count: Transcriptions made today
            - today_words: Words transcribed today
        """
        with sqlite3.connect(self.db_path) as conn:
            # Overall statistics
            row = conn.execute("""
                SELECT 
                    COUNT(*) as total_transcriptions,
                    COALESCE(SUM(word_count), 0) as total_words,
                    COALESCE(SUM(duration_seconds), 0) / 60.0 as total_minutes,
                    CASE 
                        WHEN SUM(duration_seconds) > 0 
                        THEN SUM(word_count) * 60.0 / SUM(duration_seconds)
                        ELSE 0 
                    END as avg_wpm
                FROM transcriptions
            """).fetchone()
            
            # Today's statistics
            today = datetime.now().strftime("%Y-%m-%d")
            today_row = conn.execute("""
                SELECT 
                    COUNT(*) as today_count,
                    COALESCE(SUM(word_count), 0) as today_words
                FROM transcriptions
                WHERE DATE(created_at) = ?
            """, (today,)).fetchone()
            
            return {
                "total_transcriptions": row[0],
                "total_words": row[1],
                "total_minutes": round(row[2], 1),
                "avg_wpm": round(row[3], 1),
                "today_count": today_row[0],
                "today_words": today_row[1]
            }
    
    def get_setting(self, key: str, default: str = "") -> str:
        """Get a setting value."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT value FROM settings WHERE key = ?",
                (key,)
            )
            row = cursor.fetchone()
            return row[0] if row else default
    
    def set_setting(self, key: str, value: str) -> None:
        """Set a setting value."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)""",
                (key, value)
            )
            conn.commit()
    
    def clear_history(self) -> int:
        """Clear all transcription history. Returns count of deleted records."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM transcriptions")
            conn.commit()
            return cursor.rowcount
