# logging_config.py
"""
Professional logging configuration for Voice AI system
Filters out noise and shows only important business logic
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
import os

class VoiceAILogFilter(logging.Filter):
    """Custom filter to reduce noise from third-party libraries"""
    
    def filter(self, record):
        # Block noisy MongoDB logs
        if record.name.startswith('pymongo'):
            # Only allow WARNING and above for MongoDB
            return record.levelno >= logging.WARNING
        
        # Block noisy LiveKit connection logs  
        if 'heartbeat' in record.getMessage().lower():
            return False
            
        if 'connection ready' in record.getMessage().lower():
            return False
            
        if 'connection created' in record.getMessage().lower():
            return False
            
        if 'connection closed' in record.getMessage().lower():
            return False
        
        # Block circuit breaker noise (only show state changes)
        if 'circuit breaker' in record.getMessage().lower() and 'OPEN' not in record.getMessage():
            return False
        
        # Block performance target met messages (keep warnings)
        if 'Performance target met' in record.getMessage():
            return False
            
        # Block cache hit/miss details
        if 'cache hit' in record.getMessage().lower() or 'cache miss' in record.getMessage().lower():
            return False
        
        # Block detailed duration logs under 100ms
        if 'ms:' in record.getMessage() and any(word in record.getMessage() for word in ['retrieved', 'saved', 'stored']):
            try:
                # Extract duration and only show if > 100ms
                import re
                duration_match = re.search(r'(\d+\.?\d*)\s*ms', record.getMessage())
                if duration_match:
                    duration = float(duration_match.group(1))
                    if duration < 100:  # Less than 100ms - not interesting
                        return False
            except:
                pass
        
        return True

class ColoredFormatter(logging.Formatter):
    """Colored formatter for better readability"""
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green  
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record):
        # Add color to level name
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        
        return super().format(record)

def setup_voice_ai_logging(log_level: str = "INFO", enable_file_logging: bool = True):
    """
    Setup optimized logging for Voice AI system
    
    Args:
        log_level: "DEBUG", "INFO", "WARNING", "ERROR"
        enable_file_logging: Whether to log to files
    """
    
    # Convert string to logging level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Remove all existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create custom filter
    voice_filter = VoiceAILogFilter()
    
    # Console handler with colors and filtering
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.addFilter(voice_filter)
    
    # Use colored formatter for console
    console_formatter = ColoredFormatter(
        '%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    
    # File handlers (if enabled)
    handlers = [console_handler]
    
    if enable_file_logging:
        # Main log file (filtered)
        today = datetime.now().strftime("%Y%m%d")
        main_log_file = logs_dir / f"voice_ai_{today}.log"
        
        file_handler = logging.FileHandler(main_log_file)
        file_handler.setLevel(logging.INFO)
        file_handler.addFilter(voice_filter)
        
        file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        handlers.append(file_handler)
        
        # Error log file (errors only, no filter)
        error_log_file = logs_dir / f"voice_ai_errors_{today}.log"
        error_handler = logging.FileHandler(error_log_file)
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        handlers.append(error_handler)
        
        # Call events log (business logic only)
        call_log_file = logs_dir / f"call_events_{today}.log"
        call_handler = logging.FileHandler(call_log_file)
        call_handler.setLevel(logging.INFO)
        
        # Custom filter for call events
        class CallEventsFilter(logging.Filter):
            def filter(self, record):
                message = record.getMessage().lower()
                # Only log important call events
                call_keywords = [
                    'call session started', 'incoming call', 'caller identified',
                    'new caller', 'returning caller', 'transfer', 'session ended',
                    'greeting', 'knowledge search', 'information gathered'
                ]
                return any(keyword in message for keyword in call_keywords)
        
        call_handler.addFilter(CallEventsFilter())
        call_handler.setFormatter(file_formatter)
        handlers.append(call_handler)
    
    # Configure root logger
    root_logger.setLevel(logging.DEBUG)  # Allow all levels, handlers will filter
    
    for handler in handlers:
        root_logger.addHandler(handler)
    
    # Configure third-party loggers to be less verbose
    third_party_loggers = [
        'pymongo',
        'pymongo.connection', 
        'pymongo.serverSelection',
        'pymongo.command',
        'pymongo.topology',
        'livekit.agents',
        'qdrant_client',
        'openai',
        'httpx',
        'httpcore'
    ]
    
    for logger_name in third_party_loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)
    
    # Set your application loggers to appropriate levels
    app_loggers = {
        '__main__': numeric_level,
        'main': numeric_level,
        'call_transcription_storage': logging.WARNING,  # Reduce storage noise
        'simple_rag_v2': numeric_level,
        'config': logging.WARNING
    }
    
    for logger_name, level in app_loggers.items():
        logging.getLogger(logger_name).setLevel(level)
    
    print(f"✅ Voice AI logging configured:")
    print(f"   📊 Level: {log_level}")
    print(f"   📝 File logging: {'Enabled' if enable_file_logging else 'Disabled'}")
    print(f"   📁 Log directory: {logs_dir.absolute()}")
    if enable_file_logging:
        print(f"   📄 Main log: voice_ai_{today}.log")
        print(f"   🚨 Error log: voice_ai_errors_{today}.log") 
        print(f"   📞 Call events: call_events_{today}.log")

def create_call_logger(name: str) -> logging.Logger:
    """Create a logger optimized for call-specific events"""
    logger = logging.getLogger(f"call.{name}")
    return logger

def log_call_event(logger: logging.Logger, event: str, details: str = "", level: str = "INFO"):
    """Log important call events in a structured format"""
    if level.upper() == "INFO":
        logger.info(f"📞 {event}: {details}")
    elif level.upper() == "WARNING":
        logger.warning(f"⚠️ {event}: {details}")
    elif level.upper() == "ERROR":
        logger.error(f"❌ {event}: {details}")

# Quick setup functions for different environments
def setup_development_logging():
    """Development environment - more verbose"""
    setup_voice_ai_logging("INFO", enable_file_logging=True)

def setup_production_logging():
    """Production environment - less verbose"""
    setup_voice_ai_logging("WARNING", enable_file_logging=True)

def setup_debug_logging():
    """Debug environment - most verbose but filtered"""
    setup_voice_ai_logging("DEBUG", enable_file_logging=True)

def setup_minimal_logging():
    """Minimal logging - console only, warnings+"""
    setup_voice_ai_logging("WARNING", enable_file_logging=False)

if __name__ == "__main__":
    # Test the logging setup
    setup_development_logging()
    
    logger = logging.getLogger(__name__)
    
    # Test different log levels
    logger.debug("This is a debug message")
    logger.info("✅ This is an info message")  
    logger.warning("⚠️ This is a warning message")
    logger.error("❌ This is an error message")
    
    # Test call event logging
    call_logger = create_call_logger("test")
    log_call_event(call_logger, "Call Started", "Phone: +1234567890")
    log_call_event(call_logger, "Caller Identified", "Returning caller with 3 previous calls", "INFO")
    log_call_event(call_logger, "Knowledge Search", "Query: battery service pricing", "INFO")
    
    print("\n✅ Logging test completed. Check logs/ directory for files.")