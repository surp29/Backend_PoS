# Migration Script: Thay đổi cấu trúc bảng accounts

## Mô tả
Script này sẽ thay đổi cấu trúc bảng `accounts`:
- **tk_no** → **ma_khach_hang** (VARCHAR(20))
- **tk_co** → **ngay_sinh** (DATE)

## Cách chạy

### 1. Backup database (QUAN TRỌNG!)
Trước khi chạy migration, hãy backup database của bạn:
```bash
# PostgreSQL
pg_dump -U postgres -d pos > backup_before_migration.sql
```

### 2. Chạy migration script
```bash
cd Backend
python migrate_accounts.py
```

Script sẽ:
1. Kiểm tra cấu trúc hiện tại của bảng `accounts`
2. Thêm các cột mới (`ma_khach_hang`, `ngay_sinh`) nếu chưa có
3. Copy dữ liệu từ cột cũ sang cột mới:
   - `tk_no` → `ma_khach_hang` (copy trực tiếp)
   - `tk_co` → `ngay_sinh` (convert string sang date)
4. Xóa các cột cũ (`tk_no`, `tk_co`) sau khi đã copy xong

### 3. Xử lý dữ liệu ngày sinh
Script sẽ tự động convert các định dạng date phổ biến:
- `YYYY-MM-DD` (ví dụ: 1990-01-15)
- `DD/MM/YYYY` (ví dụ: 15/01/1990)
- `DD-MM-YYYY` (ví dụ: 15-01-1990)

Nếu có dữ liệu không convert được, bạn cần cập nhật thủ công.

## Lưu ý
- Script sẽ hỏi xác nhận trước khi chạy
- Nếu có lỗi, script sẽ rollback và không thay đổi database
- Sau khi migration, kiểm tra lại dữ liệu để đảm bảo đúng

## Rollback (nếu cần)
Nếu cần rollback, bạn có thể:
1. Restore từ backup: `psql -U postgres -d pos < backup_before_migration.sql`
2. Hoặc chạy SQL thủ công để đổi lại:
```sql
ALTER TABLE accounts ADD COLUMN tk_no VARCHAR(20);
ALTER TABLE accounts ADD COLUMN tk_co VARCHAR(20);
UPDATE accounts SET tk_no = ma_khach_hang WHERE ma_khach_hang IS NOT NULL;
UPDATE accounts SET tk_co = ngay_sinh::TEXT WHERE ngay_sinh IS NOT NULL;
ALTER TABLE accounts DROP COLUMN ma_khach_hang;
ALTER TABLE accounts DROP COLUMN ngay_sinh;
```

