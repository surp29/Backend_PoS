from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Price
from ..schemas_fastapi import PriceCreate, PriceUpdate, PriceOut

router = APIRouter(prefix="/prices", tags=["prices"])

@router.get("/", response_model=list[PriceOut])
def list_prices(db: Session = Depends(get_db)):
    prices = db.query(Price).all()
    return prices

@router.post("/")
def create_price(payload: PriceCreate, db: Session = Depends(get_db)):
    price = Price(
        ma_sp=payload.ma_sp,
        ten_sp=payload.ten_sp,
        gia_chung=payload.gia_chung,
        ghi_chu=payload.ghi_chu,
    )
    db.add(price)
    db.commit()
    db.refresh(price)
    return {"success": True, "id": price.id}

@router.put("/{price_id}")
def update_price(price_id: int, payload: PriceUpdate, db: Session = Depends(get_db)):
    price = db.query(Price).get(price_id)
    if not price:
        raise HTTPException(status_code=404, detail="Không tìm thấy bảng giá")
    if payload.ma_sp is not None:
        price.ma_sp = payload.ma_sp
    if payload.ten_sp is not None:
        price.ten_sp = payload.ten_sp
    if payload.gia_chung is not None:
        price.gia_chung = payload.gia_chung
    if payload.ghi_chu is not None:
        price.ghi_chu = payload.ghi_chu
    db.commit()
    return {"success": True}

@router.delete("/{price_id}")
def delete_price(price_id: int, db: Session = Depends(get_db)):
    price = db.query(Price).get(price_id)
    if not price:
        raise HTTPException(status_code=404, detail="Không tìm thấy bảng giá")
    db.delete(price)
    db.commit()
    return {"success": True}