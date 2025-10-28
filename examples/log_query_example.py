#!/usr/bin/env python3
"""
日志查询模块使用示例
演示如何使用日志查询功能
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.log_query import LogQuery, quick_search_errors, quick_search_warnings, quick_search_keyword


def basic_query_example():
    """基本查询示例"""
    print("=== 基本查询示例 ===")
    
    # 创建日志查询器
    query = LogQuery()
    
    # 获取所有日志文件
    log_files = query.get_log_files()
    print(f"找到 {len(log_files)} 个日志文件:")
    for file_path in log_files:
        print(f"  - {file_path.name}")
    
    # 获取统计信息
    stats = query.get_log_stats()
    print(f"\n日志统计:")
    print(f"  总条目数: {stats.total_entries}")
    print(f"  文件大小: {stats.file_size / 1024:.2f} KB")
    print(f"  错误数量: {stats.error_count}")
    print(f"  警告数量: {stats.warning_count}")
    
    # 级别分布
    if stats.level_counts:
        print(f"\n级别分布:")
        for level, count in stats.level_counts.items():
            print(f"  {level}: {count}")


def search_examples():
    """搜索示例"""
    print("\n=== 搜索示例 ===")
    
    query = LogQuery()
    
    # 搜索错误日志
    print("\n🔴 最近的错误日志:")
    errors = query.search_errors(limit=5)
    for entry in errors:
        print(f"  [{entry.timestamp.strftime('%H:%M:%S')}] {entry.level} | {entry.logger_name} | {entry.message}")
    
    # 搜索警告日志
    print("\n🟡 最近的警告日志:")
    warnings = query.search_warnings(limit=5)
    for entry in warnings:
        print(f"  [{entry.timestamp.strftime('%H:%M:%S')}] {entry.level} | {entry.logger_name} | {entry.message}")
    
    # 按关键词搜索
    print("\n🔍 搜索包含'AI'的日志:")
    ai_logs = query.search_by_keyword('AI', limit=5)
    for entry in ai_logs:
        print(f"  [{entry.timestamp.strftime('%H:%M:%S')}] {entry.level} | {entry.logger_name} | {entry.message}")


def advanced_query_example():
    """高级查询示例"""
    print("\n=== 高级查询示例 ===")
    
    query = LogQuery()
    
    # 查询最近1小时的日志
    print("\n🕐 最近1小时的日志:")
    recent_logs = query.get_recent_logs(hours=1, limit=10)
    for entry in recent_logs:
        print(f"  [{entry.timestamp.strftime('%H:%M:%S')}] {entry.level} | {entry.logger_name} | {entry.message}")
    
    # 查询特定日志器的日志
    print("\n📝 特定日志器的日志:")
    analyzer_logs = query.search_by_logger('src.analysis.layered_analyzer', limit=5)
    for entry in analyzer_logs:
        print(f"  [{entry.timestamp.strftime('%H:%M:%S')}] {entry.level} | {entry.logger_name} | {entry.message}")


def export_example():
    """导出示例"""
    print("\n=== 导出示例 ===")
    
    query = LogQuery()
    
    # 导出错误日志到JSON
    output_file = "error_logs.json"
    success = query.export_logs(
        output_file=output_file,
        level='ERROR',
        format='json'
    )
    
    if success:
        print(f"✅ 错误日志已导出到: {output_file}")
    else:
        print("❌ 导出失败")


def quick_functions_example():
    """便捷函数示例"""
    print("\n=== 便捷函数示例 ===")
    
    # 快速搜索错误
    print("\n🔴 快速搜索错误:")
    errors = quick_search_errors(limit=3)
    for entry in errors:
        print(f"  [{entry.timestamp.strftime('%H:%M:%S')}] {entry.level} | {entry.logger_name} | {entry.message}")
    
    # 快速搜索警告
    print("\n🟡 快速搜索警告:")
    warnings = quick_search_warnings(limit=3)
    for entry in warnings:
        print(f"  [{entry.timestamp.strftime('%H:%M:%S')}] {entry.level} | {entry.logger_name} | {entry.message}")
    
    # 快速关键词搜索
    print("\n🔍 快速搜索关键词'解析':")
    parse_logs = quick_search_keyword('解析', limit=3)
    for entry in parse_logs:
        print(f"  [{entry.timestamp.strftime('%H:%M:%S')}] {entry.level} | {entry.logger_name} | {entry.message}")


def main():
    """主函数"""
    print("🚀 日志查询模块使用示例")
    print("=" * 50)
    
    try:
        basic_query_example()
        search_examples()
        advanced_query_example()
        export_example()
        quick_functions_example()
        
        print("\n" + "=" * 50)
        print("🎉 示例完成！")
        
    except Exception as e:
        print(f"❌ 示例运行失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
