"""
Database migrations for handling schema changes
"""
from sqlalchemy import text, inspect
from sqlalchemy.exc import SQLAlchemyError
from .database import engine
from .logger import log_info, log_success, log_warning, log_error


def run_migrations():
    """Run database migrations"""
    try:
        log_info("MIGRATIONS", "Bắt đầu kiểm tra và chạy migrations...")
        
        with engine.connect() as connection:
            # Migration 1: Add users.address column
            log_info("MIGRATIONS", "Kiểm tra cột address trong bảng users...")
            connection.execute(text("""
                DO $$ 
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='users' AND column_name='address'
                    ) THEN
                        ALTER TABLE users ADD COLUMN address VARCHAR(255);
                    END IF;
                END $$;
            """))
            connection.commit()
            log_success("MIGRATIONS", "Đã thêm cột address vào bảng users (nếu chưa có)")
            
            # Migration 2: Add shops.type column
            log_info("MIGRATIONS", "Kiểm tra cột type trong bảng shops...")
            connection.execute(text("""
                DO $$ 
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='shops' AND column_name='type'
                    ) THEN
                        ALTER TABLE shops ADD COLUMN type VARCHAR(50);
                    END IF;
                END $$;
            """))
            connection.commit()
            log_success("MIGRATIONS", "Đã thêm cột type vào bảng shops (nếu chưa có)")
            
            # Migration 3: Add accounts.total_spent column
            log_info("MIGRATIONS", "Kiểm tra cột total_spent trong bảng accounts...")
            connection.execute(text("""
                DO $$ 
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='accounts' AND column_name='total_spent'
                    ) THEN
                        ALTER TABLE accounts ADD COLUMN total_spent FLOAT DEFAULT 0.0;
                    END IF;
                END $$;
            """))
            connection.commit()
            log_success("MIGRATIONS", "Đã thêm cột total_spent vào bảng accounts (nếu chưa có)")
            
            # Migration 4: Update warehouses table
            log_info("MIGRATIONS", "Kiểm tra và cập nhật bảng warehouses...")
            
            # Remove old columns if exist
            connection.execute(text("""
                DO $$ 
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='warehouses' AND column_name='so_luong_sp'
                    ) THEN
                        ALTER TABLE warehouses DROP COLUMN so_luong_sp;
                    END IF;
                END $$;
            """))
            connection.commit()
            
            connection.execute(text("""
                DO $$ 
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='warehouses' AND column_name='nhom_san_pham'
                    ) THEN
                        ALTER TABLE warehouses DROP COLUMN nhom_san_pham;
                    END IF;
                END $$;
            """))
            connection.commit()
            
            # Add new columns if not exist
            connection.execute(text("""
                DO $$ 
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='warehouses' AND column_name='ma_sp'
                    ) THEN
                        ALTER TABLE warehouses ADD COLUMN ma_sp VARCHAR(20);
                    END IF;
                END $$;
            """))
            connection.commit()
            
            connection.execute(text("""
                DO $$ 
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='warehouses' AND column_name='gia_nhap'
                    ) THEN
                        ALTER TABLE warehouses ADD COLUMN gia_nhap FLOAT DEFAULT 0.0;
                    END IF;
                END $$;
            """))
            connection.commit()
            
            log_success("MIGRATIONS", "Đã cập nhật bảng warehouses")
            
            # Migration 5: Add orders.sp_banggia column
            log_info("MIGRATIONS", "Kiểm tra cột sp_banggia trong bảng orders...")
            connection.execute(text("""
                DO $$ 
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='orders' AND column_name='sp_banggia'
                    ) THEN
                        ALTER TABLE orders ADD COLUMN sp_banggia VARCHAR(100);
                    END IF;
                END $$;
            """))
            connection.commit()
            log_success("MIGRATIONS", "Đã thêm cột sp_banggia vào bảng orders (nếu chưa có)")
            
            # Migration 6: Add invoices.loai_hd column
            log_info("MIGRATIONS", "Kiểm tra cột loai_hd trong bảng invoices...")
            connection.execute(text("""
                DO $$ 
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='invoices' AND column_name='loai_hd'
                    ) THEN
                        ALTER TABLE invoices ADD COLUMN loai_hd VARCHAR(50);
                    END IF;
                END $$;
            """))
            connection.commit()
            log_success("MIGRATIONS", "Đã thêm cột loai_hd vào bảng invoices (nếu chưa có)")
            
        log_success("MIGRATIONS", "Hoàn thành tất cả migrations!")
        
    except SQLAlchemyError as e:
        log_error("MIGRATIONS", "Lỗi khi chạy migrations", error=e)
        # Don't raise - allow app to start even if migrations fail
    except Exception as e:
        log_error("MIGRATIONS", "Lỗi không xác định khi chạy migrations", error=e)
        # Don't raise - allow app to start even if migrations fail

