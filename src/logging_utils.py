#!/usr/bin/env python3
"""
Logging utilities for the Driver Packet Processing system
Provides centralized logging configuration with session-based and time-based rotation
"""

import os
import sys
import io
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta


def cleanup_old_session_logs(session_dir: Path, days_to_keep: int) -> None:
    """
    Clean up old session log files older than specified days
    
    Args:
        session_dir: Directory containing session logs
        days_to_keep: Number of days to keep session logs
    """
    try:
        if not session_dir.exists():
            return
            
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        # Find and remove old session log files
        removed_count = 0
        for log_file in session_dir.glob('*_session_*.log'):
            try:
                # Extract timestamp from filename: driver_packet_session_20251002_141530.log
                parts = log_file.stem.split('_')
                if len(parts) >= 4:
                    date_str = parts[-2]  # 20251002
                    time_str = parts[-1]  # 141530
                    
                    # Parse the timestamp
                    timestamp_str = f"{date_str}_{time_str}"
                    file_date = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                    
                    if file_date < cutoff_date:
                        log_file.unlink()
                        removed_count += 1
                        
            except (ValueError, IndexError):
                # Skip files that don't match the expected format
                continue
        
        if removed_count > 0:
            print(f"🧹 Cleaned up {removed_count} old session log files older than {days_to_keep} days")
            
    except Exception as e:
        # Silently fail cleanup to not disrupt logging
        pass


def init_file_logging(log_name: str = 'driver_packet', 
                     log_subdir: str = 'temp') -> logging.Logger:
    """
    Initialize logging with both session-based and time-based rotation.
    
    Creates two log handlers:
    1. Session log: New file per session with timestamp
    2. Daily rotating log: Rolls over daily, keeps historical logs
    
    Args:
        log_name: Name of the logger and log file
        log_subdir: Subdirectory under project root for log files
        
    Returns:
        Configured logger instance
    """
    try:
        from .config import config
        
        base_dir = Path(__file__).resolve().parents[1]
        log_dir = base_dir / log_subdir
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create session-based subdirectory
        session_dir = log_dir / 'sessions'
        session_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate session timestamp and file paths
        session_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        session_log_file = session_dir / f'{log_name}_session_{session_timestamp}.log'
        daily_log_file = log_dir / f'{log_name}_daily.log'
        rotating_log_file = log_dir / f'{log_name}_rotating.log'
        
        logger = logging.getLogger(log_name)
        logger.setLevel(getattr(logging, config.LOG_LEVEL, logging.INFO))
        
        # Clear existing handlers to avoid duplicates
        logger.handlers.clear()
        
        # Auto-cleanup old session logs if enabled
        if config.LOG_AUTO_CLEANUP:
            cleanup_old_session_logs(session_dir, config.LOG_SESSION_CLEANUP_DAYS)
        
        # 1. SESSION-BASED LOG (new file per run) - if enabled
        if config.LOG_SESSION_ENABLED:
            session_handler = logging.FileHandler(
                session_log_file,
                encoding='utf-8'
            )
            session_formatter = logging.Formatter(
                '%(asctime)s [%(levelname)8s] %(name)s: %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            session_handler.setFormatter(session_formatter)
            logger.addHandler(session_handler)
        
        # 2. TIME-BASED ROTATING LOG (daily rotation) - if enabled
        if config.LOG_DAILY_ROTATION:
            daily_handler = TimedRotatingFileHandler(
                daily_log_file,
                when='midnight',          # Rotate at midnight
                interval=1,               # Every 1 day
                backupCount=config.LOG_BACKUP_COUNT,  # Keep N days of logs
                encoding='utf-8',
                utc=False                 # Use local time
            )
            daily_handler.suffix = '%Y-%m-%d'  # Backup files: driver_packet_daily.log.2025-10-02
            daily_formatter = logging.Formatter(
                '%(asctime)s [%(levelname)8s] %(name)s: %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            daily_handler.setFormatter(daily_formatter)
            logger.addHandler(daily_handler)
        
        # 3. SIZE-BASED ROTATING LOG (fallback for very large single sessions) - if enabled
        if config.LOG_SIZE_ROTATION:
            rotating_handler = RotatingFileHandler(
                rotating_log_file,
                maxBytes=config.LOG_FILE_MAX_BYTES,
                backupCount=3,
                encoding='utf-8'
            )
            rotating_formatter = logging.Formatter(
                '%(asctime)s [%(levelname)8s] %(name)s: %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            rotating_handler.setFormatter(rotating_formatter)
            logger.addHandler(rotating_handler)
        
        logger.propagate = False
        
        # Log the session start
        logger.info("="*60)
        logger.info(f"🚀 NEW SESSION STARTED: {session_timestamp}")
        if config.LOG_SESSION_ENABLED:
            logger.info(f"📁 Session log: {session_log_file}")
        if config.LOG_DAILY_ROTATION:
            logger.info(f"📅 Daily log: {daily_log_file}")
        if config.LOG_SIZE_ROTATION:
            logger.info(f"🔄 Rotating log: {rotating_log_file}")
        logger.info("="*60)
        
        return logger
        
    except Exception as e:
        # Fallback to basic logging if file logging fails
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)8s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        logger = logging.getLogger(log_name)
        logger.error(f"Failed to initialize file logging: {e}")
        return logger


class StreamToLogger(io.TextIOBase):
    """
    Custom stream that redirects writes to a logger
    """
    
    def __init__(self, logger: logging.Logger, level: int):
        self.logger = logger
        self.level = level
        
    def write(self, buf):
        if not buf:
            return 0
        for line in str(buf).rstrip().splitlines():
            if line:
                self.logger.log(self.level, line)
        return len(buf)
        
    def flush(self):
        pass


def setup_print_override(logger: logging.Logger) -> None:
    """
    Override the built-in print function to log messages
    
    Args:
        logger: Logger instance to use for print statements
    """
    def print_override(*args, **kwargs):  # type: ignore[override]
        try:
            sep = kwargs.get('sep', ' ')
            end = kwargs.get('end', '')
            msg = sep.join(str(a) for a in args) + end
            
            # Heuristic for level based on emojis/keywords
            level = logging.INFO
            text = ''.join(str(a) for a in args)
            if '❌' in text or 'ERROR' in text or 'Error' in text:
                level = logging.ERROR
            elif '⚠️' in text or 'Warning' in text or 'warning' in text:
                level = logging.WARNING
                
            logger.log(level, msg)
        except Exception:
            pass
    
    # Replace the built-in print function
    import builtins
    builtins.print = print_override


def redirect_streams_to_logger(logger: logging.Logger) -> None:
    """
    Redirect stdout and stderr to the logger
    
    Args:
        logger: Logger instance to redirect streams to
    """
    try:
        sys.stdout = StreamToLogger(logger, logging.INFO)
        sys.stderr = StreamToLogger(logger, logging.ERROR)
    except Exception:
        # Silently fail if redirection doesn't work
        pass


def setup_logging(log_name: str = 'driver_packet', 
                 log_subdir: str = None,
                 redirect_streams: bool = None,
                 override_print: bool = None) -> logging.Logger:
    """
    Complete logging setup with file logging, stream redirection, and print override
    
    Args:
        log_name: Name of the logger and log file
        log_subdir: Subdirectory under project root for log files (uses config if None)
        redirect_streams: Whether to redirect stdout/stderr to logger (uses config if None)
        override_print: Whether to override the print function (uses config if None)
        
    Returns:
        Configured logger instance
    """
    # Import config here to avoid circular imports
    try:
        from .config import config
        
        # Use config defaults if not provided
        if log_subdir is None:
            log_subdir = config.LOG_DIR
        if redirect_streams is None:
            redirect_streams = config.REDIRECT_STDOUT and config.REDIRECT_STDERR  
        if override_print is None:
            override_print = config.OVERRIDE_PRINT
            
    except ImportError:
        # Fallback if config not available
        if log_subdir is None:
            log_subdir = 'temp'
        if redirect_streams is None:
            redirect_streams = True
        if override_print is None:
            override_print = True
    
    logger = init_file_logging(log_name, log_subdir)
    
    if redirect_streams:
        redirect_streams_to_logger(logger)
        
    if override_print:
        setup_print_override(logger)
    
    return logger


def get_logger(name: str = 'driver_packet') -> logging.Logger:
    """
    Get a logger instance by name
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
