#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để thay đổi cấu trúc bảng accounts:
- Thay tk_no -> ma_khach_hang (String)
- Thay tk_co -> ngay_sinh (Date)
"""
import sys
import os
from datetime import datetime
from sqlalchemy import text, inspect
from sqlalchemy.exc import SQLAlchemyError
from app.database import engine, SessionLocal

# Fix encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def migrate_accounts():
    """Thay đổi cấu trúc bảng accounts từ tk_no/tk_co sang ma_khach_hang/ngay_sinh"""
    db = SessionLocal()
    try:
        inspector = inspect(engine)
        
        # Kiểm tra xem bảng accounts có tồn tại không
        if 'accounts' not in inspector.get_table_names():
            print("[ERROR] Bang 'accounts' khong ton tai!")
            return
        
        columns = {col['name']: col for col in inspector.get_columns('accounts')}
        
        print("Current columns in accounts table:")
        for col_name, col_info in columns.items():
            print(f"  - {col_name} ({col_info['type']})")
        
        has_tk_no = 'tk_no' in columns
        has_tk_co = 'tk_co' in columns
        has_ma_khach_hang = 'ma_khach_hang' in columns
        has_ngay_sinh = 'ngay_sinh' in columns
        
        # Bước 1: Thêm cột mới nếu chưa có
        print("\n" + "=" * 60)
        print("Bước 1: Thêm các cột mới...")
        print("=" * 60)
        
        with engine.connect() as conn:
            if not has_ma_khach_hang:
                print("Adding ma_khach_hang column...")
                conn.execute(text("ALTER TABLE accounts ADD COLUMN ma_khach_hang VARCHAR(20)"))
                conn.commit()
                print("[OK] Done: Added ma_khach_hang column")
            else:
                print("Info: ma_khach_hang column already exists")
            
            if not has_ngay_sinh:
                print("Adding ngay_sinh column...")
                conn.execute(text("ALTER TABLE accounts ADD COLUMN ngay_sinh DATE"))
                conn.commit()
                print("[OK] Done: Added ngay_sinh column")
            else:
                print("Info: ngay_sinh column already exists")
        
        # Bước 2: Copy dữ liệu từ cột cũ sang cột mới (nếu có)
        print("\n" + "=" * 60)
        print("Bước 2: Copy dữ liệu từ cột cũ sang cột mới...")
        print("=" * 60)
        
        with engine.connect() as conn:
            # Copy tk_no -> ma_khach_hang
            if has_tk_no and not has_ma_khach_hang:
                print("Copying data from tk_no to ma_khach_hang...")
                result = conn.execute(text("""
                    UPDATE accounts 
                    SET ma_khach_hang = tk_no 
                    WHERE tk_no IS NOT NULL AND tk_no != ''
                """))
                conn.commit()
                print(f"[OK] Done: Copied {result.rowcount} records")
            elif has_tk_no and has_ma_khach_hang:
                # Nếu cả hai đều có, chỉ copy những record chưa có ma_khach_hang
                print("Copying data from tk_no to ma_khach_hang (only NULL values)...")
                result = conn.execute(text("""
                    UPDATE accounts 
                    SET ma_khach_hang = tk_no 
                    WHERE tk_no IS NOT NULL AND tk_no != '' 
                    AND (ma_khach_hang IS NULL OR ma_khach_hang = '')
                """))
                conn.commit()
                print(f"[OK] Done: Copied {result.rowcount} records")
            
            # Copy tk_co -> ngay_sinh (cần convert string sang date)
            if has_tk_co:
                print("Copying data from tk_co to ngay_sinh...")
                # Kiểm tra loại database
                db_type = str(engine.url).split(':')[0]
                
                try:
                    if 'postgresql' in db_type.lower():
                        # PostgreSQL: Thử convert các định dạng date phổ biến
                        result = conn.execute(text("""
                            UPDATE accounts 
                            SET ngay_sinh = CASE 
                                WHEN tk_co ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' THEN tk_co::DATE
                                WHEN tk_co ~ '^[0-9]{2}/[0-9]{2}/[0-9]{4}$' THEN TO_DATE(tk_co, 'DD/MM/YYYY')
                                WHEN tk_co ~ '^[0-9]{2}-[0-9]{2}-[0-9]{4}$' THEN TO_DATE(tk_co, 'DD-MM-YYYY')
                                ELSE NULL
                            END
                            WHERE tk_co IS NOT NULL 
                            AND tk_co != ''
                            AND (ngay_sinh IS NULL)
                        """))
                    else:
                        # SQLite hoặc database khác: Thử convert đơn giản
                        result = conn.execute(text("""
                            UPDATE accounts 
                            SET ngay_sinh = CASE 
                                WHEN tk_co LIKE '____-__-__' THEN DATE(tk_co)
                                ELSE NULL
                            END
                            WHERE tk_co IS NOT NULL 
                            AND tk_co != ''
                            AND (ngay_sinh IS NULL)
                        """))
                    
                    conn.commit()
                    print(f"[OK] Done: Converted {result.rowcount} records")
                    
                    # Kiểm tra xem có record nào không convert được không
                    if has_tk_co:
                        failed_count = conn.execute(text("""
                            SELECT COUNT(*) FROM accounts 
                            WHERE tk_co IS NOT NULL 
                            AND tk_co != ''
                            AND ngay_sinh IS NULL
                        """)).scalar()
                        if failed_count > 0:
                            print(f"[WARNING] {failed_count} records could not be converted")
                            print("  These tk_co values may need manual conversion")
                            
                except Exception as e:
                    print(f"[WARNING] Could not auto-convert dates: {e}")
                    print("  You may need to manually update ngay_sinh values")
                    print("  Note: tk_co values will be preserved for manual review")
        
        # Bước 3: Xóa các cột cũ (nếu đã có cột mới)
        print("\n" + "=" * 60)
        print("Bước 3: Xóa các cột cũ...")
        print("=" * 60)
        
        # Refresh column info after adding new columns
        inspector = inspect(engine)
        final_columns_before_drop = {col['name']: col for col in inspector.get_columns('accounts')}
        has_ma_khach_hang_final = 'ma_khach_hang' in final_columns_before_drop
        has_ngay_sinh_final = 'ngay_sinh' in final_columns_before_drop
        
        with engine.connect() as conn:
            if has_tk_no and has_ma_khach_hang_final:
                print("Dropping tk_no column...")
                try:
                    conn.execute(text("ALTER TABLE accounts DROP COLUMN tk_no"))
                    conn.commit()
                    print("[OK] Done: Dropped tk_no column")
                except Exception as e:
                    print(f"[WARNING] Could not drop tk_no column: {e}")
                    print("  You may need to drop it manually")
            
            if has_tk_co and has_ngay_sinh_final:
                print("Dropping tk_co column...")
                try:
                    conn.execute(text("ALTER TABLE accounts DROP COLUMN tk_co"))
                    conn.commit()
                    print("[OK] Done: Dropped tk_co column")
                except Exception as e:
                    print(f"[WARNING] Could not drop tk_co column: {e}")
                    print("  You may need to drop it manually")
        
        # Bước 4: Kiểm tra kết quả
        print("\n" + "=" * 60)
        print("Bước 4: Kiểm tra kết quả...")
        print("=" * 60)
        
        inspector = inspect(engine)
        final_columns = {col['name']: col for col in inspector.get_columns('accounts')}
        
        print("Final columns in accounts table:")
        for col_name, col_info in final_columns.items():
            print(f"  - {col_name} ({col_info['type']})")
        
        # Đếm số record có dữ liệu
        with engine.connect() as conn:
            if 'ma_khach_hang' in final_columns:
                count_ma = conn.execute(text("SELECT COUNT(*) FROM accounts WHERE ma_khach_hang IS NOT NULL AND ma_khach_hang != ''")).scalar()
                print(f"\nRecords with ma_khach_hang: {count_ma}")
            
            if 'ngay_sinh' in final_columns:
                count_ngay = conn.execute(text("SELECT COUNT(*) FROM accounts WHERE ngay_sinh IS NOT NULL")).scalar()
                print(f"Records with ngay_sinh: {count_ngay}")
        
        print("\n" + "=" * 60)
        print("[OK] Migration completed successfully!")
        print("=" * 60)
        
    except SQLAlchemyError as e:
        print(f"\n[ERROR] Loi database: {e}")
        import traceback
        print(f"📋 Chi tiết lỗi:\n{traceback.format_exc()}")
        db.rollback()
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Loi khong xac dinh: {e}")
        import traceback
        print(f"📋 Chi tiết lỗi:\n{traceback.format_exc()}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("MIGRATION: Change accounts table structure")
    print("  tk_no -> ma_khach_hang (VARCHAR)")
    print("  tk_co -> ngay_sinh (DATE)")
    print("=" * 60)
    print("\nWARNING: This will modify the database structure!")
    print("   Make sure you have a backup before proceeding.\n")
    
    # Auto-confirm if running non-interactively
    import sys
    if sys.stdin.isatty():
        response = input("Do you want to continue? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("Migration cancelled.")
            sys.exit(0)
    else:
        print("Running in non-interactive mode, proceeding automatically...")
    
    migrate_accounts()

