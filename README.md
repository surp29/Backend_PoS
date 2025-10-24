# PhanMemKeToan Backend

## 🚀 FastAPI Backend Server

Backend server được xây dựng với FastAPI, cung cấp RESTful API cho hệ thống quản lý bán hàng PhanMemKeToan.

## 📋 Tính năng

### 🔐 Authentication & Authorization
- JWT-based authentication
- Role-based access control
- Secure password hashing
- Session management

### 📊 Core APIs
- **Products API**: Quản lý sản phẩm, nhóm sản phẩm
- **Orders API**: Quản lý đơn hàng
- **Invoices API**: Quản lý hóa đơn
- **Prices API**: Quản lý giá cả
- **Warehouse API**: Quản lý kho hàng
- **General Diary API**: Nhật ký chung
- **Reports API**: Báo cáo thống kê
- **Areas API**: Quản lý khu vực
- **Shops API**: Quản lý shop
- **Accounts API**: Quản lý tài khoản

## 🛠️ Cài đặt

### Yêu cầu
- Python 3.8+
- PostgreSQL 12+
- pip

### Cài đặt dependencies
```bash
pip install -r requirements.txt
```

### Cấu hình database
```bash
python setup_database.py
```

### Chạy server
```bash
python main.py
```

## 🌐 API Endpoints

### Authentication
```
POST /api/auth/login          # Đăng nhập
POST /api/auth/logout         # Đăng xuất
GET  /api/auth/me             # Thông tin user hiện tại
```

### Products
```
GET    /api/products/         # Lấy danh sách sản phẩm
POST   /api/products/         # Tạo sản phẩm mới
GET    /api/products/{id}     # Lấy chi tiết sản phẩm
PUT    /api/products/{id}     # Cập nhật sản phẩm
DELETE /api/products/{id}     # Xóa sản phẩm
```

### Orders
```
GET    /api/orders/           # Lấy danh sách đơn hàng
POST   /api/orders/           # Tạo đơn hàng mới
GET    /api/orders/{id}       # Lấy chi tiết đơn hàng
PUT    /api/orders/{id}       # Cập nhật đơn hàng
DELETE /api/orders/{id}       # Xóa đơn hàng
```

### Invoices
```
GET    /api/invoices/         # Lấy danh sách hóa đơn
POST   /api/invoices/         # Tạo hóa đơn mới
GET    /api/invoices/{id}     # Lấy chi tiết hóa đơn
PUT    /api/invoices/{id}     # Cập nhật hóa đơn
DELETE /api/invoices/{id}     # Xóa hóa đơn
```

### Prices
```
GET    /api/prices/           # Lấy danh sách bảng giá
POST   /api/prices/           # Tạo bảng giá mới
GET    /api/prices/{id}       # Lấy chi tiết bảng giá
PUT    /api/prices/{id}       # Cập nhật bảng giá
DELETE /api/prices/{id}       # Xóa bảng giá
```

### Warehouse
```
GET    /api/warehouses/       # Lấy danh sách kho hàng
POST   /api/warehouses/       # Tạo kho hàng mới
GET    /api/warehouses/{id}   # Lấy chi tiết kho hàng
PUT    /api/warehouses/{id}  # Cập nhật kho hàng
DELETE /api/warehouses/{id}  # Xóa kho hàng
```

### General Diary
```
GET    /api/general-diary/    # Lấy danh sách nhật ký
POST   /api/general-diary/    # Tạo nhật ký mới
GET    /api/general-diary/{id} # Lấy chi tiết nhật ký
PUT    /api/general-diary/{id} # Cập nhật nhật ký
DELETE /api/general-diary/{id} # Xóa nhật ký
```

### Reports
```
GET    /api/reports/          # Lấy báo cáo thống kê
GET    /api/reports/sales     # Báo cáo doanh thu
GET    /api/reports/products  # Báo cáo sản phẩm
```

### Areas
```
GET    /api/areas/            # Lấy danh sách khu vực
POST   /api/areas/            # Tạo khu vực mới
GET    /api/areas/{id}        # Lấy chi tiết khu vực
PUT    /api/areas/{id}        # Cập nhật khu vực
DELETE /api/areas/{id}        # Xóa khu vực
```

### Shops
```
GET    /api/shops/            # Lấy danh sách shop
POST   /api/shops/            # Tạo shop mới
GET    /api/shops/{id}        # Lấy chi tiết shop
PUT    /api/shops/{id}        # Cập nhật shop
DELETE /api/shops/{id}        # Xóa shop
```

### Accounts
```
GET    /api/accounts/         # Lấy danh sách tài khoản
POST   /api/accounts/         # Tạo tài khoản mới
GET    /api/accounts/{id}     # Lấy chi tiết tài khoản
PUT    /api/accounts/{id}     # Cập nhật tài khoản
DELETE /api/accounts/{id}     # Xóa tài khoản
```

## 🔧 Cấu hình

### Environment Variables
Tạo file `.env`:
```env
DATABASE_URL=postgresql://username:password@localhost:5432/pos
SECRET_KEY=your-secret-key-here
DEBUG=True
HOST=0.0.0.0
PORT=5001
```

### Database Configuration
```python
# app/config.py
DATABASE_URL = "postgresql://username:password@localhost:5432/pos"
SECRET_KEY = "your-secret-key"
DEBUG = True
```

## 📊 Database Schema

### Tables
- **users**: Thông tin người dùng
- **products**: Sản phẩm
- **product_groups**: Nhóm sản phẩm
- **orders**: Đơn hàng
- **invoices**: Hóa đơn
- **prices**: Bảng giá
- **warehouses**: Kho hàng
- **general_diary**: Nhật ký chung
- **areas**: Khu vực
- **shops**: Shop
- **accounts**: Tài khoản

## 🧪 Testing

### Unit Tests
```bash
python -m pytest tests/
```

### API Tests
```bash
python -m pytest tests/api/
```

### Coverage Report
```bash
python -m pytest --cov=app tests/
```

## 📈 Performance

### Optimization
- Database connection pooling
- Query optimization
- Caching strategies
- Async operations

### Monitoring
- Request/response logging
- Performance metrics
- Error tracking
- Health checks

## 🔒 Security

### Authentication
- JWT tokens với expiration
- Password hashing với bcrypt
- Session management

### Authorization
- Role-based access control
- Permission-based endpoints
- API key validation

### Data Protection
- Input validation với Pydantic
- SQL injection prevention
- XSS protection
- CSRF protection

## 📚 API Documentation

### Swagger UI
Truy cập: http://localhost:5001/docs

### ReDoc
Truy cập: http://localhost:5001/redoc

### OpenAPI Schema
Truy cập: http://localhost:5001/openapi.json

## 🚀 Deployment

### Development
```bash
python main.py
```

### Production
```bash
uvicorn app.main:app --host 0.0.0.0 --port 5001
```

### Docker
```bash
docker build -t phanmemketoan-backend .
docker run -p 5001:5001 phanmemketoan-backend
```

## 📝 Logging

### Log Levels
- **DEBUG**: Chi tiết debug
- **INFO**: Thông tin chung
- **WARNING**: Cảnh báo
- **ERROR**: Lỗi
- **CRITICAL**: Lỗi nghiêm trọng

### Log Format
```
[2024-01-01 12:00:00] INFO: User login successful
[2024-01-01 12:00:01] ERROR: Database connection failed
```

## 🔧 Troubleshooting

### Common Issues
1. **Database Connection Error**
   - Kiểm tra PostgreSQL service
   - Verify connection string
   - Check firewall settings

2. **Authentication Error**
   - Verify JWT secret key
   - Check token expiration
   - Validate user credentials

3. **API Error**
   - Check request format
   - Verify required fields
   - Check permissions

## 📞 Support

- **Documentation**: [API Docs](http://localhost:5001/docs)
- **Issues**: [GitHub Issues](https://github.com/phanmemketoan/issues)
- **Email**: support@phanmemketoan.com

---

**PhanMemKeToan Backend** - Professional FastAPI Server