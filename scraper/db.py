import psycopg2
import os

def connect_db():
    """Connect to PostgreSQL database"""
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME", "financial_files"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "scraper_secret_password"),
        host=os.getenv("DB_HOST", "scraper-postgres"),
        port=os.getenv("DB_PORT", "5432")
    )