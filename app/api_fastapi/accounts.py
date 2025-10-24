from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Account
from ..schemas_fastapi import AccountOut, AccountCreate, AccountUpdate


router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("/", response_model=list[AccountOut])
def list_accounts(db: Session = Depends(get_db)):
    rows = db.query(Account).all()
    return [AccountOut.model_validate(row) for row in rows]


@router.get("/{account_id}", response_model=AccountOut)
def get_account(account_id: int, db: Session = Depends(get_db)):
    row = db.query(Account).get(account_id)
    if not row:
        raise HTTPException(status_code=404, detail="Không tìm thấy khách hàng")
    return AccountOut.model_validate(row)


@router.post("/")
def create_account(payload: AccountCreate, db: Session = Depends(get_db)):
    acc = Account(
        ten_tk=payload.ten_tk,
        tk_no=payload.tk_no,
        tk_co=payload.tk_co,
        email=payload.email,
        so_dt=payload.so_dt,
        dia_chi=payload.dia_chi,
        trang_thai=payload.trang_thai,
    )
    db.add(acc)
    db.commit()
    db.refresh(acc)
    return {"success": True, "id": acc.id}


@router.put("/{account_id}")
def update_account(account_id: int, payload: AccountUpdate, db: Session = Depends(get_db)):
    acc = db.query(Account).get(account_id)
    if not acc:
        raise HTTPException(status_code=404, detail="Không tìm thấy khách hàng")
    if payload.ten_tk is not None:
        acc.ten_tk = payload.ten_tk
    if payload.tk_no is not None:
        acc.tk_no = payload.tk_no
    if payload.tk_co is not None:
        acc.tk_co = payload.tk_co
    if payload.email is not None:
        acc.email = payload.email
    if payload.so_dt is not None:
        acc.so_dt = payload.so_dt
    if payload.dia_chi is not None:
        acc.dia_chi = payload.dia_chi
    if payload.trang_thai is not None:
        acc.trang_thai = payload.trang_thai
    db.commit()
    return {"success": True}


@router.delete("/{account_id}")
def delete_account(account_id: int, db: Session = Depends(get_db)):
    acc = db.query(Account).get(account_id)
    if not acc:
        raise HTTPException(status_code=404, detail="Không tìm thấy khách hàng")
    db.delete(acc)
    db.commit()
    return {"success": True}


