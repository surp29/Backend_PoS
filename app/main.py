from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from .database import Base, engine, SessionLocal
from .models import User
from werkzeug.security import generate_password_hash
from .config import Config
from .logger import (
    log_request, log_response, log_error, log_info, 
    log_success, log_warning, logger
)
import os
import time
from .api_fastapi import (
    products, prices, orders, invoices, users,
    accounts, product_groups, warehouses,
    auth, general_diary, areas, shops,
    customers_analytics, discount_codes, reports, schedules
)
from .migrations import run_migrations

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
    allow_origins=["http://localhost:5000", "*"], # Cho phép local FE truy cập toàn bộ API
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# Request logging middleware
@app.middleware("http")
async def log_requests_middleware(request: Request, call_next):
    """Middleware để log tất cả HTTP requests"""
    start_time = time.time()
    
    # Log request
    log_request(
        method=request.method,
        path=request.url.path,
        query_params=str(request.query_params)
    )
    
    try:
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log response
        log_response(
            status_code=response.status_code,
            path=request.url.path,
            process_time=f"{process_time:.3f}s"
        )
        
        return response
        
    except Exception as e:
        # Log error
        process_time = time.time() - start_time
        log_error(
            operation="REQUEST",
            message=f"Lỗi xử lý request {request.method} {request.url.path}",
            error=e
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "message": str(e),
                "path": request.url.path
            }
        )


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handler cho validation errors"""
    log_error(
        operation="VALIDATION",
        message=f"Lỗi validate dữ liệu ở {request.url.path}",
        error=exc
    )
    
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "details": exc.errors(),
            "path": request.url.path
        }
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handler cho HTTP exceptions"""
    log_warning(
        operation="HTTP_ERROR",
        message=f"HTTP {exc.status_code} ở {request.url.path}: {exc.detail}"
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": request.url.path
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handler cho các exceptions chung"""
    log_error(
        operation="EXCEPTION",
        message=f"Lỗi không xác định ở {request.url.path}",
        error=exc
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": str(exc),
            "type": exc.__class__.__name__,
            "path": request.url.path
        }
    )

# Mount static files
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Include API routers
app.include_router(products.router, prefix="/api", tags=["products"])
app.include_router(prices.router, prefix="/api", tags=["prices"])
app.include_router(orders.router, prefix="/api", tags=["orders"])
app.include_router(invoices.router, prefix="/api", tags=["invoices"])
app.include_router(users.router, prefix="/api", tags=["users"])
app.include_router(accounts.router, prefix="/api", tags=["accounts"])
app.include_router(product_groups.router, prefix="/api", tags=["product_groups"])
# Warehouses router already has internal prefix "/warehouse" → mount at "/api"
app.include_router(warehouses.router, prefix="/api", tags=["warehouses"])
app.include_router(shops.router, prefix="/api", tags=["shops"])
app.include_router(areas.router, prefix="/api", tags=["areas"])
app.include_router(auth.router, prefix="/api", tags=["authentication"])
app.include_router(general_diary.router, prefix="/api", tags=["general_diary"])
app.include_router(customers_analytics.router, prefix="/api", tags=["customers-analytics"])
app.include_router(discount_codes.router, prefix="/api/discount-codes", tags=["discount-codes"])
app.include_router(reports.router, prefix="/api", tags=["reports"])  # minimal compatibility
app.include_router(schedules.router, prefix="/api", tags=["schedules"])  # minimal compatibility

@app.on_event("startup")
async def startup_event():
    """Khởi động application"""
    # Run database migrations first
    run_migrations()
    
    # Ensure tables exist even in production (Render free plan has no pre-deploy)
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as _e:
        log_warning("STARTUP", f"Không thể tạo bảng tự động: {_e}")
    # Ensure default admin for free plan where pre-deploy is unavailable
    try:
        username = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
        password = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")
        enabled = os.getenv("DEFAULT_ADMIN_ENABLED", "true").lower() in ("1", "true", "yes")
        if enabled:
            db = SessionLocal()
            try:
                existing = db.query(User).filter(User.username == username).first()
                if not existing:
                    user = User(
                        username=username,
                        password=generate_password_hash(password),
                        name="Administrator",
                        position="Admin",
                        department="System",
                        status=True,
                    )
                    db.add(user)
                    db.commit()
                    log_success("STARTUP", f"Đã tạo tài khoản mặc định '{username}'")
            finally:
                db.close()
    except Exception as _e:
        # Don't block startup if creation fails; it will be visible in logs
        log_warning("STARTUP", f"Không thể tạo admin mặc định: {_e}")
    log_success("STARTUP", "🚀 PhanMemKeToan Backend đã khởi động thành công!")
    log_info("STARTUP", f"📡 API đang chạy tại: http://localhost:{Config.BACKEND_PORT}")
    log_info("STARTUP", f"📚 API Docs: http://localhost:{Config.BACKEND_PORT}/docs")
    if '@' in Config.SQLALCHEMY_DATABASE_URI:
        db_info = Config.SQLALCHEMY_DATABASE_URI.split('@')[-1]
    else:
        db_info = "configured"
    log_info("STARTUP", f"🗄️ Database: {db_info}")


@app.get("/", tags=["root"])
def read_root():
    """Root endpoint"""
    log_info("ROOT", "Truy cập root endpoint")
    return {
        "message": "PhanMemKeToan API is running",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", tags=["health"])
def health_check():
    """Health check endpoint"""
    log_info("HEALTH", "Health check request")
    return {
        "status": "healthy",
        "service": "PhanMemKeToan API",
        "version": "1.0.0"
    }
