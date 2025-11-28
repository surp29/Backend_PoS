# Hướng dẫn tạo dữ liệu mẫu

## Mục đích
Script `create_sample_data.py` được tạo để:
- Xóa tất cả dữ liệu hiện có (trừ tài khoản admin)
- Tạo dữ liệu mẫu để test các chức năng của hệ thống

## Cách sử dụng

### 1. Chạy script
```bash
cd Backend
python create_sample_data.py
```

### 2. Xác nhận
Script sẽ hỏi xác nhận trước khi xóa dữ liệu:
```
⚠️  Bạn có chắc muốn xóa tất cả dữ liệu và tạo lại? (yes/no):
```
Nhập `yes` để tiếp tục.

### 3. Dữ liệu được tạo

#### Nhóm sản phẩm (3)
- NHOM001: Điện tử
- NHOM002: Thực phẩm
- NHOM003: Quần áo

#### Sản phẩm (5)
- SP001: Laptop Dell - 15,000,000 VNĐ
- SP002: iPhone 15 - 25,000,000 VNĐ
- SP003: Bánh mì - 15,000 VNĐ
- SP004: Áo thun - 200,000 VNĐ
- SP005: Quần jean - 500,000 VNĐ

#### Khu vực (2)
- Hồ Chí Minh (HCM)
- Hà Nội (HN)

#### Shop (2)
- Shop chính tại HCM
- Shop phụ tại HN

#### Khách hàng (3)
- Nguyễn Văn A (KH-HCM01)
- Trần Thị B (KH-HCM02)
- Lê Văn C (KH-HN01)

#### Đơn hàng (3)
- DH001: Hoàn thành (Nguyễn Văn A)
- DH002: Hoàn thành (Trần Thị B)
- DH003: Đang xử lý (Lê Văn C)

#### Hóa đơn (3)
- HD001: Đã thanh toán (Tiền mặt)
- HD002: Đã thanh toán (MoMo)
- HD003: Chưa thanh toán (Banking)

#### Mã giảm giá (2)
- GIAM10: Giảm 10%
- GIAM50K: Giảm 50,000 VNĐ

## Lưu ý
- Tài khoản admin (username: admin, password: admin123) sẽ được giữ lại
- Tất cả dữ liệu khác sẽ bị xóa và tạo lại
- Script có thể chạy nhiều lần để reset dữ liệu

