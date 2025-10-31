from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Warehouse
from ..schemas_fastapi import WarehouseOut, WarehouseCreate, WarehouseUpdate


router = APIRouter(prefix="/warehouse", tags=["warehouse"])


@router.get("/", response_model=list[WarehouseOut])
def list_warehouses(db: Session = Depends(get_db)):
    return db.query(Warehouse).all()


@router.post("/")
def add_warehouse(payload: WarehouseCreate, db: Session = Depends(get_db)):
    wh = Warehouse(
        ma_kho=payload.ma_kho,
        ten_kho=payload.ten_kho,
        ma_sp=payload.ma_sp,
        gia_nhap=payload.gia_nhap,
        so_luong=payload.so_luong,
        dia_chi=payload.dia_chi,
        dien_thoai=payload.dien_thoai,
        ghi_chu=payload.ghi_chu,
        trang_thai=payload.trang_thai,
    )
    db.add(wh)
    db.commit()
    db.refresh(wh)
    return {"success": True}


@router.put("/{warehouse_id}")
def update_warehouse(warehouse_id: int, payload: WarehouseUpdate, db: Session = Depends(get_db)):
    wh = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
    if not wh:
        raise HTTPException(status_code=404, detail="Không tìm thấy kho hàng")
    
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(wh, key, value)
    
    db.commit()
    db.refresh(wh)
    return {"success": True}


@router.delete("/{warehouse_id}")
def delete_warehouse(warehouse_id: int, db: Session = Depends(get_db)):
    wh = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
    if not wh:
        raise HTTPException(status_code=404, detail="Không tìm thấy kho hàng")
    db.delete(wh)
    db.commit()
    return {"success": True}




