from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from ..database import get_db
from ..models import Area, Shop
from ..schemas_fastapi import AreaCreate, AreaUpdate, AreaOut
from ..crud import get_area, get_areas, create_area, update_area, delete_area

router = APIRouter()

@router.get("/", response_model=List[AreaOut])
def read_areas(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    type_filter: Optional[str] = None,
    status_filter: Optional[str] = None,
    priority_filter: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all areas with optional filtering"""
    query = db.query(Area)
    
    # Apply filters
    if search:
        query = query.filter(
            Area.name.ilike(f"%{search}%") |
            Area.code.ilike(f"%{search}%") |
            Area.province.ilike(f"%{search}%") |
            Area.district.ilike(f"%{search}%")
        )
    
    if type_filter:
        query = query.filter(Area.type == type_filter)
    
    if status_filter:
        query = query.filter(Area.status == status_filter)
    
    if priority_filter:
        query = query.filter(Area.priority == priority_filter)
    
    # Get areas with shop count
    areas = query.offset(skip).limit(limit).all()
    
    # Add shop count to each area
    result = []
    for area in areas:
        shop_count = db.query(func.count(Shop.id)).filter(Shop.area_id == area.id).scalar()
        area_dict = {
            "id": area.id,
            "name": area.name,
            "code": area.code,
            "type": area.type,
            "province": area.province,
            "district": area.district,
            "ward": area.ward,
            "address": area.address,
            "postal_code": area.postal_code,
            "phone": area.phone,
            "email": area.email,
            "manager": area.manager,
            "description": area.description,
            "status": area.status,
            "priority": area.priority,
            "created_at": area.created_at,
            "updated_at": area.updated_at,
            "shop_count": shop_count
        }
        result.append(area_dict)
    
    return result

@router.get("/areas/{area_id}", response_model=AreaOut)
def read_area(area_id: int, db: Session = Depends(get_db)):
    """Get a specific area by ID"""
    area = get_area(db, area_id=area_id)
    if area is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Area not found"
        )
    
    # Add shop count
    shop_count = db.query(func.count(Shop.id)).filter(Shop.area_id == area.id).scalar()
    area_dict = {
        "id": area.id,
        "name": area.name,
        "code": area.code,
        "type": area.type,
        "province": area.province,
        "district": area.district,
        "ward": area.ward,
        "address": area.address,
        "postal_code": area.postal_code,
        "phone": area.phone,
        "email": area.email,
        "manager": area.manager,
        "description": area.description,
        "status": area.status,
        "priority": area.priority,
        "created_at": area.created_at,
        "updated_at": area.updated_at,
        "shop_count": shop_count
    }
    
    return area_dict

@router.post("/", response_model=AreaOut)
def create_new_area(area: AreaCreate, db: Session = Depends(get_db)):
    """Create a new area"""
    # Check if area code already exists
    existing_area = db.query(Area).filter(Area.code == area.code).first()
    if existing_area:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Area code already exists"
        )
    
    # Check if area name already exists
    existing_name = db.query(Area).filter(Area.name == area.name).first()
    if existing_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Area name already exists"
        )
    
    db_area = create_area(db=db, area=area)
    
    # Return with shop count
    shop_count = db.query(func.count(Shop.id)).filter(Shop.area_id == db_area.id).scalar()
    area_dict = {
        "id": db_area.id,
        "name": db_area.name,
        "code": db_area.code,
        "type": db_area.type,
        "province": db_area.province,
        "district": db_area.district,
        "ward": db_area.ward,
        "address": db_area.address,
        "postal_code": db_area.postal_code,
        "phone": db_area.phone,
        "email": db_area.email,
        "manager": db_area.manager,
        "description": db_area.description,
        "status": db_area.status,
        "priority": db_area.priority,
        "created_at": db_area.created_at,
        "updated_at": db_area.updated_at,
        "shop_count": shop_count
    }
    
    return area_dict

@router.put("/{area_id}", response_model=AreaOut)
def update_existing_area(area_id: int, area: AreaUpdate, db: Session = Depends(get_db)):
    """Update an existing area"""
    db_area = get_area(db, area_id=area_id)
    if db_area is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Area not found"
        )
    
    # Check if new code conflicts with existing areas (excluding current area)
    if area.code and area.code != db_area.code:
        existing_code = db.query(Area).filter(
            Area.code == area.code,
            Area.id != area_id
        ).first()
        if existing_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Area code already exists"
            )
    
    # Check if new name conflicts with existing areas (excluding current area)
    if area.name and area.name != db_area.name:
        existing_name = db.query(Area).filter(
            Area.name == area.name,
            Area.id != area_id
        ).first()
        if existing_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Area name already exists"
            )
    
    updated_area = update_area(db=db, area_id=area_id, area=area)
    
    # Return with shop count
    shop_count = db.query(func.count(Shop.id)).filter(Shop.area_id == updated_area.id).scalar()
    area_dict = {
        "id": updated_area.id,
        "name": updated_area.name,
        "code": updated_area.code,
        "type": updated_area.type,
        "province": updated_area.province,
        "district": updated_area.district,
        "ward": updated_area.ward,
        "address": updated_area.address,
        "postal_code": updated_area.postal_code,
        "phone": updated_area.phone,
        "email": updated_area.email,
        "manager": updated_area.manager,
        "description": updated_area.description,
        "status": updated_area.status,
        "priority": updated_area.priority,
        "created_at": updated_area.created_at,
        "updated_at": updated_area.updated_at,
        "shop_count": shop_count
    }
    
    return area_dict

@router.delete("/{area_id}")
def delete_existing_area(area_id: int, db: Session = Depends(get_db)):
    """Delete an area"""
    db_area = get_area(db, area_id=area_id)
    if db_area is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Area not found"
        )
    
    # Check if area has shops
    shop_count = db.query(func.count(Shop.id)).filter(Shop.area_id == area_id).scalar()
    if shop_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete area. It has {shop_count} shop(s). Please delete shops first."
        )
    
    delete_area(db=db, area_id=area_id)
    return {"message": "Area deleted successfully"}

@router.get("/areas/{area_id}/shops")
def get_area_shops(area_id: int, db: Session = Depends(get_db)):
    """Get all shops in a specific area"""
    area = get_area(db, area_id=area_id)
    if area is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Area not found"
        )
    
    shops = db.query(Shop).filter(Shop.area_id == area_id).all()
    return shops
