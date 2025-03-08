import sqlite3
from datetime import datetime
import logging
from contextlib import contextmanager
from pathlib import Path
import config

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_file=config.DB_FILE):
        self.db_file = db_file
        self.init_db()

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_file)
        try:
            yield conn
        finally:
            conn.close()

    def init_db(self):
        """Initialize database with required tables"""
        create_tables_sql = """
        CREATE TABLE IF NOT EXISTS payments (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            email TEXT,
            phone TEXT,
            payment_date TIMESTAMP,
            transaction_id TEXT,
            amount REAL,
            currency TEXT
        );

        CREATE TABLE IF NOT EXISTS chat_invites (
            user_id INTEGER PRIMARY KEY,
            invite_link TEXT,
            created_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES payments (user_id)
        );
        """
        
        try:
            with self.get_connection() as conn:
                conn.executescript(create_tables_sql)
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {e}")
            raise

    def record_payment(self, user_id: int, username: str, customer_info: dict, 
                      transaction_id: str, amount: float, currency: str):
        """Record successful payment"""
        sql = """
        INSERT INTO payments 
        (user_id, username, full_name, email, phone, payment_date, transaction_id, amount, currency)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        try:
            with self.get_connection() as conn:
                conn.execute(sql, (
                    user_id,
                    username,
                    customer_info['full_name'],
                    customer_info['email'],
                    customer_info['phone'],
                    datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                    transaction_id,
                    amount,
                    currency
                ))
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error recording payment: {e}")
            raise

    def record_chat_invite(self, user_id: int, invite_link: str):
        """Record chat invite link for user"""
        sql = """
        INSERT OR REPLACE INTO chat_invites (user_id, invite_link, created_at)
        VALUES (?, ?, ?)
        """
        try:
            with self.get_connection() as conn:
                conn.execute(sql, (
                    user_id,
                    invite_link,
                    datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                ))
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error recording chat invite: {e}")
            raise

    def get_payment_status(self, user_id: int) -> bool:
        """Check if user has paid for the course"""
        sql = "SELECT EXISTS(SELECT 1 FROM payments WHERE user_id = ?)"
        try:
            with self.get_connection() as conn:
                result = conn.execute(sql, (user_id,)).fetchone()
                return bool(result[0])
        except sqlite3.Error as e:
            logger.error(f"Error checking payment status: {e}")
            return False

    def get_chat_invite(self, user_id: int) -> str:
        """Get chat invite link for paid user"""
        sql = "SELECT invite_link FROM chat_invites WHERE user_id = ?"
        try:
            with self.get_connection() as conn:
                result = conn.execute(sql, (user_id,)).fetchone()
                return result[0] if result else None
        except sqlite3.Error as e:
            logger.error(f"Error getting chat invite: {e}")
            return None

    def get_user_info(self, user_id: int) -> dict:
        """Get user's payment and access information"""
        sql = """
        SELECT p.*, ci.invite_link
        FROM payments p
        LEFT JOIN chat_invites ci ON p.user_id = ci.user_id
        WHERE p.user_id = ?
        """
        try:
            with self.get_connection() as conn:
                result = conn.execute(sql, (user_id,)).fetchone()
                if result:
                    return {
                        'user_id': result[0],
                        'username': result[1],
                        'full_name': result[2],
                        'email': result[3],
                        'phone': result[4],
                        'payment_date': result[5],
                        'transaction_id': result[6],
                        'amount': result[7],
                        'currency': result[8],
                        'invite_link': result[9]
                    }
                return None
        except sqlite3.Error as e:
            logger.error(f"Error getting user info: {e}")
            return None