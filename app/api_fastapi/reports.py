from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from ..database import get_db
from ..models import Order, Product, Invoice, Report, Debt, Price
from ..schemas_fastapi import ReportOut, ReportCreate, ReportUpdate, DebtOut, DebtUpdate
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json
from decimal import Decimal

router = APIRouter(prefix="/reports", tags=["reports"])



@router.get("/revenue-by-date")
def get_revenue_by_date(
    from_date: str = Query(..., description="Ngày bắt đầu (YYYY-MM-DD)"),
    to_date: str = Query(..., description="Ngày kết thúc (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    Lấy báo cáo doanh thu theo ngày từ from_date đến to_date
    """
    try:
        # Validate date format
        try:
            start_date = datetime.strptime(from_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(to_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=422, 
                detail="Định dạng ngày không hợp lệ. Sử dụng định dạng YYYY-MM-DD"
            )
        
        if (end_date - start_date).days > 31:
            raise HTTPException(status_code=400, detail="Khoảng thời gian tối đa là 31 ngày")
        
        if start_date > end_date:
            raise HTTPException(status_code=400, detail="Ngày bắt đầu phải nhỏ hơn ngày kết thúc")
        
        date_range = []
        current_date = start_date
        while current_date <= end_date:
            date_range.append(current_date)
            current_date += timedelta(days=1)
        
        # Lấy tất cả hóa đơn trong khoảng thời gian (không filter theo trạng thái)
        invoices = db.query(Invoice).filter(
            Invoice.ngay_hd.between(start_date, end_date)
        ).all()
        
        # Debug: In ra số lượng hóa đơn tìm được
        print(f"🔍 Found {len(invoices)} invoices between {start_date} and {end_date}")
        
        # Tính tổng doanh thu từ tất cả hóa đơn
        total_revenue = sum(float(invoice.tong_tien or 0) for invoice in invoices)
        
        # Tính số lượng đã bán từ tất cả đơn hàng (không filter theo trạng thái)
        total_quantity_sold = 0
        orders_from_paid_invoices = []
        
        for invoice in invoices:
            # Tìm đơn hàng theo tên khách hàng
            order = db.query(Order).filter(
                Order.thong_tin_kh == invoice.nguoi_mua
                # Bỏ filter Order.trang_thai == 'Hoàn thành' để lấy tất cả
            ).first()
            if order:
                so_luong_val = int(order.so_luong or 0)
                total_quantity_sold += so_luong_val
                orders_from_paid_invoices.append(order)
                print(f"📋 Found order for customer {invoice.nguoi_mua}: quantity {so_luong_val}")
            else:
                print(f"❌ No order found for customer {invoice.nguoi_mua}")
        
        print(f"📊 Total quantity sold: {total_quantity_sold}")
        print(f"📋 Total orders found: {len(orders_from_paid_invoices)}")
        
        # Lấy tổng số lượng còn lại từ sản phẩm
        # Ensure numeric scalar, avoid Column types leaking
        total_remaining = float(db.query(func.coalesce(func.sum(Product.so_luong), 0)).scalar() or 0)
        
        # Tạo dữ liệu cho biểu đồ (theo ngày)
        chart_columns = []
        for date in date_range:
            date_key = date.strftime("%Y-%m-%d")
            
            # Tính doanh thu theo ngày
            day_revenue = sum(float(invoice.tong_tien or 0 or 0) for invoice in invoices 
                            if invoice.ngay_hd.strftime("%Y-%m-%d") == date_key)
            
            # Tính số lượng đã bán theo ngày (từ tất cả hóa đơn)
            day_quantity_sold = 0
            for invoice in invoices:
                if invoice.ngay_hd.strftime("%Y-%m-%d") == date_key:
                    order = db.query(Order).filter(
                        Order.thong_tin_kh == invoice.nguoi_mua
                        # Bỏ filter Order.trang_thai == 'Hoàn thành'
                    ).first()
                    if order:
                        day_quantity_sold += int(order.so_luong or 0 or 0)
            
            chart_columns.append({
                'date': date.strftime("%d/%m/%Y"),
                'date_key': date_key,
                'revenue': day_revenue,
                'quantity_sold': day_quantity_sold,
                'quantity_remaining': total_remaining
            })
        
        # Tạo dữ liệu cho bảng sản phẩm
        # Lấy thông tin sản phẩm từ hóa đơn → đơn hàng → sản phẩm
        product_columns = []
        product_revenue_map = {}  # Map để tính doanh thu theo sản phẩm
        
        print(f"🔍 Processing {len(invoices)} invoices for product data...")
        
        # Duyệt qua từng hóa đơn
        for invoice in invoices:
            # Tìm đơn hàng theo tên khách hàng
            order = db.query(Order).filter(
                Order.thong_tin_kh == invoice.nguoi_mua
                # Bỏ filter Order.trang_thai == 'Hoàn thành'
            ).first()
            
            if order:
                sp_code = order.sp_banggia or None
                if sp_code:  # Nếu đơn hàng có mã sản phẩm
                    # Tìm sản phẩm theo mã
                    product = db.query(Product).filter(
                        Product.ma_sp == sp_code
                    ).first()
                    
                    if product:
                        # Sản phẩm có trong bảng products - lấy thông tin từ products
                        product_key = f"{product.ma_sp or ''}-{product.ten_sp or ''}"
                        if product_key not in product_revenue_map:
                            # Lấy nhóm SP từ bảng products (không phải "DV")
                            nhom_sp = product.nhom_sp or None
                            if not nhom_sp or nhom_sp.strip() == '':
                                nhom_sp = 'Chưa phân loại'  # Mặc định cho sản phẩm không có nhóm
                            
                            product_revenue_map[product_key] = {
                                'ten_san_pham': product.ten_sp or None or 'Chưa có tên',
                                'nhom_san_pham': nhom_sp,
                                'doanh_thu': 0,
                                'so_luong_ban': 0
                            }
                            
                            print(f"📦 Product found in products table: {sp_code} -> Group: {nhom_sp}, Name: {product.ten_sp or None}")
                        
                        # Cộng dồn doanh thu và số lượng cho sản phẩm này
                        product_revenue_map[product_key]['doanh_thu'] += float(invoice.tong_tien or 0 or 0)
                        product_revenue_map[product_key]['so_luong_ban'] += int(order.so_luong or 0 or 0)
                    else:
                        # Sản phẩm KHÔNG có trong bảng products - kiểm tra bảng prices
                        # Tìm trong bảng prices để lấy tên sản phẩm và nhóm "DV"
                        price_item = db.query(Price).filter(Price.ma_sp == sp_code).first()
                        
                        if price_item:
                            # Có trong bảng prices - sử dụng thông tin từ prices
                            product_key = f"{sp_code}-{price_item.ten_sp or sp_code}"
                            if product_key not in product_revenue_map:
                                product_revenue_map[product_key] = {
                                    'ten_san_pham': price_item.ten_sp or sp_code,  # Lấy tên SP từ prices
                                    'nhom_san_pham': 'DV',  # Nhóm "DV" chỉ dành cho prices
                                    'doanh_thu': 0,
                                    'so_luong_ban': 0
                                }
                                
                                print(f"📦 Product found in prices table: {sp_code} -> Group: DV, Name: {price_item.ten_sp or sp_code}")
                        else:
                            # Không có trong cả products và prices - mặc định
                            product_key = f"{sp_code}-{sp_code}"
                            if product_key not in product_revenue_map:
                                product_revenue_map[product_key] = {
                                    'ten_san_pham': sp_code,  # Sử dụng mã SP làm tên
                                    'nhom_san_pham': 'Chưa phân loại',  # Không phải "DV"
                                    'doanh_thu': 0,
                                    'so_luong_ban': 0
                                }
                                
                                print(f"📦 Product NOT found anywhere: {sp_code} -> Default Group: Chưa phân loại")
                        
                        product_revenue_map[product_key]['doanh_thu'] += float(invoice.tong_tien or 0 or 0)
                        product_revenue_map[product_key]['so_luong_ban'] += int(order.so_luong or 0 or 0)
        
        # Chuyển map thành list để trả về
        print(f"📊 Final product data summary:")
        for product_data in product_revenue_map.values():
            print(f"  - {product_data['ten_san_pham']} ({product_data['nhom_san_pham']}): {product_data['so_luong_ban']} sản phẩm, {product_data['doanh_thu']:,.0f} VND")
            
            product_columns.append({
                'ten_san_pham': product_data['ten_san_pham'],
                'nhom_san_pham': product_data['nhom_san_pham'],
                'tu_ngay': from_date,
                'den_ngay': to_date,
                'doanh_thu': product_data['doanh_thu'],
                'so_luong_ban': product_data['so_luong_ban']
            })
        
        return {
            'success': True,
            'data': {
                'columns': chart_columns,  # Dữ liệu cho biểu đồ
                'product_data': product_columns,  # Dữ liệu cho bảng sản phẩm
                'summary': {
                    'total_revenue': total_revenue,
                    'total_quantity_sold': total_quantity_sold,
                    'total_quantity_remaining': total_remaining,
                    'date_range': {
                        'from_date': from_date,
                        'to_date': to_date,
                        'total_days': len(date_range)
                    }
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")

@router.get("/", response_model=List[ReportOut])
def list_reports(db: Session = Depends(get_db)):
    return db.query(Report).all()

@router.get("/debt-report")
def get_debt_report(db: Session = Depends(get_db)):
    """Lấy báo cáo công nợ"""
    try:
        # Lấy tất cả hóa đơn
        invoices = db.query(Invoice).all()
        
        # Nhóm theo khách hàng
        customer_debt = {}
        for invoice in invoices:
            customer = invoice.nguoi_mua or None
            if customer not in customer_debt:
                customer_debt[customer] = {
                    'total_debt': 0,
                    'paid_amount': 0,
                    'remaining_debt': 0
                }
            
            # Tổng công nợ = tổng tất cả hóa đơn
            customer_debt[customer]['total_debt'] += float(invoice.tong_tien or 0 or 0)
            
            # Đã thanh toán = tổng hóa đơn đã thanh toán
            status_value = str(invoice.trang_thai or '' or '')
            if status_value == 'Đã thanh toán':
                customer_debt[customer]['paid_amount'] += float(invoice.tong_tien or 0 or 0)
        
        # Tính số tiền còn nợ
        for customer in customer_debt:
            customer_debt[customer]['remaining_debt'] = (
                customer_debt[customer]['total_debt'] - 
                customer_debt[customer]['paid_amount']
            )
        
        # Chuyển thành list
        debt_data = []
        for customer, data in customer_debt.items():
            debt_data.append({
                'ten_khach_hang': customer,
                'tong_cong_no': data['total_debt'],
                'da_thanh_toan': data['paid_amount'],
                'con_no': data['remaining_debt'],
                'trang_thai': 'Còn nợ' if data['remaining_debt'] > 0 else 'Hết nợ'
            })
        
        return {
            'success': True,
            'data': debt_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")

@router.get("/debt-by-date")
def get_debt_by_date(
    from_date: str = Query(..., description="Ngày bắt đầu (YYYY-MM-DD)"),
    to_date: str = Query(..., description="Ngày kết thúc (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Lấy báo cáo công nợ theo ngày"""
    try:
        # Validate date format
        try:
            start_date = datetime.strptime(from_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(to_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=422, 
                detail="Định dạng ngày không hợp lệ. Sử dụng định dạng YYYY-MM-DD"
            )
        
        if start_date > end_date:
            raise HTTPException(status_code=400, detail="Ngày bắt đầu phải nhỏ hơn ngày kết thúc")
        
        # Lấy dữ liệu từ bảng debts (đã được cập nhật bởi API payment-status)
        from ..models import Debt
        debt_records = db.query(Debt).all()
        
        print(f"🔍 Found {len(debt_records)} debt records in database")
        
        # Chuyển thành list với format phù hợp với frontend
        debt_data = []
        for debt_record in debt_records:
            debt_data.append({
                'customer_name': debt_record.customer_name,
                'total_debt': float(debt_record.total_debt or 0 or 0),
                'paid_amount': float(debt_record.paid_amount or 0 or 0),
                'remaining_debt': float(debt_record.remaining_debt or 0 or 0),
                'status': str(debt_record.status or '' or 'Còn nợ')
            })
        
        print(f"📊 Debt report summary: {len(debt_data)} customers")
        for item in debt_data:
            print(f"  - {item['customer_name']}: Total={item['total_debt']:,.0f}, Paid={item['paid_amount']:,.0f}, Remaining={item['remaining_debt']:,.0f}")
            
        # Debug: In ra chi tiết từng record trong bảng debts
        print(f"🔍 Detailed debt records:")
        for debt_record in debt_records:
            print(f"  Customer: {debt_record.customer_name}")
            print(f"    - Total Debt: {debt_record.total_debt or 0:,.0f}")
            print(f"    - Paid Amount: {debt_record.paid_amount or 0:,.0f}")
            print(f"    - Remaining Debt: {debt_record.remaining_debt or 0:,.0f}")
            print(f"    - Status: {debt_record.status or 'N/A'}")
        
        return {
            'success': True,
            'data': debt_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")

@router.put("/payment-status")
def update_payment_status(
    payload: dict,
    db: Session = Depends(get_db)
):
    """Cập nhật trạng thái thanh toán cho khách hàng"""
    try:
        print("🚀 API /payment-status được gọi")
        customer_name = payload.get('customer_name')
        paid_amount = float(payload.get('paid_amount', 0))
        
        print(f"📋 Input: customer_name={customer_name}, paid_amount={paid_amount}")
        
        if not customer_name:
            raise HTTPException(status_code=400, detail="Tên khách hàng không được để trống")
        
        # Tìm tất cả hóa đơn của khách hàng này
        invoices = db.query(Invoice).filter(Invoice.nguoi_mua == customer_name).all()
        
        print(f"🔍 Tìm thấy {len(invoices)} hóa đơn cho {customer_name}")
        
        if not invoices:
            raise HTTPException(status_code=404, detail=f"Không tìm thấy hóa đơn của khách hàng {customer_name}")
        
        # Tính tổng công nợ hiện tại
        total_debt = sum(float(invoice.tong_tien or 0 or 0) for invoice in invoices)
        current_paid = sum(float(invoice.tong_tien or 0 or 0) for invoice in invoices 
                          if str(invoice.trang_thai or '' or '') == 'Đã thanh toán')
        
        print(f"🔍 Cập nhật thanh toán cho {customer_name}:")
        print(f"   - Tổng công nợ: {total_debt:,.0f} VND")
        print(f"   - Đã thanh toán hiện tại: {current_paid:,.0f} VND")
        print(f"   - Số tiền thanh toán mới: {paid_amount:,.0f} VND")
        
        # Đầu tiên, đánh dấu tất cả hóa đơn là "Chưa thanh toán"
        for invoice in invoices:
            setattr(invoice, 'trang_thai', 'Chưa thanh toán')
        
        # Sau đó, đánh dấu các hóa đơn là "Đã thanh toán" theo thứ tự cho đến khi đủ số tiền
        remaining_to_pay = paid_amount
        
        for invoice in invoices:
            invoice_amount = float(invoice.tong_tien or 0 or 0)
            
            print(f"   - Xử lý hóa đơn: {invoice_amount:,.0f} VND, Còn lại: {remaining_to_pay:,.0f} VND")
            
            if remaining_to_pay >= invoice_amount:
                # Đánh dấu hóa đơn này là "Đã thanh toán"
                setattr(invoice, 'trang_thai', 'Đã thanh toán')
                remaining_to_pay -= invoice_amount
                print(f"     ✅ Đánh dấu 'Đã thanh toán'")
            else:
                # Số tiền còn lại không đủ để thanh toán hóa đơn này
                # Đánh dấu hóa đơn này là "Đã thanh toán một phần"
                setattr(invoice, 'trang_thai', f'Đã thanh toán {remaining_to_pay:,.0f} VND')
                remaining_to_pay = 0
                print(f"     ✅ Đánh dấu 'Đã thanh toán một phần: {remaining_to_pay:,.0f} VND'")
                break
        
        print("💾 Đang commit database...")
        db.commit()
        print("✅ Đã commit database")
        
        # Debug: Kiểm tra trạng thái sau khi commit
        print(f"🔍 Kiểm tra trạng thái sau khi commit:")
        for invoice in invoices:
            invoice_amount = float(invoice.tong_tien or 0 or 0)
            invoice_status = str(invoice.trang_thai or '' or '')
            print(f"   - Hóa đơn: {invoice_amount:,.0f} VND, Trạng thái: '{invoice_status}'")
        
        # Tính lại số tiền còn nợ
        new_paid = 0
        for invoice in invoices:
            status = str(invoice.trang_thai or '' or '')
            if status == 'Đã thanh toán':
                new_paid += float(invoice.tong_tien or 0 or 0)
            elif 'Đã thanh toán' in status and 'VND' in status:
                # Trích xuất số tiền từ trạng thái "Đã thanh toán X VND"
                try:
                    import re
                    match = re.search(r'Đã thanh toán ([\d,]+) VND', status)
                    if match:
                        paid_str = match.group(1).replace(',', '')
                        paid_amount = float(paid_str)
                        new_paid += paid_amount
                        print(f"     💰 Trích xuất số tiền đã thanh toán: {paid_amount:,.0f} VND")
                except:
                    print(f"     ⚠️ Không thể trích xuất số tiền từ trạng thái: {status}")
        
        remaining_debt = total_debt - new_paid
        
        print(f"📊 Kết quả cuối cùng:")
        print(f"   - Tổng công nợ: {total_debt:,.0f} VND")
        print(f"   - Đã thanh toán: {new_paid:,.0f} VND")
        print(f"   - Còn nợ: {remaining_debt:,.0f} VND")
        
        # Cập nhật bảng debts để đồng bộ với frontend
        try:
            from ..models import Debt
            debt_record = db.query(Debt).filter(Debt.customer_name == customer_name).first()
            
            if debt_record:
                # Cập nhật record hiện có
                setattr(debt_record, 'paid_amount', new_paid)
                setattr(debt_record, 'remaining_debt', remaining_debt)
                setattr(debt_record, 'status', 'Hết nợ' if remaining_debt <= 0 else 'Còn nợ')
                if new_paid > 0:
                    setattr(debt_record, 'last_payment_date', datetime.now())
                print(f"✅ Đã cập nhật bảng debts cho {customer_name}")
            else:
                # Tạo record mới nếu chưa có
                debt_record = Debt(
                    customer_name=customer_name,
                    total_debt=total_debt,
                    paid_amount=new_paid,
                    remaining_debt=remaining_debt,
                    status='Hết nợ' if remaining_debt <= 0 else 'Còn nợ',
                    created_at=datetime.now()
                )
                db.add(debt_record)
                print(f"✅ Đã tạo record mới trong bảng debts cho {customer_name}")
            
            # Commit thay đổi bảng debts
            db.commit()
            print(f"✅ Đã commit cập nhật bảng debts")
            
        except Exception as e:
            print(f"⚠️ Lỗi cập nhật bảng debts: {e}")
            # Không rollback vì hóa đơn đã được cập nhật thành công
        
        return {
            'success': True,
            'data': {
                'customer_name': customer_name,
                'total_debt': total_debt,
                'paid_amount': new_paid,
                'remaining_debt': remaining_debt
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")

@router.post("/", response_model=ReportOut)
def create_report(payload: ReportCreate, db: Session = Depends(get_db)):
    report = Report(
        ten_bao_cao=payload.ten_bao_cao,
        loai_bao_cao=payload.loai_bao_cao,
        tu_ngay=payload.tu_ngay,
        den_ngay=payload.den_ngay,
        du_lieu=payload.du_lieu,
        tong_doanh_thu=payload.tong_doanh_thu,
        tong_so_luong_ban=payload.tong_so_luong_ban,
        tong_so_luong_con_lai=payload.tong_so_luong_con_lai,
        trang_thai=payload.trang_thai
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report

@router.get("/{report_id}", response_model=ReportOut)
def get_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(Report).get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Không tìm thấy báo cáo")
    return report

@router.put("/{report_id}", response_model=ReportOut)
def update_report(report_id: int, payload: ReportUpdate, db: Session = Depends(get_db)):
    report = db.query(Report).get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Không tìm thấy báo cáo")
    
    if payload.ten_bao_cao is not None: report.ten_bao_cao = payload.ten_bao_cao
    if payload.loai_bao_cao is not None: report.loai_bao_cao = payload.loai_bao_cao
    if payload.tu_ngay is not None: report.tu_ngay = payload.tu_ngay
    if payload.den_ngay is not None: report.den_ngay = payload.den_ngay
    if payload.du_lieu is not None: report.du_lieu = payload.du_lieu
    if payload.tong_doanh_thu is not None: report.tong_doanh_thu = payload.tong_doanh_thu
    if payload.tong_so_luong_ban is not None: report.tong_so_luong_ban = payload.tong_so_luong_ban
    if payload.tong_so_luong_con_lai is not None: report.tong_so_luong_con_lai = payload.tong_so_luong_con_lai
    if payload.trang_thai is not None: report.trang_thai = payload.trang_thai
    
    db.commit()
    db.refresh(report)
    return report

@router.delete("/{report_id}")
def delete_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(Report).get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Không tìm thấy báo cáo")
    
    db.delete(report)
    db.commit()
    return {"success": True}

@router.get("/revenue-by-product")
def get_revenue_by_product(from_date: str, to_date: str, db: Session = Depends(get_db)):
    """
    Lấy báo cáo doanh thu theo sản phẩm từ from_date đến to_date
    """
    try:
        # Parse dates
        start_date = datetime.strptime(from_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(to_date, "%Y-%m-%d").date()
        
        # Validate date range
        if (end_date - start_date).days > 31:
            raise HTTPException(status_code=400, detail="Khoảng thời gian tối đa là 31 ngày")
        
        if start_date > end_date:
            raise HTTPException(status_code=400, detail="Ngày bắt đầu phải nhỏ hơn ngày kết thúc")
        
        # Get orders in date range (không bị hủy)
        orders = db.query(Order).filter(
            Order.ngay_tao.between(start_date, end_date),
            Order.trang_thai != 'Đã hủy'
        ).all()
        
        # Get products to map sp_banggia to product info
        products = db.query(Product).all()
        product_map = {p.ma_sp: p for p in products}
        
        # Group orders by product
        product_revenue = {}
        for order in orders:
            sp_code = order.sp_banggia or None
            if sp_code:
                product = product_map.get(sp_code)
                if product:
                    product_key = sp_code
                    if product_key not in product_revenue:
                        product_revenue[product_key] = {
                            'ten_sp': product.ten_sp or None,
                            'nhom_sp': product.nhom_sp or None or 'Chưa phân loại',
                            'total_quantity': 0,
                            'total_revenue': 0
                        }
                    
                    # Tính doanh thu từ hóa đơn đã thanh toán
                    # Tìm hóa đơn tương ứng với đơn hàng này
                    invoice = db.query(Invoice).filter(
                        Invoice.ngay_hd.between(start_date, end_date),
                        Invoice.trang_thai == 'Đã thanh toán'
                    ).first()
                    
                    if invoice:
                        # Tính doanh thu dựa trên tỷ lệ đơn hàng
                        order_total = order.tong_tien or 0
                        order_revenue = float(order_total or 0)
                        product_revenue[product_key]['total_revenue'] += order_revenue
                    
                    product_revenue[product_key]['total_quantity'] += int(order.so_luong or 0 or 0)
        
        # Convert to list format
        product_list = []
        for i, (product_code, data) in enumerate(product_revenue.items(), 1):
            product_list.append({
                'stt': i,
                'ten_sp': data['ten_sp'],
                'nhom_sp': data['nhom_sp'],
                'total_quantity': data['total_quantity'],
                'total_revenue': data['total_revenue']
            })
        
        # Calculate chart data (daily revenue for the chart)
        revenue_data = {}
        invoices = db.query(Invoice).filter(
            Invoice.ngay_hd.between(start_date, end_date),
            Invoice.trang_thai == 'Đã thanh toán'
        ).all()
        
        for invoice in invoices:
            date_key = invoice.ngay_hd.strftime("%Y-%m-%d")
            if date_key not in revenue_data:
                revenue_data[date_key] = 0
            revenue_data[date_key] += float(invoice.tong_tien or 0 or 0)
        
        # Generate date range for chart
        date_range = []
        current_date = start_date
        while current_date <= end_date:
            date_range.append(current_date)
            current_date += timedelta(days=1)
        
        chart_data = {
            'labels': [date.strftime("%d/%m/%Y") for date in date_range],
            'revenue': [revenue_data.get(date.strftime("%Y-%m-%d"), 0) for date in date_range]
        }
        
        # Calculate totals
        total_revenue = sum(data['total_revenue'] for data in product_list)
        total_quantity = sum(data['total_quantity'] for data in product_list)
        
        return {
            'success': True,
            'data': {
                'products': product_list,
                'chart_data': chart_data,
                'summary': {
                    'total_revenue': total_revenue,
                    'total_quantity': total_quantity,
                    'date_range': {
                        'from_date': from_date,
                        'to_date': to_date,
                        'total_days': len(date_range)
                    }
                }
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Định dạng ngày không hợp lệ: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")
