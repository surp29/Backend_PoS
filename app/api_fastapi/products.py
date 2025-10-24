from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..database import get_db
from ..models import Product, ProductGroup, OrderItem
from ..schemas_fastapi import ProductOut, ProductCreate, ProductUpdate


router = APIRouter(prefix="/products", tags=["products"])


@router.get("/")
def list_products(db: Session = Depends(get_db)):
    # Tránh lỗi cột thiếu do schema cũ: chỉ select các cột đang tồn tại
    result = db.execute(text(
        """
        SELECT id, ma_sp, ten_sp, nhom_sp, so_luong, gia_ban, gia_chung, gia_von, don_vi, trang_thai, mo_ta
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
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    # Handle field mapping from frontend
    # Frontend sends 'code' but backend expects 'ma_sp'
    ma_sp = payload.ma_sp
    if payload.code is not None:
        ma_sp = payload.code
    
    # Frontend sends 'name' but backend expects 'ten_sp'
    ten_sp = payload.ten_sp
    if payload.name is not None:
        ten_sp = payload.name
    
    # Frontend sends 'group' but backend expects 'nhom_sp'
    nhom_sp = payload.nhom_sp
    if payload.group is not None:
        nhom_sp = payload.group
    
    # Frontend sends 'cost_price' but backend expects 'gia_von'
    gia_von = payload.gia_von
    if payload.cost_price is not None:
        gia_von = payload.cost_price
    
    # Frontend sends 'price' but backend expects 'gia_ban'
    gia_ban = payload.gia_ban
    if payload.price is not None:
        gia_ban = payload.price
    
    # Frontend sends 'quantity' but backend expects 'so_luong'
    so_luong = payload.so_luong
    if payload.quantity is not None:
        so_luong = payload.quantity
    
    # Frontend sends 'unit' but backend expects 'don_vi'
    don_vi = payload.don_vi or 'cái'
    if payload.unit is not None:
        don_vi = payload.unit
    
    # Frontend sends 'description' but backend expects 'mo_ta'
    mo_ta = payload.mo_ta
    if payload.description is not None:
        mo_ta = payload.description
    
    # Validate required fields
    if not ma_sp:
        raise HTTPException(status_code=400, detail="Mã sản phẩm không được để trống")
    if not ten_sp:
        raise HTTPException(status_code=400, detail="Tên sản phẩm không được để trống")
    
    # Xử lý nhom_sp để đảm bảo lưu dưới dạng tên nhóm đơn giản
    if nhom_sp:
        # Nếu nhom_sp là JSON string, trích xuất ten_nhom
        if nhom_sp.startswith('{') and nhom_sp.endswith('}'):
            try:
                import json
                nhom_data = json.loads(nhom_sp)
                nhom_sp = nhom_data.get('ten_nhom', nhom_sp)
            except:
                pass  # Giữ nguyên nếu không parse được JSON
    
    p = Product(
        ma_sp=ma_sp,
        ten_sp=ten_sp,
        nhom_sp=nhom_sp,  # Lưu tên nhóm đã được xử lý
        so_luong=so_luong or 0,
        gia_ban=gia_ban or 0,
        gia_chung=payload.gia_chung,  # Lưu giá chung vào Product
        gia_von=gia_von or 0.0,  # Cost price field
        don_vi=don_vi,  # Unit field
        trang_thai=payload.trang_thai,
        mo_ta=mo_ta,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return {"success": True, "id": p.id}


@router.put("/{product_id}")
def update_product(product_id: int, payload: ProductUpdate, db: Session = Depends(get_db)):
    p = db.query(Product).get(product_id)
    if not p:
        raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm")
    
    # Handle field mapping from frontend
    # Frontend sends 'code' but backend expects 'ma_sp'
    if payload.code is not None:
        p.ma_sp = payload.code
    
    # Frontend sends 'name' but backend expects 'ten_sp'
    if payload.name is not None:
        p.ten_sp = payload.name
    
    # Frontend sends 'group' but backend expects 'nhom_sp'
    if payload.group is not None:
        nhom_sp = payload.group
        if nhom_sp.startswith('{') and nhom_sp.endswith('}'):
            try:
                import json
                nhom_data = json.loads(nhom_sp)
                nhom_sp = nhom_data.get('ten_nhom', nhom_sp)
            except:
                pass
        p.nhom_sp = nhom_sp
    
    # Frontend sends 'cost_price' but backend expects 'gia_von'
    if payload.cost_price is not None:
        p.gia_von = payload.cost_price
    
    # Frontend sends 'price' but backend expects 'gia_ban'
    if payload.price is not None:
        p.gia_ban = payload.price
    
    # Frontend sends 'quantity' but backend expects 'so_luong'
    if payload.quantity is not None:
        p.so_luong = payload.quantity
    
    # Frontend sends 'unit' but backend expects 'don_vi'
    if payload.unit is not None:
        p.don_vi = payload.unit
    
    # Frontend sends 'description' but backend expects 'mo_ta'
    if payload.description is not None:
        p.mo_ta = payload.description
    
    # Handle original field names
    gia_von = payload.gia_von
    if payload.cost_price is not None:
        gia_von = payload.cost_price
    
    don_vi = payload.don_vi
    if payload.unit is not None:
        don_vi = payload.unit
    
    if payload.nhom_sp is not None:
        # Xử lý nhom_sp để đảm bảo lưu dưới dạng tên nhóm đơn giản
        nhom_sp = payload.nhom_sp
        if nhom_sp:
            # Nếu nhom_sp là JSON string, trích xuất ten_nhom
            if nhom_sp.startswith('{') and nhom_sp.endswith('}'):
                try:
                    import json
                    nhom_data = json.loads(nhom_sp)
                    nhom_sp = nhom_data.get('ten_nhom', nhom_sp)
                except:
                    pass  # Giữ nguyên nếu không parse được JSON
        # Sử dụng setattr để tránh lỗi linter với Column[str]
        setattr(p, 'nhom_sp', nhom_sp)
    if payload.ma_sp is not None:
        p.ma_sp = payload.ma_sp
    if payload.ten_sp is not None:
        p.ten_sp = payload.ten_sp
    if payload.so_luong is not None:
        p.so_luong = payload.so_luong
    if payload.gia_ban is not None:
        p.gia_ban = payload.gia_ban
    if payload.gia_chung is not None:
        p.gia_chung = payload.gia_chung  # Lưu giá chung trực tiếp vào Product
    if gia_von is not None:
        p.gia_von = gia_von  # Cost price field
    if don_vi is not None:
        p.don_vi = don_vi  # Unit field
    if payload.trang_thai is not None:
        p.trang_thai = payload.trang_thai
    if payload.mo_ta is not None:
        p.mo_ta = payload.mo_ta
    db.commit()
    return {"success": True}


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


