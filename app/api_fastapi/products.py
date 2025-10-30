from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..database import get_db
from ..models import Product, ProductGroup, OrderItem
from ..schemas_fastapi import ProductOut, ProductCreate, ProductUpdate
from ..logger import log_info, log_success, log_error, log_warning
from ..services.products import save_uploaded_file, validate_product_fields
import os
from typing import Optional


router = APIRouter(prefix="/products", tags=["products"])

# Configure upload directory
UPLOAD_DIR = "static/images/products"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("/")
def list_products(db: Session = Depends(get_db)):
    # Tránh lỗi cột thiếu do schema cũ: chỉ select các cột đang tồn tại
    result = db.execute(text(
        """
        SELECT id, ma_sp, ten_sp, nhom_sp, so_luong, gia_ban, gia_chung, gia_von, don_vi, trang_thai, mo_ta, image_url
        FROM products
        ORDER BY id ASC
        """
    ))
    products = []
    for row in result.mappings():
        # Xử lý nhom_sp để đảm bảo hiển thị đúng
        nhom_sp = row.get("nhom_sp")
        if nhom_sp:
            # Nếu nhom_sp là JSON string, trích xuất ten_nhom
            if nhom_sp.startswith('{') and nhom_sp.endswith('}'):
                try:
                    import json
                    nhom_data = json.loads(nhom_sp)
                    nhom_sp = nhom_data.get('ten_nhom', nhom_sp)
                except:
                    pass  # Giữ nguyên nếu không parse được JSON
        
        products.append({
            "id": row.get("id"),
            "ma_sp": row.get("ma_sp"),
            "ten_sp": row.get("ten_sp"),
            "nhom_sp": nhom_sp,
            "so_luong": int(row.get("so_luong") or 0),
            "gia_ban": float(row.get("gia_ban") or 0.0),
            "gia_chung": float(row.get("gia_chung") or 0.0),
            "gia_von": float(row.get("gia_von") or 0.0),  # Cost price field
            "don_vi": row.get("don_vi") or "cái",  # Unit field
            "trang_thai": row.get("trang_thai"),
            "mo_ta": row.get("mo_ta"),
            "image_url": row.get("image_url"),  # Image URL
            # Add cost_price alias for frontend compatibility
            "cost_price": float(row.get("gia_von") or 0.0),
        })
    return {"success": True, "products": products}


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm")
    return product


@router.get("/search")
def search_products(q: str, db: Session = Depends(get_db)):
    rows = db.query(Product).filter(Product.ten_sp.ilike(f"%{q}%")).all()
    # Định dạng giống FE kỳ vọng: { products: [...] }
    return {"products": rows}


@router.post("/")
async def create_product(
    code: Optional[str] = Form(None),
    name: Optional[str] = Form(None),
    group: Optional[str] = Form(None),
    cost_price: Optional[float] = Form(None),
    price: Optional[float] = Form(None),
    quantity: Optional[int] = Form(None),
    unit: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    log_info("CREATE_PRODUCT", f"Tạo sản phẩm mới: {code} - {name}")
    try:
        validate_product_fields(code, name)
        image_url = None
        if image:
            image_url = save_uploaded_file(image)
            log_info("CREATE_PRODUCT", f"Đã upload ảnh: {image_url}")
        p = Product(
            ma_sp=code,
            ten_sp=name,
            nhom_sp=group or '',
            so_luong=quantity or 0,
            gia_ban=price or 0,
            gia_chung=0,
            gia_von=cost_price or 0.0,
            don_vi=unit or 'cái',
            trang_thai="active",
            mo_ta=description or '',
            image_url=image_url
        )
        db.add(p)
        db.commit()
        db.refresh(p)
        log_success("CREATE_PRODUCT", f"Tạo sản phẩm thành công: {code} - {name} (ID: {p.id})")
        return {"success": True, "id": p.id}
    except HTTPException:
        raise
    except Exception as e:
        log_error("CREATE_PRODUCT", f"Lỗi khi tạo sản phẩm {code}", error=e)
        raise HTTPException(status_code=500, detail=f"Lỗi khi tạo sản phẩm: {str(e)}")


@router.put("/{product_id}")
async def update_product(
    product_id: int,
    code: Optional[str] = Form(None),
    name: Optional[str] = Form(None),
    group: Optional[str] = Form(None),
    cost_price: Optional[float] = Form(None),
    price: Optional[float] = Form(None),
    quantity: Optional[int] = Form(None),
    unit: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    p = db.query(Product).get(product_id)
    if not p:
        raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm")
    
    # Update fields
    if code is not None:
        p.ma_sp = code
    if name is not None:
        p.ten_sp = name
    if group is not None:
        p.nhom_sp = group
    if cost_price is not None:
        p.gia_von = cost_price
    if price is not None:
        p.gia_ban = price
    if quantity is not None:
        p.so_luong = quantity
    if unit is not None:
        p.don_vi = unit
    if description is not None:
        p.mo_ta = description
    
    # Handle image upload
    if image:
        image_url = save_uploaded_file(image)
        if image_url:
            p.image_url = image_url
            log_info("UPDATE_PRODUCT", f"Đã cập nhật ảnh: {image_url}")
    
    db.commit()
    db.refresh(p)
    
    log_success("UPDATE_PRODUCT", f"Cập nhật sản phẩm thành công: {p.ma_sp} - {p.ten_sp} (ID: {product_id})")
    return {"success": True, "id": p.id}


@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    p = db.query(Product).get(product_id)
    if not p:
        raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm")
    # Xóa các bản ghi phụ thuộc nếu có (chi tiết đơn hàng)
    # Không còn liên kết với bảng giá
    try:
        db.query(OrderItem).filter(OrderItem.product_id == product_id).delete()
    except Exception:
        pass
    db.delete(p)
    db.commit()
    return {"success": True}


