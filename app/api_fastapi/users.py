from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..schemas_fastapi import UserOut, UserCreate, UserUpdate
from werkzeug.security import generate_password_hash


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).all()


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhân viên")
    return user


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
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhân viên")
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
    db.commit()
    return {"success": True}


@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhân viên")
    if user.username == 'admin':
        raise HTTPException(status_code=400, detail="Không thể xóa tài khoản admin")
    db.delete(user)
    db.commit()
    return {"success": True}


