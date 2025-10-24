from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from ..database import get_db
from ..models import Shop, Area
from ..schemas_fastapi import ShopCreate, ShopUpdate, ShopOut
from ..crud import get_shop, get_shops, create_shop, update_shop, delete_shop

router = APIRouter()

@router.get("/", response_model=List[ShopOut])
def read_shops(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    area_filter: Optional[int] = None,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all shops with optional filtering"""
    query = db.query(Shop)
    
    # Apply filters
    if search:
        query = query.filter(
            Shop.name.ilike(f"%{search}%") |
            Shop.code.ilike(f"%{search}%") |
            Shop.address.ilike(f"%{search}%") |
            Shop.manager.ilike(f"%{search}%")
        )
    
    if area_filter:
        query = query.filter(Shop.area_id == area_filter)
    
    if status_filter:
        query = query.filter(Shop.status == status_filter)
    
    # Get shops with area name
    shops = query.offset(skip).limit(limit).all()
    
    # Add area name to each shop
    result = []
    for shop in shops:
        area = db.query(Area).filter(Area.id == shop.area_id).first()
        shop_dict = {
            "id": shop.id,
            "name": shop.name,
            "code": shop.code,
            "area_id": shop.area_id,
            "address": shop.address,
            "phone": shop.phone,
            "email": shop.email,
            "manager": shop.manager,
            "description": shop.description,
            "status": shop.status,
            "created_at": shop.created_at,
            "updated_at": shop.updated_at,
            "area_name": area.name if area else None
        }
        result.append(shop_dict)
    
    return result

@router.get("/{shop_id}", response_model=ShopOut)
def read_shop(shop_id: int, db: Session = Depends(get_db)):
    """Get a specific shop by ID"""
    shop = get_shop(db, shop_id=shop_id)
    if shop is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shop not found"
        )
    
    # Add area name
    area = db.query(Area).filter(Area.id == shop.area_id).first()
    shop_dict = {
        "id": shop.id,
        "name": shop.name,
        "code": shop.code,
        "area_id": shop.area_id,
        "address": shop.address,
        "phone": shop.phone,
        "email": shop.email,
        "manager": shop.manager,
        "description": shop.description,
        "status": shop.status,
        "created_at": shop.created_at,
        "updated_at": shop.updated_at,
        "area_name": area.name if area else None
    }
    
    return shop_dict

@router.post("/", response_model=ShopOut)
def create_new_shop(shop: ShopCreate, db: Session = Depends(get_db)):
    """Create a new shop"""
    # Check if shop code already exists
    existing_shop = db.query(Shop).filter(Shop.code == shop.code).first()
    if existing_shop:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Shop code already exists"
        )
    
    # Check if shop name already exists
    existing_name = db.query(Shop).filter(Shop.name == shop.name).first()
    if existing_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Shop name already exists"
        )
    
    # Check if area exists
    area = db.query(Area).filter(Area.id == shop.area_id).first()
    if not area:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Area not found"
        )
    
    db_shop = create_shop(db=db, shop=shop)
    
    # Return with area name
    shop_dict = {
        "id": db_shop.id,
        "name": db_shop.name,
        "code": db_shop.code,
        "area_id": db_shop.area_id,
        "address": db_shop.address,
        "phone": db_shop.phone,
        "email": db_shop.email,
        "manager": db_shop.manager,
        "description": db_shop.description,
        "status": db_shop.status,
        "created_at": db_shop.created_at,
        "updated_at": db_shop.updated_at,
        "area_name": area.name
    }
    
    return shop_dict

@router.put("/{shop_id}", response_model=ShopOut)
def update_existing_shop(shop_id: int, shop: ShopUpdate, db: Session = Depends(get_db)):
    """Update an existing shop"""
    db_shop = get_shop(db, shop_id=shop_id)
    if db_shop is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shop not found"
        )
    
    # Check if new code conflicts with existing shops (excluding current shop)
    if shop.code and shop.code != db_shop.code:
        existing_code = db.query(Shop).filter(
            Shop.code == shop.code,
            Shop.id != shop_id
        ).first()
        if existing_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Shop code already exists"
            )
    
    # Check if new name conflicts with existing shops (excluding current shop)
    if shop.name and shop.name != db_shop.name:
        existing_name = db.query(Shop).filter(
            Shop.name == shop.name,
            Shop.id != shop_id
        ).first()
        if existing_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Shop name already exists"
            )
    
    # Check if new area exists
    if shop.area_id and shop.area_id != db_shop.area_id:
        area = db.query(Area).filter(Area.id == shop.area_id).first()
        if not area:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Area not found"
            )
    
    updated_shop = update_shop(db=db, shop_id=shop_id, shop=shop)
    
    # Return with area name
    area = db.query(Area).filter(Area.id == updated_shop.area_id).first()
    shop_dict = {
        "id": updated_shop.id,
        "name": updated_shop.name,
        "code": updated_shop.code,
        "area_id": updated_shop.area_id,
        "address": updated_shop.address,
        "phone": updated_shop.phone,
        "email": updated_shop.email,
        "manager": updated_shop.manager,
        "description": updated_shop.description,
        "status": updated_shop.status,
        "created_at": updated_shop.created_at,
        "updated_at": updated_shop.updated_at,
        "area_name": area.name if area else None
    }
    
    return shop_dict

@router.delete("/{shop_id}")
def delete_existing_shop(shop_id: int, db: Session = Depends(get_db)):
    """Delete a shop"""
    db_shop = get_shop(db, shop_id=shop_id)
    if db_shop is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shop not found"
        )
    
    delete_shop(db=db, shop_id=shop_id)
    return {"message": "Shop deleted successfully"}

@router.get("/by-area/{area_id}")
def get_shops_by_area(area_id: int, db: Session = Depends(get_db)):
    """Get all shops in a specific area"""
    area = db.query(Area).filter(Area.id == area_id).first()
    if not area:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Area not found"
        )
    
    shops = db.query(Shop).filter(Shop.area_id == area_id).all()
    return shops

@router.get("/stats/summary")
def get_shops_summary(db: Session = Depends(get_db)):
    """Get shops statistics summary"""
    total_shops = db.query(func.count(Shop.id)).scalar()
    active_shops = db.query(func.count(Shop.id)).filter(Shop.status == 'active').scalar()
    inactive_shops = db.query(func.count(Shop.id)).filter(Shop.status == 'inactive').scalar()
    pending_shops = db.query(func.count(Shop.id)).filter(Shop.status == 'pending').scalar()
    suspended_shops = db.query(func.count(Shop.id)).filter(Shop.status == 'suspended').scalar()
    
    return {
        "total_shops": total_shops,
        "active_shops": active_shops,
        "inactive_shops": inactive_shops,
        "pending_shops": pending_shops,
        "suspended_shops": suspended_shops
    }
