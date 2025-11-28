#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để thêm các cột product_code và product_name vào bảng invoice_items
"""
import sys
from sqlalchemy import text, inspect
from sqlalchemy.exc import SQLAlchemyError
from app.database import engine, SessionLocal

def migrate_invoice_items():
    """Thêm các cột product_code và product_name vào bảng invoice_items nếu chưa có"""
    db = SessionLocal()
    try:
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('invoice_items')]
        
        print("Current columns in invoice_items table:")
        for col in columns:
            print(f"  - {col}")
        
        # Check and add product_code column
        if 'product_code' not in columns:
            print("\nAdding product_code column...")
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE invoice_items ADD COLUMN product_code VARCHAR(20)"))
                conn.commit()
            print("Done: Added product_code column")
        else:
            print("Info: product_code column already exists")
        
        # Check and add product_name column
        if 'product_name' not in columns:
            print("\nAdding product_name column...")
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE invoice_items ADD COLUMN product_name VARCHAR(100)"))
                conn.commit()
            print("Done: Added product_name column")
        else:
            print("Info: product_name column already exists")
        
        # Update NULL values if there's old data
        print("\nUpdating data for existing records...")
        with engine.connect() as conn:
            # Update product_code and product_name from products table
            result = conn.execute(text("""
                UPDATE invoice_items ii
                SET 
                    product_code = COALESCE(p.ma_sp, ''),
                    product_name = COALESCE(p.ten_sp, '')
                FROM products p
                WHERE ii.product_id = p.id 
                AND (ii.product_code IS NULL OR ii.product_name IS NULL)
            """))
            conn.commit()
            print(f"Done: Updated {result.rowcount} records")
        
        # Set NOT NULL constraint if needed (only when no NULL data)
        print("\nChecking and setting NOT NULL constraints...")
        with engine.connect() as conn:
            # Check if there are NULL values
            null_check = conn.execute(text("""
                SELECT COUNT(*) FROM invoice_items 
                WHERE product_code IS NULL OR product_name IS NULL
            """)).scalar()
            
            if null_check == 0:
                # If no NULL, can add NOT NULL constraint
                try:
                    conn.execute(text("ALTER TABLE invoice_items ALTER COLUMN product_code SET NOT NULL"))
                    conn.execute(text("ALTER TABLE invoice_items ALTER COLUMN product_name SET NOT NULL"))
                    conn.commit()
                    print("Done: Set NOT NULL constraints for product_code and product_name")
                except Exception as e:
                    print(f"Warning: Cannot set NOT NULL constraint: {e}")
            else:
                print(f"Warning: Still have {null_check} records with NULL values, cannot set NOT NULL constraint")
        
        print("\nMigration completed!")
        
    except SQLAlchemyError as e:
        print(f"❌ Lỗi database: {e}")
        import traceback
        print(f"📋 Chi tiết lỗi:\n{traceback.format_exc()}")
        db.rollback()
        sys.exit(1)
    except Exception as e:
        print(f"❌ Lỗi không xác định: {e}")
        import traceback
        print(f"📋 Chi tiết lỗi:\n{traceback.format_exc()}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("MIGRATION: Add product_code and product_name columns to invoice_items")
    print("=" * 60)
    migrate_invoice_items()
    print("=" * 60)

