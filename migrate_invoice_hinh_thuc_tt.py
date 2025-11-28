#!/usr/bin/env python3
"""
Migration script to add hinh_thuc_tt column to invoices table
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text, inspect
from app.database import engine
import codecs

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def migrate():
    """Add hinh_thuc_tt column to invoices table"""
    
    print("=" * 60)
    print("Migration: Add hinh_thuc_tt to invoices table")
    print("=" * 60)
    
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('invoices')]
    
    if 'hinh_thuc_tt' in columns:
        print("✓ Column 'hinh_thuc_tt' already exists in 'invoices' table")
        return
    
    print("\nAdding column 'hinh_thuc_tt' to 'invoices' table...")
    
    with engine.connect() as conn:
        try:
            conn.execute(text("""
                ALTER TABLE invoices 
                ADD COLUMN hinh_thuc_tt VARCHAR(50)
            """))
            conn.commit()
            print("✓ Successfully added column 'hinh_thuc_tt' to 'invoices' table")
        except Exception as e:
            conn.rollback()
            print(f"✗ Error adding column: {e}")
            raise
    
    print("\n" + "=" * 60)
    print("Migration completed successfully!")
    print("=" * 60)

if __name__ == '__main__':
    try:
        migrate()
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        sys.exit(1)

