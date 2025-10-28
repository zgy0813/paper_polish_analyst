"""
日志管理工具模块
提供便捷的日志查询和管理功能
"""

from .query import LogQuery, LogEntry, LogStats
from ..utils.logger_config import get_logger

logger = get_logger(__name__)


def get_log_query(logs_dir: str = "logs") -> LogQuery:
    """获取日志查询器实例"""
    return LogQuery(logs_dir)


def quick_search_errors(limit: int = 20) -> list[LogEntry]:
    """快速搜索错误日志"""
    query = get_log_query()
    return query.search_errors(limit=limit)


def quick_search_warnings(limit: int = 20) -> list[LogEntry]:
    """快速搜索警告日志"""
    query = get_log_query()
    return query.search_warnings(limit=limit)


def quick_search_keyword(keyword: str, limit: int = 20) -> list[LogEntry]:
    """快速按关键词搜索"""
    query = get_log_query()
    return query.search_by_keyword(keyword, limit=limit)


def get_log_summary() -> dict:
    """获取日志摘要信息"""
    query = get_log_query()
    stats = query.get_log_stats()
    
    return {
        "total_entries": stats.total_entries,
        "error_count": stats.error_count,
        "warning_count": stats.warning_count,
        "file_size_kb": round(stats.file_size / 1024, 2),
        "time_range": {
            "start": stats.time_range[0].isoformat() if stats.time_range[0] else None,
            "end": stats.time_range[1].isoformat() if stats.time_range[1] else None
        },
        "level_distribution": stats.level_counts,
        "logger_distribution": dict(list(stats.logger_counts.items())[:10])  # 前10个日志器
    }


def get_recent_errors(limit: int = 10) -> list[dict]:
    """获取最近的错误日志"""
    errors = quick_search_errors(limit)
    return [
        {
            "timestamp": entry.timestamp.isoformat(),
            "level": entry.level,
            "logger_name": entry.logger_name,
            "message": entry.message,
            "line_number": entry.line_number
        }
        for entry in errors
    ]


def get_recent_warnings(limit: int = 10) -> list[dict]:
    """获取最近的警告日志"""
    warnings = quick_search_warnings(limit)
    return [
        {
            "timestamp": entry.timestamp.isoformat(),
            "level": entry.level,
            "logger_name": entry.logger_name,
            "message": entry.message,
            "line_number": entry.line_number
        }
        for entry in warnings
    ]


def search_logs_by_keyword(keyword: str, limit: int = 20) -> list[dict]:
    """按关键词搜索日志"""
    entries = quick_search_keyword(keyword, limit)
    return [
        {
            "timestamp": entry.timestamp.isoformat(),
            "level": entry.level,
            "logger_name": entry.logger_name,
            "message": entry.message,
            "line_number": entry.line_number
        }
        for entry in entries
    ]


def get_log_files_info() -> list[dict]:
    """获取日志文件信息"""
    query = get_log_query()
    log_files = query.get_log_files()
    
    files_info = []
    for file_path in log_files:
        try:
            stat = file_path.stat()
            files_info.append({
                "name": file_path.name,
                "size_kb": round(stat.st_size / 1024, 2),
                "modified_time": stat.st_mtime,
                "modified_datetime": file_path.stat().st_mtime
            })
        except Exception as e:
            logger.warning(f"获取文件信息失败 {file_path}: {str(e)}")
    
    return files_info


def clean_old_logs(days: int = 30) -> dict:
    """清理旧日志文件"""
    query = get_log_query()
    deleted_count = query.clean_old_logs(days)
    
    return {
        "deleted_count": deleted_count,
        "message": f"清理完成，删除了 {deleted_count} 个超过 {days} 天的日志文件"
    }

