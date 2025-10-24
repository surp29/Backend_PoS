"""
CRUD operations for PhanMemKeToan application
"""
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from . import models
from . import schemas_fastapi as schemas
import logging

logger = logging.getLogger(__name__)


# User CRUD
def get_user_by_username(db: Session, username: str):
    """Get user by username"""
    try:
        return db.query(models.User).filter(models.User.username == username).first()
    except SQLAlchemyError as e:
        logger.error(f"Error getting user by username: {e}")
        return None


def create_user(db: Session, user: schemas.UserCreate, hashed_password: str):
    """Create new user"""
    try:
        db_user = models.User(username=user.username, password=hashed_password)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except SQLAlchemyError as e:
        logger.error(f"Error creating user: {e}")
        db.rollback()
        raise


# Account CRUD
def get_accounts(db: Session):
    """Get all accounts"""
    try:
        return db.query(models.Account).all()
    except SQLAlchemyError as e:
        logger.error(f"Error getting accounts: {e}")
        return []


def create_account(db: Session, account: schemas.AccountCreate):
    """Create new account"""
    try:
        db_account = models.Account(**account.dict())
        db.add(db_account)
        db.commit()
        db.refresh(db_account)
        return db_account
    except SQLAlchemyError as e:
        logger.error(f"Error creating account: {e}")
        db.rollback()
        raise


# GeneralDiary CRUD
def get_general_diary(db: Session):
    """Get all general diary entries"""
    try:
        return db.query(models.GeneralDiary).all()
    except SQLAlchemyError as e:
        logger.error(f"Error getting general diary: {e}")
        return []


def create_general_diary(db: Session, gd: schemas.GeneralDiaryCreate):
    """Create new general diary entry"""
    try:
        db_gd = models.GeneralDiary(**gd.dict())
        db.add(db_gd)
        db.commit()
        db.refresh(db_gd)
        return db_gd
    except SQLAlchemyError as e:
        logger.error(f"Error creating general diary entry: {e}")
        db.rollback()
        raise


def get_general_diary_entry(db: Session, entry_id: int):
    """Get general diary entry by ID"""
    try:
        return db.query(models.GeneralDiary).filter(models.GeneralDiary.id == entry_id).first()
    except SQLAlchemyError as e:
        logger.error(f"Error getting general diary entry: {e}")
        return None


def update_general_diary(db: Session, entry_id: int, gd: schemas.GeneralDiaryCreate):
    """Update general diary entry"""
    try:
        db_gd = get_general_diary_entry(db, entry_id)
        if db_gd:
            for key, value in gd.dict().items():
                setattr(db_gd, key, value)
            db.commit()
            db.refresh(db_gd)
        return db_gd
    except SQLAlchemyError as e:
        logger.error(f"Error updating general diary entry: {e}")
        db.rollback()
        raise


def delete_general_diary(db: Session, entry_id: int):
    """Delete general diary entry"""
    try:
        db_gd = get_general_diary_entry(db, entry_id)
        if db_gd:
            db.delete(db_gd)
            db.commit()
        return db_gd
    except SQLAlchemyError as e:
        logger.error(f"Error deleting general diary entry: {e}")
        db.rollback()
        raise


# ProductGroup CRUD
def get_product_groups(db: Session):
    """Get all product groups"""
    try:
        return db.query(models.ProductGroup).all()
    except SQLAlchemyError as e:
        logger.error(f"Error getting product groups: {e}")
        return []


def create_product_group(db: Session, group: schemas.ProductGroupCreate):
    """Create new product group"""
    try:
        db_group = models.ProductGroup(**group.dict())
        db.add(db_group)
        db.commit()
        db.refresh(db_group)
        return db_group
    except SQLAlchemyError as e:
        logger.error(f"Error creating product group: {e}")
        db.rollback()
        raise


# Product CRUD
def get_products(db: Session):
    """Get all products"""
    try:
        return db.query(models.Product).all()
    except SQLAlchemyError as e:
        logger.error(f"Error getting products: {e}")
        return []


def create_product(db: Session, product: schemas.ProductCreate):
    """Create new product"""
    try:
        db_product = models.Product(**product.dict())
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        return db_product
    except SQLAlchemyError as e:
        logger.error(f"Error creating product: {e}")
        db.rollback()
        raise


def get_product(db: Session, product_id: int):
    """Get product by ID"""
    try:
        return db.query(models.Product).filter(models.Product.id == product_id).first()
    except SQLAlchemyError as e:
        logger.error(f"Error getting product: {e}")
        return None


def update_product(db: Session, product_id: int, product: schemas.ProductCreate):
    """Update product"""
    try:
        db_product = get_product(db, product_id)
        if db_product:
            for key, value in product.dict().items():
                setattr(db_product, key, value)
            db.commit()
            db.refresh(db_product)
        return db_product
    except SQLAlchemyError as e:
        logger.error(f"Error updating product: {e}")
        db.rollback()
        raise


def delete_product(db: Session, product_id: int):
    """Delete product"""
    try:
        db_product = get_product(db, product_id)
        if db_product:
            db.delete(db_product)
            db.commit()
        return db_product
    except SQLAlchemyError as e:
        logger.error(f"Error deleting product: {e}")
        db.rollback()
        raise


# Price CRUD
def get_prices(db: Session):
    """Get all prices"""
    try:
        return db.query(models.Price).all()
    except SQLAlchemyError as e:
        logger.error(f"Error getting prices: {e}")
        return []


def create_price(db: Session, price: schemas.PriceCreate):
    """Create new price"""
    try:
        db_price = models.Price(**price.dict())
        db.add(db_price)
        db.commit()
        db.refresh(db_price)
        return db_price
    except SQLAlchemyError as e:
        logger.error(f"Error creating price: {e}")
        db.rollback()
        raise


# Order CRUD
def get_orders(db: Session):
    """Get all orders"""
    try:
        return db.query(models.Order).all()
    except SQLAlchemyError as e:
        logger.error(f"Error getting orders: {e}")
        return []


def create_order(db: Session, order: schemas.OrderCreate):
    """Create new order"""
    try:
        db_order = models.Order(**order.dict())
        db.add(db_order)
        db.commit()
        db.refresh(db_order)
        return db_order
    except SQLAlchemyError as e:
        logger.error(f"Error creating order: {e}")
        db.rollback()
        raise


# OrderItem CRUD
def get_order_items(db: Session):
    """Get all order items"""
    try:
        return db.query(models.OrderItem).all()
    except SQLAlchemyError as e:
        logger.error(f"Error getting order items: {e}")
        return []


def create_order_item(db: Session, item: schemas.OrderItemCreate):
    """Create new order item"""
    try:
        db_item = models.OrderItem(**item.dict())
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        return db_item
    except SQLAlchemyError as e:
        logger.error(f"Error creating order item: {e}")
        db.rollback()
        raise


# Invoice CRUD
def get_invoices(db: Session):
    """Get all invoices"""
    try:
        return db.query(models.Invoice).all()
    except SQLAlchemyError as e:
        logger.error(f"Error getting invoices: {e}")
        return []


def create_invoice(db: Session, invoice: schemas.InvoiceCreate):
    """Create new invoice"""
    try:
        db_invoice = models.Invoice(**invoice.dict())
        db.add(db_invoice)
        db.commit()
        db.refresh(db_invoice)
        return db_invoice
    except SQLAlchemyError as e:
        logger.error(f"Error creating invoice: {e}")
        db.rollback()
        raise


# Warehouse CRUD
def get_warehouses(db: Session):
    """Get all warehouses"""
    try:
        return db.query(models.Warehouse).all()
    except SQLAlchemyError as e:
        logger.error(f"Error getting warehouses: {e}")
        return []


def create_warehouse(db: Session, warehouse: schemas.WarehouseCreate):
    """Create new warehouse"""
    try:
        db_warehouse = models.Warehouse(**warehouse.dict())
        db.add(db_warehouse)
        db.commit()
        db.refresh(db_warehouse)
        return db_warehouse
    except SQLAlchemyError as e:
        logger.error(f"Error creating warehouse: {e}")
        db.rollback()
        raise 


# Area CRUD
def get_area(db: Session, area_id: int):
    """Get area by ID"""
    try:
        return db.query(models.Area).filter(models.Area.id == area_id).first()
    except SQLAlchemyError as e:
        logger.error(f"Error getting area: {e}")
        return None


def get_areas(db: Session, skip: int = 0, limit: int = 100):
    """Get all areas"""
    try:
        return db.query(models.Area).offset(skip).limit(limit).all()
    except SQLAlchemyError as e:
        logger.error(f"Error getting areas: {e}")
        return []


def create_area(db: Session, area: schemas.AreaCreate):
    """Create new area"""
    try:
        db_area = models.Area(**area.dict())
        db.add(db_area)
        db.commit()
        db.refresh(db_area)
        return db_area
    except SQLAlchemyError as e:
        logger.error(f"Error creating area: {e}")
        db.rollback()
        raise


def update_area(db: Session, area_id: int, area: schemas.AreaUpdate):
    """Update area"""
    try:
        db_area = db.query(models.Area).filter(models.Area.id == area_id).first()
        if not db_area:
            return None
        
        update_data = area.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_area, field, value)
        
        db.commit()
        db.refresh(db_area)
        return db_area
    except SQLAlchemyError as e:
        logger.error(f"Error updating area: {e}")
        db.rollback()
        raise


def delete_area(db: Session, area_id: int):
    """Delete area"""
    try:
        db_area = db.query(models.Area).filter(models.Area.id == area_id).first()
        if db_area:
            db.delete(db_area)
            db.commit()
        return True
    except SQLAlchemyError as e:
        logger.error(f"Error deleting area: {e}")
        db.rollback()
        raise


# Shop CRUD
def get_shop(db: Session, shop_id: int):
    """Get shop by ID"""
    try:
        return db.query(models.Shop).filter(models.Shop.id == shop_id).first()
    except SQLAlchemyError as e:
        logger.error(f"Error getting shop: {e}")
        return None


def get_shops(db: Session, skip: int = 0, limit: int = 100):
    """Get all shops"""
    try:
        return db.query(models.Shop).offset(skip).limit(limit).all()
    except SQLAlchemyError as e:
        logger.error(f"Error getting shops: {e}")
        return []


def create_shop(db: Session, shop: schemas.ShopCreate):
    """Create new shop"""
    try:
        db_shop = models.Shop(**shop.dict())
        db.add(db_shop)
        db.commit()
        db.refresh(db_shop)
        return db_shop
    except SQLAlchemyError as e:
        logger.error(f"Error creating shop: {e}")
        db.rollback()
        raise


def update_shop(db: Session, shop_id: int, shop: schemas.ShopUpdate):
    """Update shop"""
    try:
        db_shop = db.query(models.Shop).filter(models.Shop.id == shop_id).first()
        if not db_shop:
            return None
        
        update_data = shop.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_shop, field, value)
        
        db.commit()
        db.refresh(db_shop)
        return db_shop
    except SQLAlchemyError as e:
        logger.error(f"Error updating shop: {e}")
        db.rollback()
        raise


def delete_shop(db: Session, shop_id: int):
    """Delete shop"""
    try:
        db_shop = db.query(models.Shop).filter(models.Shop.id == shop_id).first()
        if db_shop:
            db.delete(db_shop)
            db.commit()
        return True
    except SQLAlchemyError as e:
        logger.error(f"Error deleting shop: {e}")
        db.rollback()
        raise