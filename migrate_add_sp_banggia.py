"""
Migration script to add sp_banggia column to orders table
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import engine

def migrate_add_sp_banggia():
    """Add sp_banggia column to orders table if it doesn't exist"""
    try:
        with engine.connect() as conn:
            # Check if column exists
            check_query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='orders' AND column_name='sp_banggia'
            """)
            result = conn.execute(check_query).fetchone()
            
            if result:
                print("[OK] Column 'sp_banggia' already exists in 'orders' table")
                return
            
            # Add column
            alter_query = text("""
                ALTER TABLE orders 
                ADD COLUMN sp_banggia VARCHAR(100)
            """)
            conn.execute(alter_query)
            conn.commit()
            
            print("[OK] Successfully added 'sp_banggia' column to 'orders' table")
            
    except Exception as e:
        print(f"[ERROR] Error adding column: {str(e)}")
        raise

if __name__ == "__main__":
    print("Running migration: Add sp_banggia to orders table...")
    migrate_add_sp_banggia()
    print("Migration completed!")

