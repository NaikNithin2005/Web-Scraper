"""
Database connection and management.
Supports SQLite (default) with optional MongoDB/PostgreSQL support.
"""

import sqlite3
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
from loguru import logger


class Database:
    """
    Database manager for the scraper.
    Supports SQLite by default, with extensibility for other databases.
    """
    
    def __init__(self, db_path: str = "scraper.db", db_type: str = "sqlite"):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to database file (SQLite) or connection string
            db_type: Database type ("sqlite", "mongodb", "postgresql")
        """
        self.db_path = db_path
        self.db_type = db_type
        self.conn: Optional[sqlite3.Connection] = None
        
        if db_type == "sqlite":
            self._init_sqlite()
        elif db_type == "mongodb":
            self._init_mongodb()
        elif db_type == "postgresql":
            self._init_postgresql()
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    
    def _init_sqlite(self):
        """Initialize SQLite database."""
        # Ensure directory exists
        db_file = Path(self.db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
        logger.info(f"SQLite database initialized: {self.db_path}")
    
    def _init_mongodb(self):
        """Initialize MongoDB connection."""
        try:
            from pymongo import MongoClient
            self.mongo_client = MongoClient(self.db_path)
            self.mongo_db = self.mongo_client.get_database()
            logger.info("MongoDB connection initialized")
        except ImportError:
            logger.error("pymongo not installed. Install with: pip install pymongo")
            raise
    
    def _init_postgresql(self):
        """Initialize PostgreSQL connection."""
        try:
            import psycopg2
            self.pg_conn = psycopg2.connect(self.db_path)
            self.pg_conn.autocommit = True
            logger.info("PostgreSQL connection initialized")
        except ImportError:
            logger.error("psycopg2 not installed. Install with: pip install psycopg2-binary")
            raise
    
    def _create_tables(self):
        """Create all required tables."""
        cursor = self.conn.cursor()
        
        # Products table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                title TEXT,
                price REAL,
                brand TEXT,
                rating REAL,
                availability BOOLEAN,
                description TEXT,
                image_url TEXT,
                source TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Price history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                price REAL NOT NULL,
                currency TEXT DEFAULT 'USD',
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)
        
        # Scrape jobs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scrape_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                method TEXT,
                result TEXT,
                error TEXT,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # User sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                user_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_url ON products(url)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_price_history_product ON price_history(product_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_price_history_date ON price_history(recorded_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_scrape_jobs_status ON scrape_jobs(status)")
        
        self.conn.commit()
        logger.info("Database tables created successfully")
    
    def insert_product(self, product_data: Dict[str, Any]) -> int:
        """
        Insert or update a product.
        
        Args:
            product_data: Product data dict
            
        Returns:
            Product ID
        """
        cursor = self.conn.cursor()
        
        # Check if product exists
        cursor.execute("SELECT id FROM products WHERE url = ?", (product_data.get("url"),))
        existing = cursor.fetchone()
        
        metadata = json.dumps(product_data.get("metadata", {}))
        
        if existing:
            # Update existing product
            cursor.execute("""
                UPDATE products 
                SET title = ?, price = ?, brand = ?, rating = ?, 
                    availability = ?, description = ?, image_url = ?, 
                    source = ?, metadata = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                product_data.get("title"),
                product_data.get("price"),
                product_data.get("brand"),
                product_data.get("rating"),
                product_data.get("availability", False),
                product_data.get("description"),
                product_data.get("image_url"),
                product_data.get("source"),
                metadata,
                existing[0]
            ))
            product_id = existing[0]
        else:
            # Insert new product
            cursor.execute("""
                INSERT INTO products 
                (url, title, price, brand, rating, availability, description, image_url, source, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                product_data.get("url"),
                product_data.get("title"),
                product_data.get("price"),
                product_data.get("brand"),
                product_data.get("rating"),
                product_data.get("availability", False),
                product_data.get("description"),
                product_data.get("image_url"),
                product_data.get("source"),
                metadata
            ))
            product_id = cursor.lastrowid
        
        self.conn.commit()
        return product_id
    
    def add_price_history(self, product_id: int, price: float, currency: str = "USD"):
        """
        Add price history entry.
        
        Args:
            product_id: Product ID
            price: Price value
            currency: Currency code
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO price_history (product_id, price, currency)
            VALUES (?, ?, ?)
        """, (product_id, price, currency))
        self.conn.commit()
    
    def get_price_history(self, product_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get price history for a product.
        
        Args:
            product_id: Product ID
            limit: Maximum number of records
            
        Returns:
            List of price history records
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT price, currency, recorded_at
            FROM price_history
            WHERE product_id = ?
            ORDER BY recorded_at DESC
            LIMIT ?
        """, (product_id, limit))
        
        return [
            {
                "price": row[0],
                "currency": row[1],
                "recorded_at": row[2]
            }
            for row in cursor.fetchall()
        ]
    
    def create_scrape_job(self, url: str, method: str = "auto") -> int:
        """
        Create a new scrape job.
        
        Args:
            url: URL to scrape
            method: Scraping method
            
        Returns:
            Job ID
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO scrape_jobs (url, status, method, started_at)
            VALUES (?, 'pending', ?, CURRENT_TIMESTAMP)
        """, (url, method))
        self.conn.commit()
        return cursor.lastrowid
    
    def update_scrape_job(self, job_id: int, status: str, result: Optional[Dict] = None, error: Optional[str] = None):
        """
        Update scrape job status.
        
        Args:
            job_id: Job ID
            status: New status
            result: Result data
            error: Error message
        """
        cursor = self.conn.cursor()
        result_json = json.dumps(result) if result else None
        
        cursor.execute("""
            UPDATE scrape_jobs
            SET status = ?, result = ?, error = ?, completed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (status, result_json, error, job_id))
        self.conn.commit()
    
    def get_product_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Get product by URL."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM products WHERE url = ?", (url,))
        row = cursor.fetchone()
        
        if row:
            return dict(row)
        return None
    
    def get_all_products(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all products."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM products ORDER BY updated_at DESC LIMIT ?", (limit,))
        return [dict(row) for row in cursor.fetchall()]
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

