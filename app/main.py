from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine
from .config import Config
from .api_fastapi import (
    products, prices, orders, invoices, users, 
    accounts, reports, product_groups, warehouses, 
    auth, general_diary, areas, shops
)

# Create FastAPI app
app = FastAPI(
    title="PhanMemKeToan API",
    description="API cho phần mềm kế toán chuyên nghiệp",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Initialize database tables (dev environment only)
if Config.ENV == 'development':
    Base.metadata.create_all(bind=engine)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(products.router, prefix="/api", tags=["products"])
app.include_router(prices.router, prefix="/api", tags=["prices"])
app.include_router(orders.router, prefix="/api", tags=["orders"])
app.include_router(invoices.router, prefix="/api", tags=["invoices"])
app.include_router(users.router, prefix="/api", tags=["users"])
app.include_router(accounts.router, prefix="/api", tags=["accounts"])
app.include_router(reports.router, prefix="/api", tags=["reports"])
app.include_router(product_groups.router, prefix="/api", tags=["product_groups"])
app.include_router(warehouses.router, prefix="/api/warehouse", tags=["warehouses"])
app.include_router(shops.router, prefix="/api", tags=["shops"])
app.include_router(areas.router, prefix="/api", tags=["areas"])
app.include_router(auth.router, prefix="/api", tags=["authentication"])
app.include_router(general_diary.router, prefix="/api", tags=["general_diary"])

@app.get("/", tags=["root"])
def read_root():
    """Root endpoint"""
    return {
        "message": "PhanMemKeToan API is running",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", tags=["health"])
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "PhanMemKeToan API",
        "version": "1.0.0"
    }
