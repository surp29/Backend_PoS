"""
Chatbot API for AI assistant reorder suggestions
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from datetime import datetime, timedelta, date
from ..database import get_db
from ..models import Product, Warehouse, Order, OrderItem, Invoice, InvoiceItem
from ..logger import log_info, log_error, log_success
from typing import List, Optional

router = APIRouter(prefix="/chatbot", tags=["chatbot"])


def analyze_sales_trend(product_code: str, days: int, db: Session) -> dict:
    """Phân tích xu hướng bán hàng của sản phẩm từ hóa đơn đã thanh toán"""
    # Tính toán số lượng đã bán trong khoảng thời gian
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    # Tìm product_id từ product_code
    product = db.query(Product).filter(Product.ma_sp == product_code).first()
    if not product:
        return {
            "total_sold": 0,
            "sales_rate": 0,
            "period_days": days
        }
    
    # Lấy tất cả invoice items của sản phẩm đã thanh toán trong khoảng thời gian
    total_sold = db.query(func.sum(InvoiceItem.so_luong)).join(
        Invoice, InvoiceItem.invoice_id == Invoice.id
    ).filter(
        and_(
            Invoice.ngay_hd >= start_date,
            Invoice.ngay_hd <= end_date,
            Invoice.trang_thai.ilike('%đã thanh toán%'),
            InvoiceItem.product_code == product_code
        )
    ).scalar() or 0
    
    # Tính tốc độ bán trung bình mỗi ngày
    sales_rate = total_sold / days if days > 0 else 0
    
    return {
        "total_sold": int(total_sold),
        "sales_rate": round(sales_rate, 2),
        "period_days": days
    }


def calculate_reorder_suggestion(product: Product, warehouse: Optional[Warehouse], db: Session) -> dict:
    """Tính toán đề xuất đặt hàng"""
    # Phân tích xu hướng bán hàng trong 30 ngày
    trend_30 = analyze_sales_trend(product.ma_sp, 30, db)
    trend_7 = analyze_sales_trend(product.ma_sp, 7, db)
    
    # Lấy số lượng tồn kho hiện tại
    current_stock = warehouse.so_luong if warehouse else product.so_luong
    
    # Tính tốc độ bán trung bình (ưu tiên 7 ngày gần nhất)
    sales_rate = trend_7["sales_rate"] if trend_7["sales_rate"] > 0 else trend_30["sales_rate"]
    
    # Tính số ngày dự kiến hết hàng
    days_until_out = int(current_stock / sales_rate) if sales_rate > 0 else 999
    
    # Tính số lượng đề xuất đặt hàng (đủ cho 30 ngày + buffer 20%)
    if sales_rate > 0:
        recommended_quantity = int(sales_rate * 30 * 1.2)
    else:
        # Nếu chưa có dữ liệu bán hàng, đề xuất bằng số lượng hiện tại
        recommended_quantity = max(current_stock, 50)
    
    # Xác định mức độ ưu tiên
    priority = "high" if days_until_out <= 7 or current_stock <= 10 else "normal"
    
    return {
        "ma_sp": product.ma_sp,
        "product_name": product.ten_sp,
        "current_stock": current_stock,
        "sales_rate": round(sales_rate, 2),
        "days_until_out": days_until_out if days_until_out < 999 else "N/A",
        "recommended_quantity": recommended_quantity,
        "priority": priority,
        "gia_nhap": warehouse.gia_nhap if warehouse else product.gia_von or 0
    }


@router.post("/analyze")
def analyze_and_suggest(message: dict, db: Session = Depends(get_db)):
    """Phân tích yêu cầu và đưa ra đề xuất"""
    user_message = message.get("message", "").lower()
    
    log_info("CHATBOT", f"Received message: {user_message}")
    
    # Phân tích intent từ message
    if any(keyword in user_message for keyword in ["đề xuất", "đặt hàng", "reorder", "suggest"]):
        # Lấy tất cả sản phẩm có trong kho
        products = db.query(Product).all()
        suggestions = []
        
        # Lấy danh sách sản phẩm bán chạy để ưu tiên
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        best_sellers = db.query(
            InvoiceItem.product_code,
            func.sum(InvoiceItem.so_luong).label('total_sold')
        ).join(
            Invoice, InvoiceItem.invoice_id == Invoice.id
        ).filter(
            and_(
                Invoice.ngay_hd >= start_date,
                Invoice.ngay_hd <= end_date,
                Invoice.trang_thai.ilike('%đã thanh toán%')
            )
        ).group_by(
            InvoiceItem.product_code
        ).order_by(
            desc('total_sold')
        ).limit(20).all()
        
        best_seller_codes = {seller.product_code for seller in best_sellers}
        
        for product in products:
            # Tìm warehouse của sản phẩm
            warehouse = db.query(Warehouse).filter(
                Warehouse.ma_sp == product.ma_sp
            ).first()
            
            suggestion = calculate_reorder_suggestion(product, warehouse, db)
            
            # Ưu tiên sản phẩm bán chạy đang dần hết hàng
            is_best_seller = product.ma_sp in best_seller_codes
            current_stock = warehouse.so_luong if warehouse else product.so_luong
            
            # Đề xuất nếu:
            # 1. Sắp hết hàng (days_until_out <= 30)
            # 2. Hoặc là sản phẩm bán chạy và tồn kho thấp (<= 50)
            # 3. Hoặc đã hết hàng
            if (suggestion["days_until_out"] != "N/A" and suggestion["days_until_out"] <= 30) or \
               (is_best_seller and current_stock <= 50) or \
               current_stock <= 0:
                suggestion["is_best_seller"] = is_best_seller
                suggestions.append(suggestion)
        
        # Sắp xếp: ưu tiên sản phẩm bán chạy và sắp hết hàng
        suggestions.sort(key=lambda x: (
            0 if x.get("is_best_seller", False) and x["priority"] == "high" else 1,  # Best seller + high priority first
            0 if x["priority"] == "high" else 1,  # High priority
            x["days_until_out"] if isinstance(x["days_until_out"], int) else 999  # Days until out
        ))
        
        # Giới hạn 5 đề xuất đầu tiên
        suggestions = suggestions[:5]
        
        if suggestions:
            best_seller_count = sum(1 for s in suggestions if s.get("is_best_seller", False))
            response_text = f"Tôi đã phân tích tồn kho và tìm thấy {len(suggestions)} sản phẩm cần đặt hàng:\n\n"
            if best_seller_count > 0:
                response_text += f"🔥 Trong đó có {best_seller_count} sản phẩm đang bán chạy và cần đặt hàng ngay!\n\n"
            response_text += "Dựa trên tốc độ bán hàng và số lượng tồn kho hiện tại, bạn nên xem xét đặt hàng các sản phẩm sau:"
        else:
            response_text = "Hiện tại không có sản phẩm nào cần đặt hàng khẩn cấp. Tất cả sản phẩm đều có đủ tồn kho."
            suggestions = []
        
        return {
            "response": response_text,
            "suggestions": suggestions
        }
    
    elif any(keyword in user_message for keyword in ["tồn kho", "inventory", "stock", "sắp hết", "hết hàng"]):
        # Tìm sản phẩm sắp hết hàng
        products = db.query(Product).all()
        low_stock_products = []
        
        for product in products:
            warehouse = db.query(Warehouse).filter(
                Warehouse.ma_sp == product.ma_sp
            ).first()
            
            current_stock = warehouse.so_luong if warehouse else product.so_luong
            
            if current_stock <= 20:  # Ngưỡng cảnh báo
                suggestion = calculate_reorder_suggestion(product, warehouse, db)
                low_stock_products.append(suggestion)
        
        if low_stock_products:
            response_text = f"Tôi đã kiểm tra và tìm thấy {len(low_stock_products)} sản phẩm có tồn kho thấp:\n\n"
            response_text += "Các sản phẩm này cần được theo dõi và đặt hàng sớm:"
        else:
            response_text = "Tất cả sản phẩm đều có đủ tồn kho. Không có sản phẩm nào sắp hết hàng."
            low_stock_products = []
        
        return {
            "response": response_text,
            "suggestions": low_stock_products[:5]  # Giới hạn 5 sản phẩm
        }
    
    elif any(keyword in user_message for keyword in ["bán chạy", "best selling", "top", "nhiều nhất"]):
        # Phân tích sản phẩm bán chạy từ hóa đơn đã thanh toán
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        # Lấy dữ liệu từ invoice items đã thanh toán
        best_sellers = db.query(
            InvoiceItem.product_code,
            InvoiceItem.product_name,
            func.sum(InvoiceItem.so_luong).label('total_sold'),
            func.sum(InvoiceItem.total_price).label('total_revenue')
        ).join(
            Invoice, InvoiceItem.invoice_id == Invoice.id
        ).filter(
            and_(
                Invoice.ngay_hd >= start_date,
                Invoice.ngay_hd <= end_date,
                Invoice.trang_thai.ilike('%đã thanh toán%')
            )
        ).group_by(
            InvoiceItem.product_code,
            InvoiceItem.product_name
        ).order_by(
            desc('total_sold')
        ).limit(10).all()
        
        if best_sellers:
            response_text = f"🔥 Top {len(best_sellers)} sản phẩm bán chạy trong 30 ngày qua:\n\n"
            
            suggestions = []
            for idx, seller in enumerate(best_sellers, 1):
                product = db.query(Product).filter(Product.ma_sp == seller.product_code).first()
                warehouse = db.query(Warehouse).filter(Warehouse.ma_sp == seller.product_code).first()
                
                current_stock = warehouse.so_luong if warehouse else (product.so_luong if product else 0)
                
                response_text += f"{idx}. {seller.product_name} ({seller.product_code})\n"
                response_text += f"   • Đã bán: {int(seller.total_sold)} sản phẩm\n"
                response_text += f"   • Doanh thu: {float(seller.total_revenue):,.0f} VNĐ\n"
                response_text += f"   • Tồn kho hiện tại: {current_stock}\n\n"
                
                # Nếu tồn kho thấp, thêm vào suggestions
                if current_stock <= 50:
                    suggestion = calculate_reorder_suggestion(product, warehouse, db) if product else None
                    if suggestion:
                        suggestions.append(suggestion)
            
            if suggestions:
                response_text += "\n⚠️ Một số sản phẩm bán chạy đang có tồn kho thấp và cần đặt hàng ngay!"
        else:
            response_text = "Chưa có dữ liệu bán hàng trong 30 ngày qua."
            suggestions = []
        
        return {
            "response": response_text,
            "suggestions": suggestions[:5]  # Giới hạn 5 đề xuất
        }
    
    elif any(keyword in user_message for keyword in ["phân tích", "analysis", "thống kê", "statistics"]):
        # Phân tích tổng quan
        total_products = db.query(Product).count()
        total_warehouse_items = db.query(Warehouse).count()
        
        # Đếm sản phẩm sắp hết
        low_stock_count = 0
        products = db.query(Product).all()
        for product in products:
            warehouse = db.query(Warehouse).filter(
                Warehouse.ma_sp == product.ma_sp
            ).first()
            current_stock = warehouse.so_luong if warehouse else product.so_luong
            if current_stock <= 20:
                low_stock_count += 1
        
        # Tính tổng doanh thu từ hóa đơn đã thanh toán
        total_revenue = db.query(func.sum(Invoice.tong_tien)).filter(
            Invoice.trang_thai.ilike('%đã thanh toán%')
        ).scalar() or 0
        
        response_text = f"📊 Báo cáo tổng quan:\n\n"
        response_text += f"• Tổng số sản phẩm: {total_products}\n"
        response_text += f"• Tổng số item trong kho: {total_warehouse_items}\n"
        response_text += f"• Sản phẩm sắp hết (≤20): {low_stock_count}\n"
        response_text += f"• Tổng doanh thu: {float(total_revenue):,.0f} VNĐ\n\n"
        response_text += "Bạn có muốn tôi đề xuất đặt hàng cho các sản phẩm sắp hết không?"
        
        return {
            "response": response_text,
            "suggestions": []
        }
    
    elif any(keyword in user_message for keyword in ["doanh thu", "revenue", "báo cáo", "report"]):
        # Phân tích doanh thu
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        # Tính tổng doanh thu từ hóa đơn đã thanh toán
        total_revenue = db.query(func.sum(Invoice.tong_tien)).filter(
            and_(
                Invoice.ngay_hd >= start_date,
                Invoice.ngay_hd <= end_date,
                Invoice.trang_thai.ilike('%đã thanh toán%')
            )
        ).scalar() or 0
        
        # Đếm số hóa đơn đã thanh toán
        paid_invoices_count = db.query(func.count(Invoice.id)).filter(
            and_(
                Invoice.ngay_hd >= start_date,
                Invoice.ngay_hd <= end_date,
                Invoice.trang_thai.ilike('%đã thanh toán%')
            )
        ).scalar() or 0
        
        # Tính công nợ
        unpaid_invoices = db.query(Invoice).filter(
            ~Invoice.trang_thai.ilike('%đã thanh toán%')
        ).all()
        total_debt = sum(float(inv.tong_tien or 0) for inv in unpaid_invoices)
        
        response_text = f"💰 Báo cáo doanh thu 30 ngày qua:\n\n"
        response_text += f"• Tổng doanh thu: {float(total_revenue):,.0f} VNĐ\n"
        response_text += f"• Số hóa đơn đã thanh toán: {paid_invoices_count}\n"
        response_text += f"• Tổng công nợ: {float(total_debt):,.0f} VNĐ\n"
        response_text += f"• Số hóa đơn chưa thanh toán: {len(unpaid_invoices)}\n\n"
        response_text += "Bạn có muốn xem sản phẩm bán chạy không?"
        
        return {
            "response": response_text,
            "suggestions": []
        }
    
    else:
        # Default response
        response_text = "Xin chào! Tôi là Thư ký ảo AI của bạn. Tôi có thể giúp bạn:\n\n"
        response_text += "• 📊 Phân tích và thống kê tồn kho\n"
        response_text += "• 🛒 Đề xuất đặt hàng tự động\n"
        response_text += "• ⚠️ Kiểm tra sản phẩm sắp hết hàng\n"
        response_text += "• 🔥 Phân tích sản phẩm bán chạy\n"
        response_text += "• 💰 Báo cáo doanh thu\n\n"
        response_text += "Hãy thử các lệnh như:\n"
        response_text += "• 'Đề xuất đặt hàng'\n"
        response_text += "• 'Sản phẩm sắp hết'\n"
        response_text += "• 'Sản phẩm bán chạy'\n"
        response_text += "• 'Phân tích tồn kho'\n"
        response_text += "• 'Báo cáo doanh thu'"
        
        return {
            "response": response_text,
            "suggestions": []
        }


@router.post("/create-order")
def create_reorder(payload: dict, db: Session = Depends(get_db)):
    """Tạo đơn đặt hàng tự động từ chatbot"""
    product_code = payload.get("product_code")
    quantity = payload.get("quantity")
    
    if not product_code or not quantity:
        raise HTTPException(status_code=400, detail="Thiếu thông tin sản phẩm hoặc số lượng")
    
    # Tìm sản phẩm
    product = db.query(Product).filter(Product.ma_sp == product_code).first()
    if not product:
        raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm")
    
    # Tìm warehouse
    warehouse = db.query(Warehouse).filter(Warehouse.ma_sp == product_code).first()
    
    # Tạo mã đơn hàng tự động
    order_code = f"CHATBOT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    try:
        # Tạo đơn hàng
        order = Order(
            ma_don_hang=order_code,
            thong_tin_kh="Đơn đặt hàng tự động từ Thư ký ảo AI",
            ngay_tao=datetime.now().date(),
            so_luong=quantity,
            tong_tien=quantity * (warehouse.gia_nhap if warehouse else product.gia_von or 0),
            trang_thai="Chờ xử lý"
        )
        db.add(order)
        db.flush()
        
        # Tạo order item
        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            so_luong=quantity,
            don_gia=warehouse.gia_nhap if warehouse else product.gia_von or 0,
            total_price=quantity * (warehouse.gia_nhap if warehouse else product.gia_von or 0)
        )
        db.add(order_item)
        db.commit()
        db.refresh(order)
        
        log_success("CHATBOT_ORDER", f"Created order {order_code} for product {product_code}, quantity {quantity}")
        
        return {
            "success": True,
            "order_code": order_code,
            "order_id": order.id,
            "message": f"Đã tạo đơn đặt hàng {order_code} cho {quantity} sản phẩm {product.ten_sp}"
        }
    except Exception as e:
        db.rollback()
        log_error("CHATBOT_ORDER", f"Error creating order: {str(e)}", error=e)
        raise HTTPException(status_code=500, detail=f"Lỗi khi tạo đơn đặt hàng: {str(e)}")

