"""
论文风格分析与润色系统

一个智能的学术论文润色工具，通过分析期刊论文提取写作风格特征，
提供多轮交互式润色和质量评分功能。
"""

from . import analysis
from . import polishing
from . import core
from . import utils

__version__ = "1.0.0"
__author__ = "AI Assistant"

__all__ = [
    'analysis',
    'polishing', 
    'core',
    'utils'
]
