from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from decimal import Decimal

# User schemas for authentication
class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    position: Optional[str] = None
    department: Optional[str] = None
    status: bool

    class Config:
        from_attributes = True


class ProductGroupOut(BaseModel):
    id: int
    ten_nhom: str
    mo_ta: Optional[str] = None

    class Config:
        from_attributes = True


class ProductOut(BaseModel):
    id: int
    ma_sp: Optional[str] = None
    ten_sp: Optional[str] = None
    nhom_sp: Optional[str] = None  # Đổi từ nhom_id thành nhom_sp
    so_luong: Optional[int] = 0
    gia_ban: Optional[float] = 0
    gia_chung: Optional[float] = None  # Thêm giá chung
    gia_von: Optional[float] = 0.0  # Cost price field
    don_vi: Optional[str] = 'cái'  # Unit field
    trang_thai: Optional[str] = None
    mo_ta: Optional[str] = None

    class Config:
        from_attributes = True


class PriceOut(BaseModel):
    id: int
    ma_sp: str
    ten_sp: str
    loai_sp: str
    gia_von: float
    gia_chung: float
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class WarehouseOut(BaseModel):
    id: int
    ma_kho: Optional[str]
    ten_kho: Optional[str]
    dia_chi: Optional[str]
    so_luong_sp: Optional[int]
    trang_thai: Optional[str]
    dien_thoai: Optional[str]
    nhom_san_pham: Optional[str]
    mo_ta: Optional[str]

    class Config:
        from_attributes = True


class ProductGroupUpdate(BaseModel):
    mo_ta: Optional[str] = None


class PriceCreate(BaseModel):
    ma_sp: str
    ten_sp: str
    loai_sp: Optional[str] = 'Hành động'
    gia_von: float
    gia_chung: float


class PriceUpdate(BaseModel):
    ma_sp: Optional[str] = None
    ten_sp: Optional[str] = None
    loai_sp: Optional[str] = None
    gia_von: Optional[float] = None
    gia_chung: Optional[float] = None


class ProductCreate(BaseModel):
    nhom_sp: Optional[str] = None
    ma_sp: Optional[str] = None
    ten_sp: Optional[str] = None
    so_luong: Optional[int] = 0
    gia_ban: Optional[float] = 0
    gia_chung: Optional[float] = None  # Thêm giá chung
    gia_von: Optional[float] = 0.0  # Cost price field
    don_vi: Optional[str] = 'cái'  # Unit field
    trang_thai: Optional[str] = None
    mo_ta: Optional[str] = None
    
    # Frontend compatibility fields
    code: Optional[str] = None  # Alias for ma_sp
    name: Optional[str] = None  # Alias for ten_sp
    group: Optional[str] = None  # Alias for nhom_sp
    cost_price: Optional[float] = None  # Alias for gia_von
    price: Optional[float] = None  # Alias for gia_ban
    quantity: Optional[int] = None  # Alias for so_luong
    unit: Optional[str] = None  # Alias for don_vi
    description: Optional[str] = None  # Alias for mo_ta


class ProductUpdate(BaseModel):
    nhom_sp: Optional[str] = None
    ma_sp: Optional[str] = None
    ten_sp: Optional[str] = None
    so_luong: Optional[int] = None
    gia_ban: Optional[float] = None
    gia_chung: Optional[float] = None
    gia_von: Optional[float] = None  # Cost price field
    don_vi: Optional[str] = None  # Unit field
    trang_thai: Optional[str] = None
    mo_ta: Optional[str] = None
    
    # Frontend compatibility fields
    code: Optional[str] = None  # Alias for ma_sp
    name: Optional[str] = None  # Alias for ten_sp
    group: Optional[str] = None  # Alias for nhom_sp
    cost_price: Optional[float] = None  # Alias for gia_von
    price: Optional[float] = None  # Alias for gia_ban
    quantity: Optional[int] = None  # Alias for so_luong
    unit: Optional[str] = None  # Alias for don_vi
    description: Optional[str] = None  # Alias for mo_ta


class WarehouseCreate(BaseModel):
    ma_kho: str
    ten_kho: str
    dia_chi: str
    dien_thoai: Optional[str] = None
    so_luong_sp: Optional[int] = 0
    trang_thai: Optional[str] = 'Hoạt động'
    nhom_san_pham: Optional[str] = None
    mo_ta: Optional[str] = None


# Users
class UserOut(BaseModel):
    id: int
    username: str
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    position: Optional[str] = None
    department: Optional[str] = None
    status: Optional[bool] = True

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    username: str
    password: str
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    position: Optional[str] = None
    department: Optional[str] = None
    status: Optional[bool] = True


class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    position: Optional[str] = None
    department: Optional[str] = None
    status: Optional[bool] = None


# Accounts
class AccountOut(BaseModel):
    id: int
    ten_tk: Optional[str]
    tk_no: Optional[str]
    tk_co: Optional[str]
    email: Optional[str]
    so_dt: Optional[str]
    dia_chi: Optional[str]
    trang_thai: Optional[bool]

    class Config:
        from_attributes = True


class AccountCreate(BaseModel):
    ten_tk: str
    tk_no: Optional[str] = None
    tk_co: Optional[str] = None
    email: Optional[str] = None
    so_dt: Optional[str] = None
    dia_chi: Optional[str] = None
    trang_thai: Optional[bool] = True


class AccountUpdate(BaseModel):
    ten_tk: Optional[str] = None
    tk_no: Optional[str] = None
    tk_co: Optional[str] = None
    email: Optional[str] = None
    so_dt: Optional[str] = None
    dia_chi: Optional[str] = None
    trang_thai: Optional[bool] = None


# Orders
class OrderOut(BaseModel):
    id: int
    ma_don_hang: Optional[str]
    thong_tin_kh: Optional[str]
    sp_banggia: Optional[str]
    ngay_tao: Optional[date]
    ma_co_quan_thue: Optional[str]
    so_luong: Optional[int]
    tong_tien: Optional[float]
    hinh_thuc_tt: Optional[str]
    trang_thai: Optional[str]

    class Config:
        from_attributes = True


class OrderCreate(BaseModel):
    ma_don_hang: str
    thong_tin_kh: str
    sp_banggia: Optional[str] = None
    ngay_tao: Optional[date] = None
    ma_co_quan_thue: Optional[str] = None
    so_luong: Optional[int] = 1
    tong_tien: Optional[float] = 0
    hinh_thuc_tt: Optional[str] = None
    trang_thai: Optional[str] = None


class OrderUpdate(BaseModel):
    ma_don_hang: Optional[str] = None
    thong_tin_kh: Optional[str] = None
    sp_banggia: Optional[str] = None
    ngay_tao: Optional[date] = None
    ma_co_quan_thue: Optional[str] = None
    so_luong: Optional[int] = None
    tong_tien: Optional[float] = None
    hinh_thuc_tt: Optional[str] = None
    trang_thai: Optional[str] = None


class OrderItemCreate(BaseModel):
    order_id: int
    product_id: int
    so_luong: int
    don_gia: Optional[float] = 0
    total_price: Optional[float] = 0


# Invoices
class InvoiceOut(BaseModel):
    id: int
    so_hd: Optional[str]
    ngay_hd: Optional[date]
    nguoi_mua: Optional[str]
    tong_tien: Optional[float]
    loai_hd: Optional[str]
    trang_thai: Optional[str]

    class Config:
        from_attributes = True


class InvoiceCreate(BaseModel):
    so_hd: str
    ngay_hd: date
    nguoi_mua: str
    tong_tien: float
    loai_hd: str
    trang_thai: Optional[str] = 'Đã thanh toán'


class InvoiceUpdate(BaseModel):
    so_hd: Optional[str] = None
    ngay_hd: Optional[date] = None
    nguoi_mua: Optional[str] = None
    tong_tien: Optional[float] = None
    loai_hd: Optional[str] = None
    trang_thai: Optional[str] = None


# Reports
class ReportOut(BaseModel):
    id: int
    ten_bao_cao: Optional[str] = None
    loai_bao_cao: Optional[str] = None
    tu_ngay: Optional[date] = None
    den_ngay: Optional[date] = None
    du_lieu: Optional[str] = None
    tong_doanh_thu: Optional[float] = 0
    tong_so_luong_ban: Optional[int] = 0
    tong_so_luong_con_lai: Optional[int] = 0
    ngay_tao: Optional[datetime] = None
    trang_thai: Optional[str] = 'active'

    class Config:
        from_attributes = True


class ReportCreate(BaseModel):
    ten_bao_cao: str
    loai_bao_cao: str
    tu_ngay: date
    den_ngay: date
    du_lieu: Optional[str] = None
    tong_doanh_thu: Optional[float] = 0
    tong_so_luong_ban: Optional[int] = 0
    tong_so_luong_con_lai: Optional[int] = 0
    trang_thai: Optional[str] = 'active'


class ReportUpdate(BaseModel):
    ten_bao_cao: Optional[str] = None
    loai_bao_cao: Optional[str] = None
    tu_ngay: Optional[date] = None
    den_ngay: Optional[date] = None
    du_lieu: Optional[str] = None
    tong_doanh_thu: Optional[float] = None
    tong_so_luong_ban: Optional[int] = None
    tong_so_luong_con_lai: Optional[int] = None
    trang_thai: Optional[str] = None


# Debts
class DebtOut(BaseModel):
    id: int
    customer_name: str
    total_debt: Decimal
    paid_amount: Decimal
    remaining_debt: Decimal
    status: str
    last_payment_date: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DebtCreate(BaseModel):
    customer_name: str
    total_debt: Decimal = Decimal('0.00')
    paid_amount: Decimal = Decimal('0.00')
    remaining_debt: Decimal = Decimal('0.00')
    status: Optional[str] = 'Còn nợ'


class DebtUpdate(BaseModel):
    total_debt: Optional[Decimal] = None
    paid_amount: Optional[Decimal] = None
    remaining_debt: Optional[Decimal] = None
    status: Optional[str] = None
    last_payment_date: Optional[datetime] = None





class GeneralDiaryCreate(BaseModel):
    ngay_nhap: Optional[date] = None
    so_hieu: Optional[str] = None
    dien_giai: Optional[str] = None
    tk_no: Optional[str] = None
    tk_co: Optional[str] = None
    so_luong_nhap: Optional[int] = 0
    so_luong_xuat: Optional[int] = 0
    so_tien: Optional[float] = 0

    class Config:
        from_attributes = True


class ProductGroupCreate(BaseModel):
    ten_nhom: str
    mo_ta: Optional[str] = None

    class Config:
        from_attributes = True


# Area schemas
class AreaBase(BaseModel):
    name: str
    code: str
    type: str
    province: str
    district: Optional[str] = None
    ward: Optional[str] = None
    address: Optional[str] = None
    postal_code: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    manager: Optional[str] = None
    description: Optional[str] = None
    status: str = "active"
    priority: str = "medium"

class AreaCreate(AreaBase):
    pass

class AreaUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    type: Optional[str] = None
    province: Optional[str] = None
    district: Optional[str] = None
    ward: Optional[str] = None
    address: Optional[str] = None
    postal_code: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    manager: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None

class AreaOut(AreaBase):
    id: int
    created_at: datetime
    updated_at: datetime
    shop_count: Optional[int] = 0

    class Config:
        from_attributes = True


# Shop schemas
class ShopBase(BaseModel):
    name: str
    code: str
    area_id: int
    address: str
    phone: Optional[str] = None
    email: Optional[str] = None
    manager: Optional[str] = None
    description: Optional[str] = None
    status: str = "active"

class ShopCreate(ShopBase):
    pass

class ShopUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    area_id: Optional[int] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    manager: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

class ShopOut(ShopBase):
    id: int
    created_at: datetime
    updated_at: datetime
    area_name: Optional[str] = None

    class Config:
        from_attributes = True
