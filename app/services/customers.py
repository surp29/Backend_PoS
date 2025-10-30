# Backend/app/services/customers.py
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..models import Account, Order, Invoice

def safe_name(name: str | None) -> str:
    return (name or '').strip() or 'Khách vãng lai'

def calc_customer_tier(total_amount: float) -> dict:
    """Tính phân hạng tier cho khách hàng dựa trên tổng chi tiêu."""
    labels = [
        {'name': 'Đồng', 'color': '#cd7f32'},
        {'name': 'Bạc', 'color': '#bcc6cc'},
        {'name': 'Vàng', 'color': '#ffd700'},
        {'name': 'Bạch kim', 'color': '#e5e4e2'},
        {'name': 'Kim cương', 'color': '#00e5ee'},
    ]
    thresholds = [0, 30000000]
    for i in range(2, len(labels)):
        prev = thresholds[i-1]
        thresholds.append(prev + 10_000_000 + int(prev * 0.5))
    for i in reversed(range(len(thresholds))):
        if total_amount >= thresholds[i]:
            return { 'tierName': labels[i]['name'], 'tierColor': labels[i]['color'], 'tierLevel': i+1, 'tierMinAmount': thresholds[i] }
    return { 'tierName': labels[0]['name'], 'tierColor': labels[0]['color'], 'tierLevel': 1, 'tierMinAmount': thresholds[0] }

def customer_aggregates(db: Session):
    """Trả về tổng hợp theo khách hàng: orders count, total quantity, total amount, debt..."""
    order_rows = (
        db.query(
            Order.thong_tin_kh.label('customer_name'),
            func.count(Order.id).label('order_count'),
            func.coalesce(func.sum(Order.so_luong), 0).label('total_quantity'),
            func.coalesce(func.sum(Order.tong_tien), 0.0).label('total_amount'),
        ).group_by(Order.thong_tin_kh)
         .all()
    )
    paid_rows = (
        db.query(
            Invoice.nguoi_mua.label('customer_name'),
            func.coalesce(func.sum(Invoice.tong_tien), 0.0).label('paid_amount')
        ).filter(Invoice.trang_thai.ilike('%đã thanh toán%'))
         .group_by(Invoice.nguoi_mua)
         .all()
    )
    paid_map = { safe_name(r.customer_name): float(r.paid_amount or 0) for r in paid_rows }
    results = []
    for r in order_rows:
        name = safe_name(r.customer_name)
        total_amount = float(r.total_amount or 0)
        paid = paid_map.get(name, 0.0)
        debt = max(total_amount - paid, 0.0)
        results.append({
            'customerName': name,
            'orderCount': int(r.order_count or 0),
            'totalQuantity': int(r.total_quantity or 0),
            'totalAmount': total_amount,
            'totalDebt': debt,
        })
    return results

def customer_leaderboard(db: Session, limit: int = 100):
    """Leaderboard by total amount spent."""
    rows = (
        db.query(
            Order.thong_tin_kh.label('customer_name'),
            func.coalesce(func.sum(Order.tong_tien), 0.0).label('total_amount'),
            func.coalesce(func.sum(Order.so_luong), 0).label('total_quantity'),
            func.count(Order.id).label('order_count'),
        ).group_by(Order.thong_tin_kh)
        .order_by(func.coalesce(func.sum(Order.tong_tien), 0.0).desc())
        .limit(limit)
        .all()
    )
    return [
        {
            'customerName': safe_name(r.customer_name),
            'totalAmount': float(r.total_amount or 0),
            'totalQuantity': int(r.total_quantity or 0),
            'orderCount': int(r.order_count or 0),
            **calc_customer_tier(float(r.total_amount or 0))
        } for r in rows
    ]
