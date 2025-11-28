"""
Database models for PhanMemKeToan application
"""
from sqlalchemy import Column, Integer, String, Float, Date, Boolean, Text, DateTime, func, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    """User model for authentication and authorization"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    name = Column(String(100))
    email = Column(String(120))
    phone = Column(String(20))
    position = Column(String(100))
    department = Column(String(100))
    status = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<User(username='{self.username}', name='{self.name}')>"


class Account(Base):
    """Account model for customer management"""
    __tablename__ = 'accounts'
    
    id = Column(Integer, primary_key=True)
    ten_tk = Column(String(100), nullable=False, index=True) # Tên khách hàng
    ma_khach_hang = Column(String(20))  # Mã khách hàng
    ngay_sinh = Column(Date)  # Ngày sinh khách hàng
    email = Column(String(120))
    so_dt = Column(String(20))
    dia_chi = Column(String(255))
    trang_thai = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<Account(ten_tk='{self.ten_tk}')>"


class GeneralDiary(Base):
    """General diary model for accounting entries"""
    __tablename__ = 'general_diary'
    
    id = Column(Integer, primary_key=True)
    ngay_nhap = Column(Date, nullable=False)
    so_hieu = Column(String(50), nullable=False)
    dien_giai = Column(String(255))
    so_luong_nhap = Column(Integer, default=0)
    so_luong_xuat = Column(Integer, default=0)
    so_tien = Column(Float, default=0.0)
    
    def __repr__(self):
        return f"<GeneralDiary(so_hieu='{self.so_hieu}', ngay='{self.ngay_nhap}')>"


class ProductGroup(Base):
    """Product group model for categorizing products"""
    __tablename__ = 'product_groups'
    
    id = Column(Integer, primary_key=True)
    ten_nhom = Column(String(100), nullable=False, unique=True)
    mo_ta = Column(String(255))
    
    def __repr__(self):
        return f"<ProductGroup(ten_nhom='{self.ten_nhom}')>"


class Product(Base):
    """Product model for inventory management"""
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    ma_sp = Column(String(20), unique=True, nullable=False, index=True)
    ten_sp = Column(String(100), nullable=False)
    nhom_sp = Column(String(100))
    so_luong = Column(Integer, default=0)
    gia_ban = Column(Float, default=0.0)
    gia_chung = Column(Float, default=0.0)
    gia_von = Column(Float, default=0.0)  # Cost price field
    don_vi = Column(String(50), default='cái')  # Unit field
    trang_thai = Column(String(50), default='active')
    mo_ta = Column(String(255))
    image_url = Column(String(255))  # Image URL field
    
    def __repr__(self):
        return f"<Product(ma_sp='{self.ma_sp}', ten_sp='{self.ten_sp}')>"


class Price(Base):
    """Independent price list model (separate from products)"""
    __tablename__ = 'prices'

    id = Column(Integer, primary_key=True)
    ma_sp = Column(String(20), nullable=False, index=True)
    ten_sp = Column(String(100), nullable=False)
    gia_chung = Column(Float, default=0.0)
    ghi_chu = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Price(ma_sp='{self.ma_sp}', ten_sp='{self.ten_sp}', gia_chung={self.gia_chung})>"

class Invoice(Base):
    """Invoice model for billing"""
    __tablename__ = 'invoices'
    
    id = Column(Integer, primary_key=True)
    so_hd = Column(String(50), unique=True, nullable=False, index=True)
    ngay_hd = Column(Date, nullable=False)
    nguoi_mua = Column(String(100), nullable=False)
    tong_tien = Column(Float, nullable=False)
    trang_thai = Column(String(50), default='pending')
    hinh_thuc_tt = Column(String(50))  # Hình thức thanh toán: Tiền mặt, MoMo, Banking
    
    # Relationship to invoice items
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Invoice(so_hd='{self.so_hd}')>"


class InvoiceItem(Base):
    """Invoice item model for invoice details"""
    __tablename__ = 'invoice_items'
    
    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey('invoices.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    product_code = Column(String(20), nullable=False)  # Store product code for reference
    product_name = Column(String(100), nullable=False)  # Store product name for reference
    so_luong = Column(Integer, nullable=False)
    don_gia = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    
    # Relationships
    invoice = relationship("Invoice", back_populates="items")
    product = relationship("Product")
    
    def __repr__(self):
        return f"<InvoiceItem(invoice_id={self.invoice_id}, product_code='{self.product_code}', so_luong={self.so_luong})>"


class Order(Base):
    """Order model for order management"""
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True)
    ma_don_hang = Column(String(50), unique=True, nullable=False, index=True)
    thong_tin_kh = Column(String(255))
    sp_banggia = Column(String(100))  # Mã sản phẩm hoặc mã bảng giá
    ngay_tao = Column(Date, nullable=False)
    so_luong = Column(Integer, default=1)
    tong_tien = Column(Float, default=0.0)
    ma_co_quan_thue = Column(String(50))
    # hinh_thuc_tt = Column(String(50))  # Removed - no longer used
    trang_thai = Column(String(50), default='pending')
    
    def __repr__(self):
        return f"<Order(ma_don_hang='{self.ma_don_hang}')>"


class OrderItem(Base):
    """Order item model for order details"""
    __tablename__ = 'order_items'
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    so_luong = Column(Integer, nullable=False)
    don_gia = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    
    def __repr__(self):
        return f"<OrderItem(order_id={self.order_id}, product_id={self.product_id})>"


class Warehouse(Base):
    """Warehouse model for inventory management"""
    __tablename__ = 'warehouses'
    
    id = Column(Integer, primary_key=True)
    ma_kho = Column(String(50), unique=True, nullable=False, index=True)
    ten_kho = Column(String(100), nullable=False)
    ma_sp = Column(String(20), unique=True, nullable=False, index=True)
    gia_nhap = Column(Float, default=0.0)
    so_luong = Column(Integer, default=0)
    dia_chi = Column(String(255))
    dien_thoai = Column(String(20))
    ghi_chu = Column(Text)
    trang_thai = Column(String(50), default='active')
    
    def __repr__(self):
        return f"<Warehouse(ma_kho='{self.ma_kho}', ten_kho='{self.ten_kho}')>"


class Area(Base):
    """Area model for managing geographical areas"""
    __tablename__ = 'areas'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, index=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    type = Column(String(50), nullable=False)  # city, district, ward, region, zone
    province = Column(String(100), nullable=False)
    district = Column(String(100))
    ward = Column(String(100))
    address = Column(Text)
    postal_code = Column(String(10))
    phone = Column(String(20))
    email = Column(String(120))
    manager = Column(String(100))
    description = Column(Text)
    status = Column(String(20), default='active', index=True)  # active, inactive, pending, suspended
    priority = Column(String(20), default='medium')  # low, medium, high, critical
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationship with shops
    shops = relationship("Shop", back_populates="area")
    
    def __repr__(self):
        return f"<Area(name='{self.name}', code='{self.code}')>"


class Shop(Base):
    """Shop model for managing shops/branches"""
    __tablename__ = 'shops'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, index=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    area_id = Column(Integer, ForeignKey('areas.id'), nullable=False)
    address = Column(Text, nullable=False)
    phone = Column(String(20))
    email = Column(String(120))
    manager = Column(String(100))
    description = Column(Text)
    status = Column(String(20), default='active', index=True)  # active, inactive, pending, suspended
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationship with area
    area = relationship("Area", back_populates="shops")
    
    def __repr__(self):
        return f"<Shop(name='{self.name}', code='{self.code}')>"


class DiscountCode(Base):
    __tablename__ = "discount_codes"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    discount_type = Column(String(20), nullable=False)  # 'percentage' or 'fixed'
    discount_value = Column(Float, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    max_uses = Column(Integer, default=None)  # None means unlimited
    used_count = Column(Integer, default=0)
    min_order_value = Column(Float, default=0.0)
    status = Column(String(20), default='active')  # 'active', 'expired', 'inactive'
    total_savings = Column(Float, default=0.0)  # Total amount saved by this code
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<DiscountCode(code='{self.code}', name='{self.name}', type='{self.discount_type}')>"


class Schedule(Base):
    """Schedule model for employee work schedules"""
    __tablename__ = 'schedules'
    
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    work_date = Column(Date, nullable=False, index=True)
    shift_type = Column(String(50), nullable=False)  # Ca 1, Ca 2, Ca 3, Ca sáng, Ca chiều, Ca tối
    notes = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationship
    employee = relationship("User")
    
    def __repr__(self):
        return f"<Schedule(employee_id={self.employee_id}, work_date='{self.work_date}', shift_type='{self.shift_type}')>"