from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Invoice
from ..schemas_fastapi import InvoiceOut, InvoiceCreate, InvoiceUpdate
from ..logger import log_info, log_success, log_error, log_warning
from ..services.invoices import update_debt_for_customer
from datetime import datetime


router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.get("/", response_model=list[InvoiceOut])
def list_invoices(db: Session = Depends(get_db)):
    return db.query(Invoice).all()


@router.post("/")
def create_invoice(payload: InvoiceCreate, db: Session = Depends(get_db)):
    """Tạo hóa đơn mới"""
    log_info("CREATE_INVOICE", f"Tạo hóa đơn mới: {payload.so_hd} - Khách hàng: {payload.nguoi_mua} - Tổng tiền: {payload.tong_tien:,.0f} VND")
    
    try:
        # Tạo hóa đơn mới
        inv = Invoice(
            so_hd=payload.so_hd,
            ngay_hd=payload.ngay_hd,
            nguoi_mua=payload.nguoi_mua,
            tong_tien=payload.tong_tien,
            trang_thai=payload.trang_thai,
        )
        db.add(inv)
        db.commit()
        db.refresh(inv)
        
        # Cập nhật bảng công nợ
        update_debt_for_customer(payload.nguoi_mua, db)
        
        log_success("CREATE_INVOICE", f"Tạo hóa đơn thành công: {payload.so_hd} (ID: {inv.id})")
        return {"success": True, "id": inv.id}
    except Exception as e:
        log_error("CREATE_INVOICE", f"Lỗi khi tạo hóa đơn {payload.so_hd}", error=e)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi tạo hóa đơn: {str(e)}")


@router.put("/{invoice_id:int}")
def update_invoice(invoice_id: int, payload: InvoiceUpdate, db: Session = Depends(get_db)):
    try:
        inv = db.query(Invoice).get(invoice_id)
        if not inv:
            raise HTTPException(status_code=404, detail="Không tìm thấy hóa đơn")
        
        # Lưu tên khách hàng cũ để cập nhật công nợ
        old_customer_name = inv.nguoi_mua
        
        # Cập nhật hóa đơn
        if payload.so_hd is not None: setattr(inv, 'so_hd', payload.so_hd)
        if payload.ngay_hd is not None: setattr(inv, 'ngay_hd', payload.ngay_hd)
        if payload.nguoi_mua is not None: setattr(inv, 'nguoi_mua', payload.nguoi_mua)
        if payload.tong_tien is not None: setattr(inv, 'tong_tien', payload.tong_tien)
        if payload.loai_hd is not None: setattr(inv, 'loai_hd', payload.loai_hd)
        if payload.trang_thai is not None: setattr(inv, 'trang_thai', payload.trang_thai)
        
        db.commit()
        
        # Cập nhật công nợ cho khách hàng cũ (nếu có thay đổi)
        if old_customer_name:
            update_debt_for_customer(old_customer_name, db)
        
        # Cập nhật công nợ cho khách hàng mới
        new_customer_name = payload.nguoi_mua if payload.nguoi_mua is not None else old_customer_name
        if new_customer_name and new_customer_name != old_customer_name:
            update_debt_for_customer(new_customer_name, db)
        
        return {"success": True}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi cập nhật hóa đơn: {str(e)}")


@router.get("/{invoice_id:int}", response_model=InvoiceOut)
def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    inv = db.query(Invoice).get(invoice_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Không tìm thấy hóa đơn")
    return inv


@router.delete("/{invoice_id:int}")
def delete_invoice(invoice_id: int, db: Session = Depends(get_db)):
    try:
        inv = db.query(Invoice).get(invoice_id)
        if not inv:
            raise HTTPException(status_code=404, detail="Không tìm thấy hóa đơn")
        
        # Lưu tên khách hàng để cập nhật công nợ
        customer_name = inv.nguoi_mua
        
        # Xóa hóa đơn
        db.delete(inv)
        db.commit()
        
        # Cập nhật công nợ cho khách hàng
        if customer_name:
            update_debt_for_customer(customer_name, db)
        
        return {"success": True}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi xóa hóa đơn: {str(e)}")


@router.get("/next-number")
def next_invoice_number(db: Session = Depends(get_db)):
    last = db.query(Invoice).order_by(Invoice.id.desc()).first()
    # Avoid treating SQLAlchemy columns as booleans/strings directly
    if not last:
        return {"next_number": 1}
    so_hd_value = getattr(last, "so_hd", None)
    if not so_hd_value:
        return {"next_number": 1}
    import re
    m = re.search(r'HĐ-(\d+)', str(so_hd_value))
    if not m:
        return {"next_number": 1}
    return {"next_number": int(m.group(1)) + 1}


@router.post("/search")
def search_invoices(criteria: dict, db: Session = Depends(get_db)):
    q = db.query(Invoice)
    from_date = criteria.get("fromDate")
    to_date = criteria.get("toDate")
    invoice_number = criteria.get("invoiceNumber")
    customer_info = criteria.get("customerInfo")

    if from_date and to_date:
        q = q.filter(Invoice.ngay_hd.between(from_date, to_date))
    if invoice_number:
        like = f"%{invoice_number}%"
        q = q.filter(Invoice.so_hd.ilike(like))
    if customer_info:
        like = f"%{customer_info}%"
        q = q.filter(Invoice.nguoi_mua.ilike(like))

    rows = q.all()
    return {"success": True, "data": rows}

