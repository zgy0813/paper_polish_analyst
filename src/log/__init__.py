"""
日志管理模块
提供日志查询、统计和管理功能
"""

from .query import LogQuery, LogEntry, LogStats
from .utils import (
    get_log_query, 
    quick_search_errors, 
    quick_search_warnings, 
    quick_search_keyword,
    get_log_summary,
    get_recent_errors,
    get_recent_warnings,
    search_logs_by_keyword,
    get_log_files_info
)

__all__ = [
    'LogQuery',
    'LogEntry', 
    'LogStats',
    'get_log_query',
    'quick_search_errors',
    'quick_search_warnings', 
    'quick_search_keyword',
    'get_log_summary',
    'get_recent_errors',
    'get_recent_warnings',
    'search_logs_by_keyword',
    'get_log_files_info'
]
