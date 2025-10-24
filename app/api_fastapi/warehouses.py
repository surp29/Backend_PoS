from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Warehouse
from ..schemas_fastapi import WarehouseOut, WarehouseCreate


router = APIRouter()


@router.get("/", response_model=list[WarehouseOut])
def list_warehouses(db: Session = Depends(get_db)):
    return db.query(Warehouse).all()


@router.post("/")
def add_warehouse(payload: WarehouseCreate, db: Session = Depends(get_db)):
    wh = Warehouse(
        ma_kho=payload.ma_kho,
        ten_kho=payload.ten_kho,
        dia_chi=payload.dia_chi,
        dien_thoai=payload.dien_thoai,
        so_luong_sp=payload.so_luong_sp,
        trang_thai=payload.trang_thai,
        nhom_san_pham=payload.nhom_san_pham,
        mo_ta=payload.mo_ta,
    )
    db.add(wh)
    db.commit()
    return {"success": True}


@router.delete("/{warehouse_id}")
def delete_warehouse(warehouse_id: int, db: Session = Depends(get_db)):
    wh = db.query(Warehouse).get(warehouse_id)
    if not wh:
        raise HTTPException(status_code=404, detail="Không tìm thấy kho hàng")
    db.delete(wh)
    db.commit()
    return {"success": True}




