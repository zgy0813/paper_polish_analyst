"""
日志查询模块
用于管理和查询logs目录中的日志文件
"""

import os
import re
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict, Counter

from ..utils.logger_config import get_logger

logger = get_logger(__name__)


@dataclass
class LogEntry:
    """日志条目数据类"""
    timestamp: datetime
    level: str
    logger_name: str
    message: str
    raw_line: str
    line_number: int


@dataclass
class LogStats:
    """日志统计信息"""
    total_entries: int
    level_counts: Dict[str, int]
    logger_counts: Dict[str, int]
    time_range: Tuple[datetime, datetime]
    file_size: int
    error_count: int
    warning_count: int


class LogQuery:
    """日志查询器"""
    
    def __init__(self, logs_dir: str = "logs"):
        """
        初始化日志查询器
        
        Args:
            logs_dir: 日志目录路径
        """
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(exist_ok=True)
        
        # 日志格式正则表达式
        self.log_pattern = re.compile(
            r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - ([^-]+) - (\w+) - (.+)$'
        )
    
    def get_log_files(self) -> List[Path]:
        """
        获取所有日志文件
        
        Returns:
            日志文件路径列表
        """
        if not self.logs_dir.exists():
            return []
        
        log_files = []
        for file_path in self.logs_dir.iterdir():
            if file_path.is_file() and file_path.suffix == '.log':
                log_files.append(file_path)
        
        # 按修改时间排序，最新的在前
        log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        return log_files
    
    def parse_log_line(self, line: str, line_number: int) -> Optional[LogEntry]:
        """
        解析单行日志
        
        Args:
            line: 日志行内容
            line_number: 行号
            
        Returns:
            解析后的日志条目，如果解析失败返回None
        """
        line = line.strip()
        if not line:
            return None
        
        match = self.log_pattern.match(line)
        if not match:
            return None
        
        try:
            timestamp_str, logger_name, level, message = match.groups()
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
            
            return LogEntry(
                timestamp=timestamp,
                level=level,
                logger_name=logger_name,
                message=message,
                raw_line=line,
                line_number=line_number
            )
        except Exception as e:
            logger.warning(f"解析日志行失败 (行 {line_number}): {str(e)}")
            return None
    
    def read_log_file(self, file_path: Path) -> List[LogEntry]:
        """
        读取日志文件
        
        Args:
            file_path: 日志文件路径
            
        Returns:
            日志条目列表
        """
        entries = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_number, line in enumerate(f, 1):
                    entry = self.parse_log_line(line, line_number)
                    if entry:
                        entries.append(entry)
        except Exception as e:
            logger.error(f"读取日志文件失败 {file_path}: {str(e)}")
        
        return entries
    
    def query_logs(
        self,
        level: Optional[str] = None,
        logger_name: Optional[str] = None,
        keyword: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None,
        file_pattern: Optional[str] = None
    ) -> List[LogEntry]:
        """
        查询日志
        
        Args:
            level: 日志级别过滤 (INFO, WARNING, ERROR, DEBUG)
            logger_name: 日志器名称过滤
            keyword: 关键词过滤（在消息中搜索）
            start_time: 开始时间过滤
            end_time: 结束时间过滤
            limit: 限制返回数量
            file_pattern: 文件名模式过滤
            
        Returns:
            过滤后的日志条目列表
        """
        all_entries = []
        
        # 获取日志文件
        log_files = self.get_log_files()
        if file_pattern:
            import fnmatch
            log_files = [f for f in log_files if fnmatch.fnmatch(f.name, file_pattern)]
        
        # 读取所有日志文件
        for file_path in log_files:
            entries = self.read_log_file(file_path)
            all_entries.extend(entries)
        
        # 按时间排序
        all_entries.sort(key=lambda x: x.timestamp, reverse=True)
        
        # 应用过滤条件
        filtered_entries = []
        for entry in all_entries:
            # 级别过滤
            if level and entry.level != level:
                continue
            
            # 日志器名称过滤
            if logger_name and logger_name not in entry.logger_name:
                continue
            
            # 关键词过滤
            if keyword and keyword.lower() not in entry.message.lower():
                continue
            
            # 时间范围过滤
            if start_time and entry.timestamp < start_time:
                continue
            if end_time and entry.timestamp > end_time:
                continue
            
            filtered_entries.append(entry)
            
            # 限制数量
            if limit and len(filtered_entries) >= limit:
                break
        
        return filtered_entries
    
    def get_log_stats(self, file_path: Optional[Path] = None) -> LogStats:
        """
        获取日志统计信息
        
        Args:
            file_path: 指定日志文件，None表示所有文件
            
        Returns:
            日志统计信息
        """
        if file_path:
            entries = self.read_log_file(file_path)
            file_size = file_path.stat().st_size
        else:
            entries = []
            file_size = 0
            for log_file in self.get_log_files():
                entries.extend(self.read_log_file(log_file))
                file_size += log_file.stat().st_size
        
        if not entries:
            return LogStats(
                total_entries=0,
                level_counts={},
                logger_counts={},
                time_range=(datetime.now(), datetime.now()),
                file_size=file_size,
                error_count=0,
                warning_count=0
            )
        
        # 统计信息
        level_counts = Counter(entry.level for entry in entries)
        logger_counts = Counter(entry.logger_name for entry in entries)
        
        timestamps = [entry.timestamp for entry in entries]
        time_range = (min(timestamps), max(timestamps))
        
        error_count = level_counts.get('ERROR', 0)
        warning_count = level_counts.get('WARNING', 0)
        
        return LogStats(
            total_entries=len(entries),
            level_counts=dict(level_counts),
            logger_counts=dict(logger_counts),
            time_range=time_range,
            file_size=file_size,
            error_count=error_count,
            warning_count=warning_count
        )
    
    def search_errors(self, limit: int = 50) -> List[LogEntry]:
        """
        搜索错误日志
        
        Args:
            limit: 限制返回数量
            
        Returns:
            错误日志条目列表
        """
        return self.query_logs(level='ERROR', limit=limit)
    
    def search_warnings(self, limit: int = 50) -> List[LogEntry]:
        """
        搜索警告日志
        
        Args:
            limit: 限制返回数量
            
        Returns:
            警告日志条目列表
        """
        return self.query_logs(level='WARNING', limit=limit)
    
    def search_by_keyword(self, keyword: str, limit: int = 50) -> List[LogEntry]:
        """
        按关键词搜索日志
        
        Args:
            keyword: 搜索关键词
            limit: 限制返回数量
            
        Returns:
            匹配的日志条目列表
        """
        return self.query_logs(keyword=keyword, limit=limit)
    
    def search_by_logger(self, logger_name: str, limit: int = 50) -> List[LogEntry]:
        """
        按日志器名称搜索
        
        Args:
            logger_name: 日志器名称
            limit: 限制返回数量
            
        Returns:
            匹配的日志条目列表
        """
        return self.query_logs(logger_name=logger_name, limit=limit)
    
    def get_recent_logs(self, hours: int = 24, limit: int = 100) -> List[LogEntry]:
        """
        获取最近的日志
        
        Args:
            hours: 最近多少小时
            limit: 限制返回数量
            
        Returns:
            最近的日志条目列表
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        return self.query_logs(start_time=start_time, end_time=end_time, limit=limit)
    
    def export_logs(
        self,
        output_file: str,
        level: Optional[str] = None,
        keyword: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        format: str = 'json'
    ) -> bool:
        """
        导出日志到文件
        
        Args:
            output_file: 输出文件路径
            level: 日志级别过滤
            keyword: 关键词过滤
            start_time: 开始时间过滤
            end_time: 结束时间过滤
            format: 导出格式 ('json', 'txt', 'csv')
            
        Returns:
            是否导出成功
        """
        try:
            entries = self.query_logs(
                level=level,
                keyword=keyword,
                start_time=start_time,
                end_time=end_time
            )
            
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if format == 'json':
                data = []
                for entry in entries:
                    data.append({
                        'timestamp': entry.timestamp.isoformat(),
                        'level': entry.level,
                        'logger_name': entry.logger_name,
                        'message': entry.message,
                        'line_number': entry.line_number
                    })
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            
            elif format == 'txt':
                with open(output_path, 'w', encoding='utf-8') as f:
                    for entry in entries:
                        f.write(f"{entry.raw_line}\n")
            
            elif format == 'csv':
                import csv
                with open(output_path, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['timestamp', 'level', 'logger_name', 'message', 'line_number'])
                    for entry in entries:
                        writer.writerow([
                            entry.timestamp.isoformat(),
                            entry.level,
                            entry.logger_name,
                            entry.message,
                            entry.line_number
                        ])
            
            logger.info(f"日志导出成功: {output_file} ({len(entries)} 条记录)")
            return True
            
        except Exception as e:
            logger.error(f"日志导出失败: {str(e)}")
            return False
    
    def clean_old_logs(self, days: int = 30) -> int:
        """
        清理旧日志文件
        
        Args:
            days: 保留最近多少天的日志
            
        Returns:
            删除的文件数量
        """
        cutoff_time = datetime.now() - timedelta(days=days)
        deleted_count = 0
        
        for log_file in self.get_log_files():
            file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
            if file_time < cutoff_time:
                try:
                    log_file.unlink()
                    deleted_count += 1
                    logger.info(f"删除旧日志文件: {log_file}")
                except Exception as e:
                    logger.error(f"删除日志文件失败 {log_file}: {str(e)}")
        
        return deleted_count


# 便捷函数
def get_log_query(logs_dir: str = "logs") -> LogQuery:
    """获取日志查询器实例"""
    return LogQuery(logs_dir)


def quick_search_errors(limit: int = 20) -> List[LogEntry]:
    """快速搜索错误日志"""
    query = get_log_query()
    return query.search_errors(limit=limit)


def quick_search_warnings(limit: int = 20) -> List[LogEntry]:
    """快速搜索警告日志"""
    query = get_log_query()
    return query.search_warnings(limit=limit)


def quick_search_keyword(keyword: str, limit: int = 20) -> List[LogEntry]:
    """快速按关键词搜索"""
    query = get_log_query()
    return query.search_by_keyword(keyword, limit=limit)
