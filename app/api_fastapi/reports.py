from fastapi import APIRouter

router = APIRouter(prefix="/reports", tags=["reports"]) 

@router.get("/revenue")
def revenue_report():
    return {
        "summary": {
            "total_revenue": 0,
            "total_quantity_sold": 0,
            "total_quantity_remaining": 0,
            "total_products": 0
        },
        "items": []
    }

@router.get("/debt")
def debt_report():
    return {
        "summary": {
            "total_debt": 0,
            "overdue_debt": 0,
            "debt_customers": 0,
            "avg_debt": 0
        },
        "items": []
    }
