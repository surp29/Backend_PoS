#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để xóa các cột tk_no và tk_co khỏi bảng general_diary
"""
import sys
import os
from sqlalchemy import text, inspect
from sqlalchemy.exc import SQLAlchemyError
from app.database import engine, SessionLocal

# Fix encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def migrate_general_diary():
    """Xóa các cột tk_no và tk_co khỏi bảng general_diary"""
    db = SessionLocal()
    try:
        inspector = inspect(engine)
        
        # Kiểm tra xem bảng general_diary có tồn tại không
        if 'general_diary' not in inspector.get_table_names():
            print("[ERROR] Bang 'general_diary' khong ton tai!")
            return
        
        columns = {col['name']: col for col in inspector.get_columns('general_diary')}
        
        print("Current columns in general_diary table:")
        for col_name, col_info in columns.items():
            print(f"  - {col_name} ({col_info['type']})")
        
        has_tk_no = 'tk_no' in columns
        has_tk_co = 'tk_co' in columns
        
        if not has_tk_no and not has_tk_co:
            print("\n[INFO] Cac cot tk_no va tk_co da khong con trong bang!")
            return
        
        # Xóa các cột cũ
        print("\n" + "=" * 60)
        print("Xoa cac cot cu...")
        print("=" * 60)
        
        with engine.connect() as conn:
            if has_tk_no:
                print("Dropping tk_no column...")
                try:
                    conn.execute(text("ALTER TABLE general_diary DROP COLUMN tk_no"))
                    conn.commit()
                    print("[OK] Done: Dropped tk_no column")
                except Exception as e:
                    print(f"[WARNING] Could not drop tk_no column: {e}")
                    print("  You may need to drop it manually")
            
            if has_tk_co:
                print("Dropping tk_co column...")
                try:
                    conn.execute(text("ALTER TABLE general_diary DROP COLUMN tk_co"))
                    conn.commit()
                    print("[OK] Done: Dropped tk_co column")
                except Exception as e:
                    print(f"[WARNING] Could not drop tk_co column: {e}")
                    print("  You may need to drop it manually")
        
        # Kiểm tra kết quả
        print("\n" + "=" * 60)
        print("Kiem tra ket qua...")
        print("=" * 60)
        
        inspector = inspect(engine)
        final_columns = {col['name']: col for col in inspector.get_columns('general_diary')}
        
        print("Final columns in general_diary table:")
        for col_name, col_info in final_columns.items():
            print(f"  - {col_name} ({col_info['type']})")
        
        if 'tk_no' not in final_columns and 'tk_co' not in final_columns:
            print("\n[OK] Migration completed successfully!")
        else:
            print("\n[WARNING] Some columns may still exist. Check manually.")
        
        print("=" * 60)
        
    except SQLAlchemyError as e:
        print(f"\n[ERROR] Loi database: {e}")
        import traceback
        print(f"Chi tiet loi:\n{traceback.format_exc()}")
        db.rollback()
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Loi khong xac dinh: {e}")
        import traceback
        print(f"Chi tiet loi:\n{traceback.format_exc()}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("MIGRATION: Remove tk_no and tk_co columns from general_diary")
    print("=" * 60)
    print("\nWARNING: This will modify the database structure!")
    print("   Make sure you have a backup before proceeding.\n")
    
    # Auto-confirm if running non-interactively
    if sys.stdin.isatty():
        response = input("Do you want to continue? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("Migration cancelled.")
            sys.exit(0)
    else:
        print("Running in non-interactive mode, proceeding automatically...")
    
    migrate_general_diary()

