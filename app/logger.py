"""
Logging utility for PhanMemKeToan Backend
Provides colored console logging for better visibility
"""
import logging
import sys
from datetime import datetime
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Custom formatter với màu sắc cho console output"""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',       # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    ICONS = {
        'DEBUG': '🔍',
        'INFO': 'ℹ️',
        'WARNING': '⚠️',
        'ERROR': '❌',
        'CRITICAL': '🚨',
        'SUCCESS': '✅',
        'REQUEST': '📥',
        'RESPONSE': '📤',
        'DATABASE': '💾',
        'API': '🔌'
    }
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset_color = self.COLORS['RESET']
        icon = self.ICONS.get(record.levelname, '')
        
        # Format timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Format message với màu và icon
        if hasattr(record, 'operation'):
            operation = record.operation
            log_msg = f"{log_color}{icon} [{timestamp}] [{record.levelname}] [{operation}]{reset_color} {record.getMessage()}"
        else:
            log_msg = f"{log_color}{icon} [{timestamp}] [{record.levelname}]{reset_color} {record.getMessage()}"
        
        return log_msg


def setup_logging():
    """Setup logging configuration"""
    # Tạo logger cho application
    logger = logging.getLogger('phanmemketoan')
    logger.setLevel(logging.INFO)
    
    # Xóa các handlers cũ nếu có
    logger.handlers.clear()
    
    # Console handler với màu sắc
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(ColoredFormatter())
    
    logger.addHandler(console_handler)
    
    # Không propagate để tránh duplicate logs
    logger.propagate = False
    
    return logger


# Tạo logger instance
logger = setup_logging()


def log_info(operation: str, message: str, **kwargs):
    """Log thông tin thao tác"""
    extra = {'operation': operation}
    logger.info(f"{message}", extra=extra)


def log_success(operation: str, message: str, **kwargs):
    """Log thành công"""
    extra = {'operation': operation, 'levelname': 'SUCCESS'}
    logger.info(f"✅ {message}", extra=extra)


def log_warning(operation: str, message: str, **kwargs):
    """Log cảnh báo"""
    extra = {'operation': operation}
    logger.warning(f"{message}", extra=extra)


def log_error(operation: str, message: str, error: Optional[Exception] = None, **kwargs):
    """Log lỗi"""
    extra = {'operation': operation}
    error_msg = message
    if error:
        error_msg += f" | Chi tiết: {str(error)}"
        if hasattr(error, '__class__'):
            error_msg += f" | Loại lỗi: {error.__class__.__name__}"
    logger.error(f"{error_msg}", extra=extra)


def log_request(method: str, path: str, **kwargs):
    """Log HTTP request"""
    extra = {'operation': 'REQUEST', 'levelname': 'REQUEST'}
    logger.info(f"📥 {method} {path}", extra=extra)


def log_response(status_code: int, path: str, **kwargs):
    """Log HTTP response"""
    extra = {'operation': 'RESPONSE', 'levelname': 'RESPONSE'}
    status_icon = '✅' if 200 <= status_code < 300 else '❌'
    logger.info(f"📤 {status_icon} {status_code} {path}", extra=extra)


def log_database(operation: str, message: str, **kwargs):
    """Log database operations"""
    extra = {'operation': 'DATABASE', 'levelname': 'DATABASE'}
    logger.info(f"💾 [{operation}] {message}", extra=extra)


def log_api(operation: str, message: str, **kwargs):
    """Log API operations"""
    extra = {'operation': 'API', 'levelname': 'API'}
    logger.info(f"🔌 [{operation}] {message}", extra=extra)

