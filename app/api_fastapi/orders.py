from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Order, OrderItem, Product, Account, Warehouse
from sqlalchemy import or_
from ..schemas_fastapi import OrderOut, OrderCreate, OrderUpdate
from ..logger import log_info, log_success, log_error, log_warning
from fastapi import Body
from ..services.orders import create_order_service
from ..services.general_diary import create_general_diary_entry
from ..services.auth_helper import get_username_from_request


def is_cancelled(status: str | None) -> bool:
    s = (status or '').strip().lower()
    return s in ('đã hủy', 'da huy', 'hủy', 'huy', 'canceled', 'cancelled')


router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("/check-duplicate")
def check_duplicate(ma_don_hang: str = Query(..., description="Mã đơn hàng cần kiểm tra"), db: Session = Depends(get_db)):
    code = (ma_don_hang or "").strip()
    if not code:
        return {"exists": False}
    exists = db.query(Order).filter(Order.ma_don_hang == code).first() is not None
    return {"exists": exists}


@router.get("/", response_model=list[OrderOut])
def list_orders(db: Session = Depends(get_db)):
    orders = db.query(Order).all()
    return [OrderOut.model_validate(o).model_dump() for o in orders]


@router.get("/search")
def search_orders(customer_id: int | None = None, customer_name: str | None = None, q: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Order)
    
    log_info("SEARCH_ORDERS", f"Search params: customer_id={customer_id}, customer_name={customer_name}, q={q}")
    
    # Tìm theo customer_id hoặc customer_name
    customer_filters = []
    
    # Nếu có customer_name, ưu tiên tìm theo tên trực tiếp
    if customer_name:
        customer_name_clean = (customer_name or '').strip()
        if customer_name_clean and customer_name_clean != 'Khách vãng lai':
            customer_filters.append(Order.thong_tin_kh.ilike(f"%{customer_name_clean}%"))
            log_info("SEARCH_ORDERS", f"Added customer_name filter: {customer_name_clean}")
    
    # Nếu có customer_id, map id -> thông tin tài khoản và lọc theo thong_tin_kh
    if customer_id is not None:
        acc = None
        try:
            acc = db.query(Account).get(int(customer_id))
        except Exception:
            acc = None
        if acc:
            name = (acc.ten_tk or '').strip()
            ma_kh = (acc.ma_khach_hang or '').strip()
            log_info("SEARCH_ORDERS", f"Found account: id={acc.id}, ten_tk={name}, ma_khach_hang={ma_kh}")
            if name:
                customer_filters.append(Order.thong_tin_kh.ilike(f"%{name}%"))
                log_info("SEARCH_ORDERS", f"Added account name filter: {name}")
            if ma_kh:
                customer_filters.append(Order.thong_tin_kh.ilike(f"%{ma_kh}%"))
                log_info("SEARCH_ORDERS", f"Added account code filter: {ma_kh}")
        else:
            log_warning("SEARCH_ORDERS", f"Account not found for customer_id={customer_id}")
    
    # Áp dụng filter khách hàng (OR logic - tìm theo bất kỳ điều kiện nào khớp)
    if customer_filters:
        query = query.filter(or_(*customer_filters))
        log_info("SEARCH_ORDERS", f"Applied {len(customer_filters)} customer filters")
    else:
        log_warning("SEARCH_ORDERS", "No customer filters applied")
    
    # Tìm kiếm theo query string nếu có
    if q:
        ql = f"%{q}%"
        query = query.filter((Order.ma_don_hang.ilike(ql)) | (Order.trang_thai.ilike(ql)))
    
    # Chỉ trả về đơn hàng Hoàn thành (hỗ trợ nhiều format: hoan_thanh, Hoàn thành, HOÀN THÀNH)
    # Trong database, trạng thái được lưu là 'hoan_thanh' (chữ thường, không dấu)
    query = query.filter(
        or_(
            Order.trang_thai.ilike('%hoan_thanh%'),
            Order.trang_thai.ilike('%Hoàn thành%'),
            Order.trang_thai.ilike('%HOÀN THÀNH%'),
            Order.trang_thai.ilike('%hoàn thành%'),
            Order.trang_thai.ilike('%hoan thanh%')
        )
    )
    
    results = query.order_by(Order.id.desc()).all()
    log_info("SEARCH_ORDERS", f"Found {len(results)} completed orders")
    out = []
    for o in results:
        # xác định loại SP dựa trên sp_banggia và bảng products
        loai = 'Khác'
        if o.sp_banggia:
            p = db.query(Product).filter(Product.ma_sp == o.sp_banggia).first()
            loai = 'Sản phẩm' if p is not None else 'Hành động (Bảng giá)'
        out.append({
            'id': o.id,
            'ma_don_hang': o.ma_don_hang,
            'tong_tien': o.tong_tien,
            'trang_thai': o.trang_thai,
            'sp_banggia': o.sp_banggia,
            'loai_suy_luan': loai,
        })
    return out


@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: int, db: Session = Depends(get_db)):
    o = db.query(Order).get(order_id)
    if not o:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn hàng")
    return OrderOut.model_validate(o).model_dump()


@router.post("/")
def create_order(payload: OrderCreate, db: Session = Depends(get_db)):
    log_info("CREATE_ORDER", f"Tạo đơn hàng mới: {payload.ma_don_hang} - Khách hàng: {payload.thong_tin_kh}")
    log_info("CREATE_ORDER", f"Payload details: sp_banggia={payload.sp_banggia}, so_luong={payload.so_luong}, tong_tien={payload.tong_tien}")
    try:
        # Validate required fields
        if not payload.ma_don_hang or not payload.ma_don_hang.strip():
            raise HTTPException(status_code=400, detail="Mã đơn hàng không được để trống")
        if not payload.thong_tin_kh or not payload.thong_tin_kh.strip():
            raise HTTPException(status_code=400, detail="Thông tin khách hàng không được để trống")
        
        # Set default ngay_tao if not provided
        from datetime import date
        ngay_tao = payload.ngay_tao if payload.ngay_tao else date.today()
        
        service_res = create_order_service(payload, db)
        is_product = service_res['is_product']
        is_action = service_res['is_action']
        product = service_res['product']
        price_item = service_res['price_item']
        computed_total = service_res['computed_total']
        existing_order = db.query(Order).filter(Order.ma_don_hang == payload.ma_don_hang).first()
        if existing_order:
            log_error("CREATE_ORDER", f"Mã đơn hàng {payload.ma_don_hang} đã tồn tại!")
            raise HTTPException(
                status_code=400,
                detail=f"Mã đơn hàng '{payload.ma_don_hang}' đã tồn tại! Vui lòng chọn mã khác."
            )
        o = Order(
            ma_don_hang=payload.ma_don_hang,
            thong_tin_kh=payload.thong_tin_kh,
            sp_banggia=payload.sp_banggia,
            ngay_tao=ngay_tao,
            ma_co_quan_thue=payload.ma_co_quan_thue,
            so_luong=payload.so_luong or 1,
            tong_tien=computed_total,
            trang_thai=payload.trang_thai or 'cho_xu_ly',
        )
        db.add(o)
        db.commit()
        db.refresh(o)
        # Trừ kho nếu là sản phẩm
        quantity_out = 0
        if is_product and product and payload.so_luong:
            current_qty = int(getattr(product, 'so_luong', 0) or 0)
            quantity_out = int(payload.so_luong or 0)
            new_qty = max(current_qty - quantity_out, 0)
            setattr(product, 'so_luong', new_qty)
            setattr(product, 'trang_thai', 'Còn hàng' if new_qty > 0 else 'Hết hàng')
            
            # Cập nhật warehouse nếu có
            warehouse = db.query(Warehouse).filter(Warehouse.ma_sp == payload.sp_banggia).first()
            if warehouse:
                current_wh_qty = warehouse.so_luong or 0
                new_wh_qty = max(0, current_wh_qty - quantity_out)
                warehouse.so_luong = new_wh_qty
                warehouse.trang_thai = 'Còn hàng' if new_wh_qty > 0 else 'Hết hàng'
            
            db.commit()
            log_success("CREATE_ORDER", f"Đã trừ số lượng sản phẩm {payload.sp_banggia}: {new_qty} còn lại")
        
        # Tự động ghi vào General Diary
        try:
            sp_banggia_display = payload.sp_banggia if payload.sp_banggia else "N/A"
            description = f"Đơn hàng {payload.ma_don_hang} - Khách hàng: {payload.thong_tin_kh} - Sản phẩm: {sp_banggia_display}"
            create_general_diary_entry(
                db=db,
                source="Order",
                total_amount=computed_total or 0.0,
                quantity_out=quantity_out,
                quantity_in=0,
                description=description
            )
            db.commit()
        except Exception as diary_error:
            # Log lỗi nhưng không làm gián đoạn việc tạo order
            log_error("CREATE_ORDER_DIARY", f"Lỗi khi ghi vào General Diary: {str(diary_error)}", error=diary_error)
            # Không rollback vì order đã được tạo thành công
        
        log_success("CREATE_ORDER", f"Tạo đơn hàng thành công: {payload.ma_don_hang} - Tổng tiền: {computed_total:,.0f} VND")
        return {"success": True, "id": o.id}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        log_error("CREATE_ORDER", f"Lỗi khi tạo đơn hàng {payload.ma_don_hang}: {str(e)}", error=e)
        log_error("CREATE_ORDER", f"Traceback: {error_trace}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi khi tạo đơn hàng: {str(e)}")


@router.put("/{order_id}")
def update_order(order_id: int, payload: OrderUpdate, request: Request, db: Session = Depends(get_db)):
    o = db.query(Order).get(order_id)
    if not o:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn hàng")
    
    # Trạng thái cũ/mới
    old_status = o.trang_thai
    new_status = payload.trang_thai if payload.trang_thai is not None else old_status
    
    # Lưu thông tin cũ để tính toán
    old_quantity = o.so_luong or 0
    old_sp_banggia = o.sp_banggia
    
    # Phân biệt sản phẩm cũ và mới
    old_product = None
    new_product = None
    old_price_item = None
    new_price_item = None
    old_is_product = False
    new_is_product = False
    old_is_action = False
    new_is_action = False
    
    # Kiểm tra loại cũ
    if old_sp_banggia:
        old_product = db.query(Product).filter(Product.ma_sp == old_sp_banggia).first()
        if old_product:
            old_is_product = True
        else:
            old_is_action = True
    
    # Kiểm tra loại mới
    if payload.sp_banggia is not None:
        if payload.sp_banggia:
            new_product = db.query(Product).filter(Product.ma_sp == payload.sp_banggia).first()
            if new_product:
                new_is_product = True
            else:
                new_is_action = True
    else:
        # Giữ nguyên loại cũ
        new_product = old_product
        new_is_product = old_is_product
        new_is_action = old_is_action
    
    # Số lượng mới
    new_quantity = payload.so_luong if payload.so_luong is not None else old_quantity
    
    # CHỈ kiểm tra kho nếu là SẢN PHẨM và đơn mới không bị hủy
    if new_is_product and new_product and new_quantity is not None and not is_cancelled(new_status):
        current_qty = int(new_product.so_luong or 0 or 0)
        if old_is_product and old_product and new_product.id or None == old_product.id or None:
            # Cùng sản phẩm, tính chênh lệch
            quantity_diff = int(new_quantity or 0) - int(old_quantity or 0)
            if quantity_diff > 0 and current_qty < quantity_diff:
                raise HTTPException(status_code=400, detail=f"Số lượng sản phẩm không đủ. Hiện có: {current_qty}, cần thêm: {quantity_diff}")
        else:
            # Sản phẩm khác hoặc từ hành động chuyển sang sản phẩm
            if current_qty < int(new_quantity or 0):
                raise HTTPException(status_code=400, detail=f"Số lượng sản phẩm không đủ. Hiện có: {current_qty}, yêu cầu: {new_quantity}")
    
    # Cập nhật dữ liệu cơ bản
    if payload.ma_don_hang is not None: o.ma_don_hang = payload.ma_don_hang
    if payload.thong_tin_kh is not None: o.thong_tin_kh = payload.thong_tin_kh
    if payload.sp_banggia is not None: o.sp_banggia = payload.sp_banggia
    if payload.ngay_tao is not None: o.ngay_tao = payload.ngay_tao
    if payload.ma_co_quan_thue is not None: o.ma_co_quan_thue = payload.ma_co_quan_thue
    if payload.so_luong is not None: o.so_luong = payload.so_luong
    if payload.trang_thai is not None: o.trang_thai = payload.trang_thai
    
    # Tính lại tổng tiền - ưu tiên tong_tien từ payload nếu có và > 0
    if payload.tong_tien is not None and payload.tong_tien > 0:
        # Nếu payload có tong_tien và > 0, sử dụng giá trị đó
        o.tong_tien = float(payload.tong_tien)
    elif new_quantity is not None and not is_cancelled(new_status):
        # Nếu không có tong_tien từ payload, tính toán từ sản phẩm/số lượng
        if new_is_product and new_product:
            # Try gia_ban first, then gia_chung
            unit_price = float(new_product.gia_ban or 0)
            if unit_price == 0:
                unit_price = float(new_product.gia_chung or 0)
            o.tong_tien = unit_price * int(new_quantity or 0)
        elif new_is_action:
            # Với hành động, sử dụng giá từ payload hoặc giá mặc định
            if new_price_item:
                unit_price = float(new_price_item.gia_chung or 0)
            else:
                # Nếu không có price_item, sử dụng giá từ payload hoặc giá hiện tại
                if payload.tong_tien and payload.tong_tien > 0:
                    unit_price = float(payload.tong_tien) / max(int(new_quantity or 1), 1)
                else:
                    unit_price = float(o.tong_tien or 0) / max(int(new_quantity or 1), 1)
            o.tong_tien = unit_price * int(new_quantity or 0)
    
    db.commit()
    
    # Điều chỉnh kho theo thay đổi trạng thái/sản phẩm/số lượng
    # 1) Nếu chuyển sang Đã hủy: hoàn trả kho sản phẩm cũ (CHỈ CHO SẢN PHẨM)
    if is_cancelled(new_status):
        if old_is_product and old_product:
            old_qty = int(old_product.so_luong or 0 or 0)
            setattr(old_product, 'so_luong', old_qty + int(old_quantity or 0))
            setattr(old_product, 'trang_thai', 'Còn hàng' if (old_qty + int(old_quantity or 0)) > 0 else 'Hết hàng')
            db.commit()
        return {"success": True}
    
    # 2) Nếu từ Đã hủy chuyển về trạng thái hoạt động: cần trừ kho theo số lượng mới (CHỈ CHO SẢN PHẨM)
    if is_cancelled(old_status) and not is_cancelled(new_status):
        if new_is_product and new_product:
            new_stock = int(new_product.so_luong or 0 or 0)
            # Trừ toàn bộ số lượng mới
            new_stock = max(new_stock - int(new_quantity or 0), 0)
            setattr(new_product, 'so_luong', new_stock)
            setattr(new_product, 'trang_thai', 'Còn hàng' if new_stock > 0 else 'Hết hàng')
            db.commit()
        return {"success": True}
    
    # 3) Cả hai đều không bị hủy: xử lý kho (CHỈ CHO SẢN PHẨM)
    if new_quantity is not None:
        # Hoàn trả kho cũ nếu là sản phẩm
        if old_is_product and old_product and (not new_is_product or not new_product or old_product.id or None != new_product.id or None):
            old_qty = int(old_product.so_luong or 0 or 0)
            setattr(old_product, 'so_luong', old_qty + int(old_quantity or 0))
            setattr(old_product, 'trang_thai', 'Còn hàng' if (old_qty + int(old_quantity or 0)) > 0 else 'Hết hàng')
        
        # Trừ kho mới nếu là sản phẩm
        if new_is_product and new_product:
            new_stock = int(new_product.so_luong or 0 or 0)
            if old_is_product and old_product and new_product.id or None == old_product.id or None:
                # Cùng sản phẩm: tính chênh lệch
                quantity_diff = int(new_quantity or 0) - int(old_quantity or 0)
                new_stock = max(new_stock - max(quantity_diff, 0), 0)
            else:
                # Sản phẩm khác: trừ toàn bộ số lượng mới
                new_stock = max(new_stock - int(new_quantity or 0), 0)
            setattr(new_product, 'so_luong', new_stock)
            setattr(new_product, 'trang_thai', 'Còn hàng' if new_stock > 0 else 'Hết hàng')
        
        db.flush()  # Flush để đảm bảo update được thực hiện
    
    # Lấy username từ token
    username = get_username_from_request(request)
    
    # Ghi vào general_diary
    try:
        computed_total = o.tong_tien or 0.0
        description_text = f"Sửa đơn hàng: {o.ma_don_hang} - Khách hàng: {o.thong_tin_kh}"
        create_general_diary_entry(
            db=db,
            source="Order",
            total_amount=float(computed_total),
            quantity_out=0,
            quantity_in=0,
            description=description_text[:255],
            username=username
        )
        db.commit()
    except Exception as diary_error:
        log_error("UPDATE_ORDER_DIARY", f"Lỗi khi ghi vào General Diary: {str(diary_error)}", error=diary_error)
        db.commit()  # Vẫn commit việc update đơn hàng
    
    return {"success": True}


@router.delete("/{order_id}")
def delete_order(order_id: int, request: Request, db: Session = Depends(get_db)):
    try:
        o = db.query(Order).get(order_id)
        if not o:
            raise HTTPException(status_code=404, detail="Không tìm thấy đơn hàng")
        
        # Lấy username từ token
        username = get_username_from_request(request)
        
        # Lưu thông tin đơn hàng trước khi xóa
        order_info = f"{o.ma_don_hang} - Khách hàng: {o.thong_tin_kh}"
        order_total = float(o.tong_tien or 0)
        order_sp_banggia = o.sp_banggia
        order_so_luong = o.so_luong
        
        # CHỈ hoàn trả số lượng sản phẩm trước khi xóa đơn hàng (không hoàn trả cho hành động)
        if order_sp_banggia and order_so_luong:
            product = db.query(Product).filter(Product.ma_sp == order_sp_banggia).first()
            if product:
                # Chỉ hoàn trả nếu đây là sản phẩm (có trong bảng products)
                current_qty = int(product.so_luong or 0)
                order_qty = int(order_so_luong or 0)
                new_qty = current_qty + order_qty
                product.so_luong = new_qty
                product.trang_thai = 'Còn hàng' if new_qty > 0 else 'Hết hàng'
                
                # Cập nhật warehouse nếu có
                warehouse = db.query(Warehouse).filter(Warehouse.ma_sp == order_sp_banggia).first()
                if warehouse:
                    current_wh_qty = warehouse.so_luong or 0
                    new_wh_qty = current_wh_qty + order_qty
                    warehouse.so_luong = new_wh_qty
                    warehouse.trang_thai = 'Còn hàng' if new_wh_qty > 0 else 'Hết hàng'
                
                db.flush()
        
        # Ghi vào general_diary trước khi xóa
        try:
            description_text = f"Xóa đơn hàng: {order_info}"
            create_general_diary_entry(
                db=db,
                source="Order",
                total_amount=order_total,
                quantity_out=0,
                quantity_in=order_so_luong if order_sp_banggia else 0,  # Hoàn trả = nhập lại
                description=description_text[:255],
                username=username
            )
            db.flush()
        except Exception as diary_error:
            log_error("DELETE_ORDER_DIARY", f"Lỗi khi ghi vào General Diary: {str(diary_error)}", error=diary_error)
            # Tiếp tục xóa đơn hàng dù có lỗi ghi diary
        
        # Xóa đơn hàng
        db.delete(o)
        db.commit()
        
        log_success("DELETE_ORDER", f"Đã xóa đơn hàng: {order_info}")
        return {"success": True}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        import traceback
        error_trace = traceback.format_exc()
        log_error("DELETE_ORDER", f"Lỗi khi xóa đơn hàng {order_id}: {str(e)}", error=e)
        log_error("DELETE_ORDER", f"Traceback: {error_trace}")
        raise HTTPException(status_code=500, detail=f"Lỗi khi xóa đơn hàng: {str(e)}")


@router.post("/items")
def add_order_item(payload: dict = Body(...), db: Session = Depends(get_db)):
    # Chấp nhận cả kiểu tên trường cũ từ FE: don_hang/san_pham/thanh_tien
    order_id = payload.get('order_id') or payload.get('don_hang')
    product_id = payload.get('product_id') or payload.get('san_pham')
    so_luong = payload.get('so_luong') or payload.get('quantity') or 1
    don_gia = payload.get('don_gia') or payload.get('unit_price') or 0
    total_price = payload.get('total_price') or payload.get('thanh_tien') or 0
    if not order_id or not product_id:
        raise HTTPException(status_code=422, detail="Thiếu order_id hoặc product_id")
    it = OrderItem(
        order_id=int(order_id),
        product_id=int(product_id),
        so_luong=int(so_luong or 1),
        don_gia=float(don_gia or 0),
        total_price=float(total_price or 0),
    )
    db.add(it)
    db.commit()
    db.refresh(it)
    return {"success": True, "id": it.id}




