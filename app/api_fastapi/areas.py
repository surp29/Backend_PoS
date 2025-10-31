from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from ..database import get_db
from ..models import Area, Shop
from ..schemas_fastapi import AreaCreate, AreaUpdate, AreaOut

router = APIRouter(prefix="/areas", tags=["areas"])

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
    query = db.query(Area)
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
    areas = query.offset(skip).limit(limit).all()
    result = []
    for area in areas:
        shop_count = db.query(func.count(Shop.id)).filter(Shop.area_id == area.id).scalar()
        area_dict = {**{col.name: getattr(area, col.name) for col in Area.__table__.columns}, "shop_count": shop_count}
        # Map to Vietnamese field names for frontend
        area_dict["ten_khu_vuc"] = area_dict.get("name")
        area_dict["ma_khu_vuc"] = area_dict.get("code")
        area_dict["loai_khu_vuc"] = area_dict.get("type")
        result.append(area_dict)
    return result

@router.get("/{area_id}", response_model=AreaOut)
def read_area(area_id: int, db: Session = Depends(get_db)):
    area = db.query(Area).filter(Area.id == area_id).first()
    if area is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Area not found")
    shop_count = db.query(func.count(Shop.id)).filter(Shop.area_id == area.id).scalar()
    area_dict = {**{col.name: getattr(area, col.name) for col in Area.__table__.columns}, "shop_count": shop_count}
    # Map to Vietnamese field names for frontend
    area_dict["ten_khu_vuc"] = area_dict.get("name")
    area_dict["ma_khu_vuc"] = area_dict.get("code")
    area_dict["loai_khu_vuc"] = area_dict.get("type")
    return area_dict

@router.post("/", response_model=AreaOut)
def create_new_area(area: AreaCreate, db: Session = Depends(get_db)):
    existing_area = db.query(Area).filter(Area.code == area.code).first()
    if existing_area:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Area code already exists")
    existing_name = db.query(Area).filter(Area.name == area.name).first()
    if existing_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Area name already exists")
    db_area = Area(**area.dict())
    db.add(db_area)
    db.commit()
    db.refresh(db_area)
    shop_count = db.query(func.count(Shop.id)).filter(Shop.area_id == db_area.id).scalar()
    area_dict = {**{col.name: getattr(db_area, col.name) for col in Area.__table__.columns}, "shop_count": shop_count}
    return area_dict

@router.put("/{area_id}", response_model=AreaOut)
def update_existing_area(area_id: int, area: AreaUpdate, db: Session = Depends(get_db)):
    db_area = db.query(Area).filter(Area.id == area_id).first()
    if db_area is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Area not found")
    if area.code and area.code != db_area.code:
        existing_code = db.query(Area).filter(Area.code == area.code, Area.id != area_id).first()
        if existing_code:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Area code already exists")
    if area.name and area.name != db_area.name:
        existing_name = db.query(Area).filter(Area.name == area.name, Area.id != area_id).first()
        if existing_name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Area name already exists")
    for field, value in area.dict(exclude_unset=True).items():
        setattr(db_area, field, value)
    db.commit()
    db.refresh(db_area)
    shop_count = db.query(func.count(Shop.id)).filter(Shop.area_id == db_area.id).scalar()
    area_dict = {**{col.name: getattr(db_area, col.name) for col in Area.__table__.columns}, "shop_count": shop_count}
    return area_dict

@router.delete("/{area_id}")
def delete_existing_area(area_id: int, db: Session = Depends(get_db)):
    db_area = db.query(Area).filter(Area.id == area_id).first()
    if db_area is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Area not found")
    shop_count = db.query(func.count(Shop.id)).filter(Shop.area_id == area_id).scalar()
    if shop_count > 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Cannot delete area. It has {shop_count} shop(s). Please delete shops first.")
    db.delete(db_area)
    db.commit()
    return {"message": "Area deleted successfully"}

@router.get("/{area_id}/shops")
def get_area_shops(area_id: int, db: Session = Depends(get_db)):
    area = db.query(Area).filter(Area.id == area_id).first()
    if area is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Area not found")
    shops = db.query(Shop).filter(Shop.area_id == area_id).all()
    return shops
