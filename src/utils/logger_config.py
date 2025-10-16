"""
日志配置模块

统一配置所有模块的日志输出到logs文件夹
"""

import logging
from pathlib import Path
from datetime import datetime


def setup_logging():
    """设置统一的日志配置"""

    # 创建logs目录
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # 生成日志文件名（按日期）
    log_filename = f"app_{datetime.now().strftime('%Y%m%d')}.log"
    log_file_path = logs_dir / log_filename

    # 配置日志格式
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # 配置根日志器
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            # 文件处理器 - 输出到日志文件
            logging.FileHandler(log_file_path, encoding="utf-8"),
            # 控制台处理器 - 输出到控制台
            logging.StreamHandler(),
        ],
    )

    # 设置第三方库的日志级别
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    return log_file_path


def get_logger(name: str) -> logging.Logger:
    """获取指定名称的日志器"""
    return logging.getLogger(name)
