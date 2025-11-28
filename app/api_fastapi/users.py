from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..schemas_fastapi import UserOut, UserCreate, UserUpdate
from werkzeug.security import generate_password_hash
from ..services.general_diary import create_general_diary_entry
from ..services.auth_helper import get_username_from_request


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [UserOut.model_validate(u).model_dump() for u in users]


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhân viên")
    return UserOut.model_validate(user).model_dump()


@router.post("/")
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=400, detail="Tên đăng nhập đã tồn tại")
    user = User(
        username=payload.username,
        password=generate_password_hash(payload.password),
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        position=payload.position,
        department=payload.department,
        status=payload.status,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"success": True, "id": user.id}


@router.put("/{user_id}")
def update_user(user_id: int, payload: UserUpdate, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhân viên")
    
    # Lấy username từ token
    username = get_username_from_request(request)
    
    if payload.username is not None:
        if payload.username != user.username and db.query(User).filter(User.username == payload.username).first():
            raise HTTPException(status_code=400, detail="Tên đăng nhập đã tồn tại")
        user.username = payload.username
    if payload.password:
        user.password = generate_password_hash(payload.password)
    if payload.name is not None:
        user.name = payload.name
    if payload.email is not None:
        user.email = payload.email
    if payload.phone is not None:
        user.phone = payload.phone
    if payload.position is not None:
        user.position = payload.position
    if payload.department is not None:
        user.department = payload.department
    if payload.status is not None:
        user.status = payload.status
    
    db.flush()  # Flush để đảm bảo update được thực hiện
    
    # Ghi vào general_diary
    try:
        description_text = f"Sửa nhân viên: {user.username} - {user.name or 'N/A'}"
        create_general_diary_entry(
            db=db,
            source="User",
            total_amount=0.0,
            quantity_out=0,
            quantity_in=0,
            description=description_text[:255],
            username=username
        )
        db.commit()
    except Exception as diary_error:
        from ..logger import log_error
        log_error("UPDATE_USER_DIARY", f"Lỗi khi ghi vào General Diary: {str(diary_error)}", error=diary_error)
        db.commit()  # Vẫn commit việc update nhân viên
    
    return {"success": True}


@router.delete("/{user_id}")
def delete_user(user_id: int, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhân viên")
    if user.username == 'admin':
        raise HTTPException(status_code=400, detail="Không thể xóa tài khoản admin")
    
    # Lấy username từ token
    username = get_username_from_request(request)
    
    # Lưu thông tin nhân viên trước khi xóa
    user_info = f"{user.username} - {user.name or 'N/A'}"
    
    db.delete(user)
    db.flush()  # Flush để đảm bảo xóa được thực hiện
    
    # Ghi vào general_diary
    try:
        description_text = f"Xóa nhân viên: {user_info}"
        create_general_diary_entry(
            db=db,
            source="User",
            total_amount=0.0,
            quantity_out=0,
            quantity_in=0,
            description=description_text[:255],
            username=username
        )
        db.commit()
    except Exception as diary_error:
        from ..logger import log_error
        log_error("DELETE_USER_DIARY", f"Lỗi khi ghi vào General Diary: {str(diary_error)}", error=diary_error)
        db.commit()  # Vẫn commit việc xóa nhân viên
    
    return {"success": True}


