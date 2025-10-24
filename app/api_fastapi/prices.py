from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Price
from ..schemas_fastapi import PriceCreate, PriceUpdate


router = APIRouter(prefix="/prices", tags=["prices"])


@router.get("/")
def get_prices(db: Session = Depends(get_db)):
    """Lấy danh sách tất cả bảng giá"""
    prices = db.query(Price).all()
    result = []
    for price in prices:
        result.append({
            "id": price.id,
            "ma_sp": price.ma_sp,
            "ten_sp": price.ten_sp,
            "loai_sp": price.loai_sp,
            "gia_von": price.gia_von,
            "gia_chung": price.gia_chung,
            "created_at": price.created_at,
            "updated_at": price.updated_at
        })
    return {"success": True, "prices": result}
@router.get("/{price_id}")
def get_price(price_id: int, db: Session = Depends(get_db)):
    """Lấy chi tiết một bảng giá"""
    price = db.query(Price).get(price_id)
    if not price:
        raise HTTPException(status_code=404, detail="Không tìm thấy bảng giá")
    return {
        "success": True,
        "price": {
            "id": price.id,
            "ma_sp": price.ma_sp,
            "ten_sp": price.ten_sp,
            "loai_sp": price.loai_sp,
            "gia_von": price.gia_von,
            "gia_chung": price.gia_chung,
            "created_at": price.created_at,
            "updated_at": price.updated_at,
        }
    }


@router.post("/")
def add_price(payload: PriceCreate, db: Session = Depends(get_db)):
    """Tạo bảng giá mới"""
    # Kiểm tra xem mã bảng giá đã tồn tại chưa
    existing_price = db.query(Price).filter(Price.ma_sp == payload.ma_sp).first()
    if existing_price:
        raise HTTPException(
            status_code=400, 
            detail=f"Bảng giá với mã {payload.ma_sp} đã tồn tại."
        )
    
    # Tạo bảng giá mới
    price = Price(
        ma_sp=payload.ma_sp,
        ten_sp=payload.ten_sp,
        loai_sp=payload.loai_sp or 'Hành động',
        gia_von=payload.gia_von,
        gia_chung=payload.gia_chung
    )
    
    db.add(price)
    db.commit()
    db.refresh(price)
    
    return {"success": True, "id": price.id}


@router.put("/{price_id}")
def update_price(price_id: int, payload: PriceUpdate, db: Session = Depends(get_db)):
    """Cập nhật bảng giá"""
    price = db.query(Price).get(price_id)
    if not price:
        raise HTTPException(status_code=404, detail="Không tìm thấy bảng giá")
    
    # Cập nhật các field nếu có
    if payload.ma_sp is not None:
        # Kiểm tra xem mã mới có trùng với bảng giá khác không
        existing_price = db.query(Price).filter(Price.ma_sp == payload.ma_sp, Price.id != price_id).first()
        if existing_price:
            raise HTTPException(
                status_code=400, 
                detail=f"Bảng giá với mã {payload.ma_sp} đã tồn tại."
            )
        price.ma_sp = payload.ma_sp
    
    if payload.ten_sp is not None:
        price.ten_sp = payload.ten_sp
    
    if payload.loai_sp is not None:
        price.loai_sp = payload.loai_sp
    
    if payload.gia_von is not None:
        price.gia_von = payload.gia_von
    
    if payload.gia_chung is not None:
        price.gia_chung = payload.gia_chung
    
    # Không còn liên kết với product
    pass
    
    db.commit()
    return {"success": True}


@router.delete("/{price_id}")
def delete_price(price_id: int, db: Session = Depends(get_db)):
    """Xóa bảng giá theo ID"""
    price = db.query(Price).get(price_id)
    if not price:
        raise HTTPException(status_code=404, detail="Không tìm thấy bảng giá")
    
    db.delete(price)
    db.commit()
    return {"success": True}