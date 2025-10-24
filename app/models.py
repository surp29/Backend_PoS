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
    ten_tk = Column(String(100), nullable=False, index=True)
    tk_no = Column(String(20))
    tk_co = Column(String(20))
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
    tk_no = Column(String(20))
    tk_co = Column(String(20))
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
    
    def __repr__(self):
        return f"<Product(ma_sp='{self.ma_sp}', ten_sp='{self.ten_sp}')>"


class Price(Base):
    """Price model for product pricing"""
    __tablename__ = 'prices'
    
    id = Column(Integer, primary_key=True)
    ma_sp = Column(String(20), unique=True, nullable=False, index=True)
    ten_sp = Column(String(100), nullable=False)
    loai_sp = Column(String(50), default='Hành động')
    gia_von = Column(Float, nullable=False)
    gia_chung = Column(Float, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Price(ma_sp='{self.ma_sp}', ten_sp='{self.ten_sp}')>"


class Order(Base):
    """Order model for order management"""
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True)
    ma_don_hang = Column(String(50), unique=True, nullable=False, index=True)
    thong_tin_kh = Column(String(255))
    sp_banggia = Column(String(100))
    ngay_tao = Column(Date, nullable=False)
    ma_co_quan_thue = Column(String(50))
    so_luong = Column(Integer, default=1)
    tong_tien = Column(Float, default=0.0)
    hinh_thuc_tt = Column(String(50))
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


class Invoice(Base):
    """Invoice model for billing"""
    __tablename__ = 'invoices'
    
    id = Column(Integer, primary_key=True)
    so_hd = Column(String(50), unique=True, nullable=False, index=True)
    ngay_hd = Column(Date, nullable=False)
    nguoi_mua = Column(String(100), nullable=False)
    tong_tien = Column(Float, nullable=False)
    loai_hd = Column(String(50), nullable=False)
    trang_thai = Column(String(50), default='pending')
    
    def __repr__(self):
        return f"<Invoice(so_hd='{self.so_hd}')>"


class Warehouse(Base):
    """Warehouse model for inventory management"""
    __tablename__ = 'warehouses'
    
    id = Column(Integer, primary_key=True)
    ma_kho = Column(String(50), unique=True, nullable=False, index=True)
    ten_kho = Column(String(100), nullable=False)
    dia_chi = Column(String(255))
    so_luong_sp = Column(Integer, default=0)
    trang_thai = Column(String(50), default='active')
    dien_thoai = Column(String(20))
    nhom_san_pham = Column(String(100))
    mo_ta = Column(String(255))
    
    def __repr__(self):
        return f"<Warehouse(ma_kho='{self.ma_kho}', ten_kho='{self.ten_kho}')>"


class Report(Base):
    """Report model for financial reporting"""
    __tablename__ = 'reports'
    
    id = Column(Integer, primary_key=True)
    ten_bao_cao = Column(String(255), nullable=False)
    loai_bao_cao = Column(String(100), nullable=False)
    tu_ngay = Column(Date, nullable=False)
    den_ngay = Column(Date, nullable=False)
    du_lieu = Column(Text)
    tong_doanh_thu = Column(Float, default=0.0)
    tong_so_luong_ban = Column(Integer, default=0)
    tong_so_luong_con_lai = Column(Integer, default=0)
    ngay_tao = Column(DateTime, default=func.now())
    trang_thai = Column(String(50), default='active')
    
    def __repr__(self):
        return f"<Report(ten_bao_cao='{self.ten_bao_cao}', loai='{self.loai_bao_cao}')>"


class Debt(Base):
    """Debt model for debt tracking"""
    __tablename__ = 'debts'
    
    id = Column(Integer, primary_key=True)
    customer_name = Column(String(255), nullable=False, index=True)
    total_debt = Column(Numeric(15, 2), default=0.00)
    paid_amount = Column(Numeric(15, 2), default=0.00)
    remaining_debt = Column(Numeric(15, 2), default=0.00)
    status = Column(String(50), default='Còn nợ', index=True)
    last_payment_date = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Debt(customer='{self.customer_name}', remaining='{self.remaining_debt}')>"


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