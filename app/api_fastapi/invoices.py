from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Invoice, Debt
from ..schemas_fastapi import InvoiceOut, InvoiceCreate, InvoiceUpdate
from datetime import datetime


router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.get("/", response_model=list[InvoiceOut])
def list_invoices(db: Session = Depends(get_db)):
    return db.query(Invoice).all()


@router.post("/")
def create_invoice(payload: InvoiceCreate, db: Session = Depends(get_db)):
    try:
        # Tạo hóa đơn mới
        inv = Invoice(
            so_hd=payload.so_hd,
            ngay_hd=payload.ngay_hd,
            nguoi_mua=payload.nguoi_mua,
            tong_tien=payload.tong_tien,
            loai_hd=payload.loai_hd,
            trang_thai=payload.trang_thai,
        )
        db.add(inv)
        db.commit()
        db.refresh(inv)
        
        # Cập nhật bảng công nợ
        update_debt_for_customer(payload.nguoi_mua, db)
        
        return {"success": True, "id": inv.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi tạo hóa đơn: {str(e)}")


def update_debt_for_customer(customer_name: str, db: Session):
    """Cập nhật bảng công nợ cho khách hàng"""
    try:
        # Tìm tất cả hóa đơn của khách hàng này
        invoices = db.query(Invoice).filter(Invoice.nguoi_mua == customer_name).all()
        
        if not invoices:
            return
        
        # Tính tổng công nợ và số tiền đã thanh toán
        total_debt = sum(float(invoice.tong_tien or 0 or 0) for invoice in invoices)
        paid_amount = sum(float(invoice.tong_tien or 0 or 0) for invoice in invoices 
                         if str(invoice.trang_thai or '' or '') == 'Đã thanh toán')
        remaining_debt = total_debt - paid_amount
        
        # Tìm hoặc tạo record trong bảng Debt
        debt_record = db.query(Debt).filter(Debt.customer_name == customer_name).first()
        
        if debt_record:
            # Cập nhật record hiện có
            setattr(debt_record, 'total_debt', total_debt)
            setattr(debt_record, 'paid_amount', paid_amount)
            setattr(debt_record, 'remaining_debt', remaining_debt)
            setattr(debt_record, 'status', 'Hết nợ' if remaining_debt <= 0 else 'Còn nợ')
            if paid_amount > 0:
                setattr(debt_record, 'last_payment_date', datetime.now())
        else:
            # Tạo record mới
            debt_record = Debt(
                customer_name=customer_name,
                total_debt=total_debt,
                paid_amount=paid_amount,
                remaining_debt=remaining_debt,
                status='Hết nợ' if remaining_debt <= 0 else 'Còn nợ',
                created_at=datetime.now()
            )
            db.add(debt_record)
        
        db.commit()
        print(f"✅ Đã cập nhật công nợ cho {customer_name}: Tổng={total_debt:,.0f}, Đã trả={paid_amount:,.0f}, Còn nợ={remaining_debt:,.0f}")
        
    except Exception as e:
        print(f"❌ Lỗi cập nhật công nợ cho {customer_name}: {e}")
        db.rollback()


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

