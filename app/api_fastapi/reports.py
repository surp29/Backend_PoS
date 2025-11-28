from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from ..database import get_db
from ..models import Invoice, InvoiceItem, Product
from datetime import datetime, date

router = APIRouter(prefix="/reports", tags=["reports"]) 

@router.get("/revenue")
def revenue_report(
    from_date: str = Query(None, description="Từ ngày (YYYY-MM-DD)"),
    to_date: str = Query(None, description="Đến ngày (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    Báo cáo doanh thu - chỉ tính các hóa đơn đã thanh toán
    """
    # Query chỉ lấy các hóa đơn đã thanh toán
    query = db.query(Invoice, InvoiceItem).join(
        InvoiceItem, Invoice.id == InvoiceItem.invoice_id
    ).filter(
        Invoice.trang_thai.ilike('%đã thanh toán%')
    )
    
    # Lọc theo ngày nếu có
    if from_date:
        try:
            from_date_obj = datetime.strptime(from_date, '%Y-%m-%d').date()
            query = query.filter(Invoice.ngay_hd >= from_date_obj)
        except ValueError:
            pass
    
    if to_date:
        try:
            to_date_obj = datetime.strptime(to_date, '%Y-%m-%d').date()
            query = query.filter(Invoice.ngay_hd <= to_date_obj)
        except ValueError:
            pass
    
    # Lấy tất cả invoice items đã thanh toán
    paid_items = query.all()
    
    # Tính tổng doanh thu và số lượng
    total_revenue = 0.0
    total_quantity_sold = 0
    product_revenue = {}  # {product_code: {ten_sp, so_luong_ban, gia_ban, doanh_thu}}
    
    for invoice, item in paid_items:
        total_revenue += float(item.total_price or 0)
        total_quantity_sold += int(item.so_luong or 0)
        
        # Nhóm theo sản phẩm
        product_code = item.product_code or 'N/A'
        if product_code not in product_revenue:
            product_revenue[product_code] = {
                'ma_sp': product_code,
                'ten_sp': item.product_name or 'N/A',
                'so_luong_ban': 0,
                'gia_ban': float(item.don_gia or 0),
                'doanh_thu': 0.0
            }
        
        product_revenue[product_code]['so_luong_ban'] += int(item.so_luong or 0)
        product_revenue[product_code]['doanh_thu'] += float(item.total_price or 0)
    
    # Tính tổng số lượng còn lại và tổng sản phẩm
    total_quantity_remaining = db.query(func.sum(Product.so_luong)).scalar() or 0
    total_products = db.query(func.count(Product.id)).scalar() or 0
    
    # Tính tỷ lệ cho mỗi sản phẩm
    # Tỷ lệ = (doanh thu sản phẩm / tổng doanh thu) * 100
    items = []
    for product_code, data in product_revenue.items():
        if total_revenue > 0:
            ty_le = (data['doanh_thu'] / total_revenue) * 100
        else:
            ty_le = 0.0
        items.append({
            **data,
            'ty_le': round(ty_le, 2)  # Làm tròn đến 2 chữ số thập phân
        })
    
    # Sắp xếp theo doanh thu giảm dần
    items.sort(key=lambda x: x['doanh_thu'], reverse=True)
    
    return {
        "summary": {
            "total_revenue": round(total_revenue, 2),
            "total_quantity_sold": total_quantity_sold,
            "total_quantity_remaining": int(total_quantity_remaining),
            "total_products": total_products
        },
        "items": items
    }

@router.get("/debt")
def debt_report(db: Session = Depends(get_db)):
    """
    Báo cáo công nợ - tính các hóa đơn chưa thanh toán
    """
    # Query lấy các hóa đơn chưa thanh toán (không phải "Đã thanh toán")
    unpaid_invoices = db.query(Invoice).filter(
        ~Invoice.trang_thai.ilike('%đã thanh toán%')
    ).all()
    
    # Tính tổng công nợ
    total_debt = sum(float(inv.tong_tien or 0) for inv in unpaid_invoices)
    
    # Tính công nợ quá hạn (giả sử quá 30 ngày là quá hạn)
    today = date.today()
    overdue_debt = 0.0
    overdue_count = 0
    
    for inv in unpaid_invoices:
        if inv.ngay_hd:
            days_diff = (today - inv.ngay_hd).days
            if days_diff > 30:
                overdue_debt += float(inv.tong_tien or 0)
                overdue_count += 1
    
    # Đếm số khách hàng nợ (unique)
    debt_customers = len(set(inv.nguoi_mua for inv in unpaid_invoices if inv.nguoi_mua))
    
    # Tính công nợ trung bình
    avg_debt = (total_debt / debt_customers) if debt_customers > 0 else 0
    
    # Tạo danh sách chi tiết công nợ
    items = []
    for inv in unpaid_invoices:
        days_diff = (today - inv.ngay_hd).days if inv.ngay_hd else 0
        status = 'overdue' if days_diff > 30 else 'normal'
        
        items.append({
            'khach_hang': inv.nguoi_mua or 'N/A',
            'so_hoa_don': inv.so_hd or 'N/A',
            'ngay_tao': inv.ngay_hd.isoformat() if inv.ngay_hd else '',
            'so_tien_no': float(inv.tong_tien or 0),
            'trang_thai': status,
            'ghi_chu': f'Còn nợ {days_diff} ngày' if days_diff > 0 else 'Chưa thanh toán'
        })
    
    # Sắp xếp theo số tiền nợ giảm dần
    items.sort(key=lambda x: x['so_tien_no'], reverse=True)
    
    return {
        "summary": {
            "total_debt": round(total_debt, 2),
            "overdue_debt": round(overdue_debt, 2),
            "debt_customers": debt_customers,
            "avg_debt": round(avg_debt, 2)
        },
        "items": items
    }
