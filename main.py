import uvicorn
import logging
import sys
from app.main import app
from app.config import Config

# Tắt hoàn toàn tất cả log không cần thiết
import logging.config

# Cấu hình logging để tắt hoàn toàn
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
    },
    "root": {
        "level": "CRITICAL",
        "handlers": ["default"],
    },
    "loggers": {
        "sqlalchemy": {"level": "CRITICAL", "handlers": [], "propagate": False},
        "sqlalchemy.engine": {"level": "CRITICAL", "handlers": [], "propagate": False},
        "sqlalchemy.pool": {"level": "CRITICAL", "handlers": [], "propagate": False},
        "sqlalchemy.dialects": {"level": "CRITICAL", "handlers": [], "propagate": False},
        "uvicorn": {"level": "CRITICAL", "handlers": [], "propagate": False},
        "uvicorn.access": {"level": "CRITICAL", "handlers": [], "propagate": False},
        "uvicorn.error": {"level": "CRITICAL", "handlers": [], "propagate": False},
        "fastapi": {"level": "CRITICAL", "handlers": [], "propagate": False},
        "starlette": {"level": "CRITICAL", "handlers": [], "propagate": False},
    },
}

logging.config.dictConfig(LOGGING_CONFIG)

# Redirect stdout để chỉ hiển thị print statements và lỗi
class FilteredOutput:
    def __init__(self, original_stream):
        self.original_stream = original_stream
        
    def write(self, text):
        # Chỉ hiển thị các dòng chứa print statements của chúng ta hoặc lỗi
        if any(keyword in text for keyword in ["🚀", "🌐", "🔗", "📚", "🗄️", "💡", "Starting PhanMemKeToan", "API will be available", "Frontend should connect", "API Documentation", "Make sure PostgreSQL", "Use Ctrl+C", "ERROR", "CRITICAL", "Exception", "Traceback"]):
            self.original_stream.write(text)
        elif text.strip() == "":
            self.original_stream.write(text)
        # Bỏ qua tất cả các log khác (INFO, DEBUG, WARNING, SQLAlchemy logs)
        elif any(keyword in text for keyword in ["INFO:", "sqlalchemy", "Engine:", "SELECT", "COMMIT", "BEGIN"]):
            pass  # Bỏ qua hoàn toàn
        else:
            pass  # Bỏ qua tất cả các log khác
    
    def flush(self):
        self.original_stream.flush()
    
    def isatty(self):
        return self.original_stream.isatty()
    
    def __getattr__(self, name):
        return getattr(self.original_stream, name)

# Redirect stdout
sys.stdout = FilteredOutput(sys.stdout)

if __name__ == "__main__":
    print(f"🚀 Starting PhanMemKeToan Backend on port {Config.BACKEND_PORT}")
    print(f"🌐 API will be available at: http://localhost:{Config.BACKEND_PORT}")
    print(f"🔗 Frontend should connect to: http://localhost:{Config.BACKEND_PORT}")
    print(f"📚 API Documentation: http://localhost:{Config.BACKEND_PORT}/docs")
    print(f"🗄️ Make sure PostgreSQL is running before starting backend")
    print(f"💡 Use Ctrl+C to stop the server")
    print()
    
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=Config.BACKEND_PORT, 
        reload=True,
        log_level="critical",  # Chỉ hiển thị critical errors
        access_log=False,      # Tắt access log
        log_config=None        # Tắt hoàn toàn uvicorn logging
    )