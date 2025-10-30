from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Order, Product, Account
from sqlalchemy import or_
from ..schemas_fastapi import OrderOut, OrderCreate, OrderUpdate
from ..logger import log_info, log_success, log_error, log_warning
from fastapi import Body
from ..services.orders import create_order_service


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
    return db.query(Order).all()


@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: int, db: Session = Depends(get_db)):
    o = db.query(Order).get(order_id)
    if not o:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn hàng")
    return o


@router.get("/search")
def search_orders(customer_id: int | None = None, q: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Order)
    if customer_id is not None:
        # Map id -> thông tin tài khoản và lọc linh hoạt theo thong_tin_kh
        acc = None
        try:
            acc = db.query(Account).get(int(customer_id))
        except Exception:
            acc = None
        if acc:
            name = (acc.ten_tk or '').strip()
            tk_no = (acc.tk_no or '').strip()
            tk_co = (acc.tk_co or '').strip()
            composite = f"{tk_no} - {tk_co} - {name}".strip()
            patterns = [
                Order.thong_tin_kh.ilike(f"%{name}%") if name else None,
                Order.thong_tin_kh.ilike(f"%{composite}%") if composite else None,
                Order.thong_tin_kh.ilike(f"%{tk_no}%") if tk_no else None,
                Order.thong_tin_kh.ilike(f"%{tk_co}%") if tk_co else None,
            ]
            patterns = [p for p in patterns if p is not None]
            if patterns:
                query = query.filter(or_(*patterns))
    if q:
        ql = f"%{q}%"
        query = query.filter((Order.ma_don_hang.ilike(ql)) | (Order.trang_thai.ilike(ql)))
    # Chỉ trả về đơn hàng Hoàn thành
    query = query.filter(Order.trang_thai.ilike('%Hoàn thành%'))
    results = query.order_by(Order.id.desc()).all()
    out = []
    for o in results:
        # xác định loại SP dựa trên sp_banggia và bảng products
        loai = 'Khác'
        if o.sp_banggia or None:
            p = db.query(Product).filter(Product.ma_sp == o.sp_banggia or '').first()
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


@router.post("/")
def create_order(payload: OrderCreate, db: Session = Depends(get_db)):
    log_info("CREATE_ORDER", f"Tạo đơn hàng mới: {payload.ma_don_hang} - Khách hàng: {payload.thong_tin_kh}")
    log_info("CREATE_ORDER", f"Payload details: sp_banggia={payload.sp_banggia}, so_luong={payload.so_luong}, tong_tien={payload.tong_tien}")
    try:
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
            ngay_tao=payload.ngay_tao,
            ma_co_quan_thue=payload.ma_co_quan_thue,
            so_luong=payload.so_luong,
            tong_tien=computed_total,
            hinh_thuc_tt=payload.hinh_thuc_tt,
            trang_thai=payload.trang_thai,
        )
        db.add(o)
        db.commit()
        db.refresh(o)
        # Trừ kho nếu là sản phẩm
        if is_product and product and payload.so_luong:
            current_qty = int(getattr(product, 'so_luong', 0) or 0)
            new_qty = max(current_qty - int(payload.so_luong or 0), 0)
            setattr(product, 'so_luong', new_qty)
            setattr(product, 'trang_thai', 'Còn hàng' if new_qty > 0 else 'Hết hàng')
            db.commit()
            log_success("CREATE_ORDER", f"Đã trừ số lượng sản phẩm {payload.sp_banggia}: {new_qty} còn lại")
        log_success("CREATE_ORDER", f"Tạo đơn hàng thành công: {payload.ma_don_hang} - Tổng tiền: {computed_total:,.0f} VND")
        return {"success": True, "id": o.id}
    except HTTPException:
        raise
    except Exception as e:
        log_error("CREATE_ORDER", f"Lỗi khi tạo đơn hàng {payload.ma_don_hang}", error=e)
        raise HTTPException(status_code=500, detail=f"Lỗi khi tạo đơn hàng: {str(e)}")


@router.put("/{order_id}")
def update_order(order_id: int, payload: OrderUpdate, db: Session = Depends(get_db)):
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
    if payload.hinh_thuc_tt is not None: o.hinh_thuc_tt = payload.hinh_thuc_tt
    if payload.trang_thai is not None: o.trang_thai = payload.trang_thai
    
    # Tính lại tổng tiền nếu đơn không bị hủy
    if new_quantity is not None and not is_cancelled(new_status):
        if new_is_product and new_product:
            unit_price = float(new_product.gia_chung or 0 or 0)
            o.tong_tien = unit_price * int(new_quantity or 0)
        elif new_is_action:
            # Với hành động, sử dụng giá từ payload hoặc giá mặc định
            if new_price_item:
                unit_price = float(new_price_item.gia_chung or 0 or 0)
            else:
                # Nếu không có price_item, sử dụng giá từ payload hoặc giá mặc định
                unit_price = float(payload.tong_tien or o.tong_tien or 0) / max(int(new_quantity or 1), 1)
            o.tong_tien = unit_price * int(new_quantity or 0)
    elif payload.tong_tien is not None:
        o.tong_tien = payload.tong_tien
    
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
        
        db.commit()
    
    return {"success": True}


@router.delete("/{order_id}")
def delete_order(order_id: int, db: Session = Depends(get_db)):
    o = db.query(Order).get(order_id)
    if not o:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn hàng")
    
    # CHỈ hoàn trả số lượng sản phẩm trước khi xóa đơn hàng (không hoàn trả cho hành động)
    if o.sp_banggia or None and o.so_luong or None:
        product = db.query(Product).filter(Product.ma_sp == o.sp_banggia or '').first()
        if product:
            # Chỉ hoàn trả nếu đây là sản phẩm (có trong bảng products)
            current_qty = int(product.so_luong or 0 or 0)
            order_qty = int(o.so_luong or 0 or 0)
            setattr(product, 'so_luong', current_qty + order_qty)
            setattr(product, 'trang_thai', 'Còn hàng' if (current_qty + order_qty) > 0 else 'Hết hàng')
            db.commit()
    
    db.delete(o)
    db.commit()
    return {"success": True}


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




