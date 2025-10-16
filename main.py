"""
论文风格分析与润色系统 - 命令行界面

主程序入口，提供风格分析和论文润色功能。
"""

import click
import json
import os
import sys
from pathlib import Path
import logging
from datetime import datetime

# 添加src目录到路径
sys.path.append(str(Path(__file__).parent / 'src'))

from config import Config
from src.core.pymupdf_extractor import PyMuPDFExtractor
from src.analysis.incremental_analyzer import IncrementalAnalyzer
from src.analysis.layered_analyzer import LayeredAnalyzer
from src.polishing.multi_round_polisher import MultiRoundPolisher
from src.analysis.quality_scorer import QualityScorer
from src.analysis.style_guide_generator import StyleGuideGenerator

# 设置日志
from src.utils.logger_config import setup_logging, get_logger
setup_logging()
logger = get_logger(__name__)

@click.group()
def cli():
    """论文风格分析与润色系统"""
    pass

@cli.command()
@click.option('--input', '-i', default=Config.JOURNALS_DIR, 
              help='期刊PDF文件目录')
@click.option('--output', '-o', default=Config.STYLE_GUIDE_JSON,
              help='风格指南输出文件')
@click.option('--batch-size', '-b', default=Config.BATCH_SIZE,
              help='每批分析的论文数量')
@click.option('--max-papers', '-m', default=Config.MAX_PAPERS,
              help='最大分析论文数量')
@click.option('--resume', is_flag=True, help='恢复中断的分析')
def analyze(input, output, batch_size, max_papers, resume):
    """分析期刊论文，生成风格指南"""
    click.echo("🔍 开始期刊论文风格分析...")
    
    try:
        # 验证配置
        Config.validate()
        
        # 更新配置
        Config.BATCH_SIZE = batch_size
        Config.MAX_PAPERS = max_papers
        
        # 创建分析器
        analyzer = IncrementalAnalyzer()
        
        if resume:
            # 恢复分析
            result = analyzer.resume_analysis()
        else:
            # 运行分析
            result = analyzer.run_incremental_analysis()
        
        if 'error' in result:
            click.echo(f"❌ 分析失败: {result['error']}", err=True)
            sys.exit(1)
        
        # 显示结果摘要
        click.echo("\n📊 分析结果摘要:")
        click.echo(f"  总论文数: {result.get('total_papers', 0)}")
        click.echo(f"  完成批次数: {len(result.get('batches', []))}")
        click.echo(f"  是否提前停止: {'是' if result.get('early_stop') else '否'}")
        click.echo(f"  分析时长: {result.get('end_time', '未知')}")
        
        # 检查最终风格指南
        final_guide = result.get('final_guide', {})
        if 'rules' in final_guide:
            click.echo(f"  生成规则数: {len(final_guide['rules'])}")
            core_rules = len([r for r in final_guide['rules'] if r.get('rule_type') == 'core'])
            optional_rules = len([r for r in final_guide['rules'] if r.get('rule_type') == 'optional'])
            click.echo(f"  核心规则: {core_rules} 条")
            click.echo(f"  可选规则: {optional_rules} 条")
        
        click.echo(f"\n✅ 风格指南已保存到: {output}")
        
    except Exception as e:
        click.echo(f"❌ 分析过程中出现错误: {str(e)}", err=True)
        logger.exception("分析失败")
        sys.exit(1)

@cli.command()
@click.option('--max-papers', '-m', default=None, type=int,
              help='最大分析论文数量，不指定则分析所有')
@click.option('--resume', is_flag=True, help='从上次中断的地方继续分析')
@click.option('--progress', is_flag=True, help='显示分析进度')
def analyze_individual(max_papers, resume, progress):
    """分析所有单个PDF文件（独立于批量分析）"""
    click.echo("🔍 开始分析所有单个PDF文件...")
    
    try:
        # 验证配置
        Config.validate()
        
        # 创建分析器
        analyzer = LayeredAnalyzer()
        
        # 显示进度（如果启用）
        if progress:
            import threading
            import time
            
            def show_progress():
                while True:
                    progress_info = analyzer.get_analysis_progress()
                    if progress_info['total_files'] > 0:
                        completed = progress_info['completed_files']
                        total = progress_info['total_files']
                        current = progress_info['current_file']
                        failed = progress_info['failed_files']
                        
                        click.echo(f"\r📊 进度: {completed}/{total} 完成, {failed} 失败 | 当前: {current}", nl=False)
                        
                        if completed + failed >= total:
                            break
                    time.sleep(5)
            
            # 启动进度显示线程
            progress_thread = threading.Thread(target=show_progress, daemon=True)
            progress_thread.start()
        
        # 开始分析
        result = analyzer.analyze_all_individual_papers(
            max_papers=max_papers,
            resume=resume
        )
        
        if 'error' in result:
            click.echo(f"❌ 分析失败: {result['error']}")
            sys.exit(1)
        
        # 显示结果摘要
        click.echo(f"\n✅ 单个文件分析完成!")
        click.echo(f"📊 分析摘要:")
        click.echo(f"  总文件数: {result['total_papers']}")
        click.echo(f"  成功分析: {result['successful_papers']}")
        click.echo(f"  分析失败: {result['failed_papers']}")
        click.echo(f"  成功率: {result['success_rate']:.1%}")
        
        if result['text_statistics']['avg_text_length'] > 0:
            click.echo(f"📝 文本统计:")
            click.echo(f"  平均文本长度: {result['text_statistics']['avg_text_length']:.0f} 字符")
            click.echo(f"  平均词数: {result['text_statistics']['avg_word_count']:.0f} 词")
        
        if result['failed_papers']:
            click.echo(f"❌ 失败的文件:")
            for paper_id in result['failed_papers']:
                click.echo(f"  - {paper_id}")
        
        # 保存分析摘要
        summary_file = Path("data/individual_analysis_summary.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        click.echo(f"💾 分析摘要已保存到: {summary_file}")
        
    except Exception as e:
        logger.error(f"单个文件分析失败: {str(e)}")
        click.echo(f"❌ 分析失败: {str(e)}")
        sys.exit(1)

@cli.command()
@click.option('--text', '-t', help='论文文本内容')
@click.option('--file', '-f', help='论文文件路径')
@click.option('--interactive/--no-interactive', default=True, 
              help='是否使用交互模式')
@click.option('--output', '-o', help='润色结果输出文件')
def polish(text, file, interactive, output):
    """润色论文"""
    click.echo("✨ 开始论文润色...")
    
    try:
        # 验证配置
        Config.validate()
        
        # 获取论文文本
        if text:
            paper_text = text
        elif file:
            if not Path(file).exists():
                click.echo(f"❌ 文件不存在: {file}", err=True)
                sys.exit(1)
            with open(file, 'r', encoding='utf-8') as f:
                paper_text = f.read()
        else:
            click.echo("❌ 请提供论文文本 (-t) 或文件路径 (-f)", err=True)
            sys.exit(1)
        
        # 检查风格指南是否存在
        if not Path(Config.STYLE_GUIDE_JSON).exists():
            click.echo("❌ 风格指南不存在，请先运行分析命令", err=True)
            click.echo("   运行: python main.py analyze", err=True)
            sys.exit(1)
        
        # 创建润色器
        polisher = MultiRoundPolisher()
        
        # 润色论文
        result = polisher.polish_paper(paper_text, interactive=interactive)
        
        if not result.get('success', False):
            click.echo(f"❌ 润色失败: {result.get('error', '未知错误')}", err=True)
            sys.exit(1)
        
        # 显示结果
        click.echo("\n📈 润色结果:")
        before_score = result.get('before_scores', {}).get('overall_score', 0)
        after_score = result.get('after_scores', {}).get('overall_score', 0)
        improvement = result.get('score_comparison', {}).get('overall_improvement', 0)
        
        click.echo(f"  润色前总分: {before_score:.1f}")
        click.echo(f"  润色后总分: {after_score:.1f}")
        click.echo(f"  改进幅度: +{improvement:.1f} 分")
        
        # 显示各维度改进
        comparison = result.get('score_comparison', {})
        click.echo(f"  风格匹配: +{comparison.get('style_improvement', 0):.1f}")
        click.echo(f"  学术规范: +{comparison.get('academic_improvement', 0):.1f}")
        click.echo(f"  可读性: +{comparison.get('readability_improvement', 0):.1f}")
        
        # 显示修改统计
        summary = result.get('polishing_summary', {})
        click.echo(f"\n📝 修改统计:")
        click.echo(f"  润色轮数: {summary.get('total_rounds', 0)}")
        click.echo(f"  应用修改: {summary.get('total_modifications_applied', 0)} 处")
        
        # 保存结果
        if output:
            polisher.save_polished_result(result, output)
            click.echo(f"\n💾 润色结果已保存到: {output}")
        
        # 显示润色后的文本
        click.echo("\n📄 润色后的论文:")
        click.echo("-" * 50)
        click.echo(result.get('polished_text', ''))
        click.echo("-" * 50)
        
        click.echo("\n✅ 论文润色完成!")
        
    except Exception as e:
        click.echo(f"❌ 润色过程中出现错误: {str(e)}", err=True)
        logger.exception("润色失败")
        sys.exit(1)

@cli.command()
@click.option('--text', '-t', help='论文文本内容')
@click.option('--file', '-f', help='论文文件路径')
def score(text, file):
    """评估论文质量"""
    click.echo("📊 开始论文质量评估...")
    
    try:
        # 验证配置
        Config.validate()
        
        # 获取论文文本
        if text:
            paper_text = text
        elif file:
            if not Path(file).exists():
                click.echo(f"❌ 文件不存在: {file}", err=True)
                sys.exit(1)
            with open(file, 'r', encoding='utf-8') as f:
                paper_text = f.read()
        else:
            click.echo("❌ 请提供论文文本 (-t) 或文件路径 (-f)", err=True)
            sys.exit(1)
        
        # 创建评分器
        scorer = QualityScorer()
        
        # 评分
        scores = scorer.score_paper(paper_text)
        
        if 'error' in scores:
            click.echo(f"❌ 评分失败: {scores['error']}", err=True)
            sys.exit(1)
        
        # 显示评分结果
        click.echo("\n📈 质量评分结果:")
        click.echo(f"  总分: {scores.get('overall_score', 0):.1f}/100")
        
        style_score = scores.get('style_match', {}).get('score', 0)
        academic_score = scores.get('academic_standard', {}).get('score', 0)
        readability_score = scores.get('readability', {}).get('score', 0)
        
        click.echo(f"  风格匹配: {style_score:.1f}/100")
        click.echo(f"  学术规范: {academic_score:.1f}/100")
        click.echo(f"  可读性: {readability_score:.1f}/100")
        
        # 显示详细分析
        detailed = scores.get('detailed_analysis', {})
        if detailed:
            basic_stats = detailed.get('basic_stats', {})
            click.echo(f"\n📝 基础统计:")
            click.echo(f"  字数: {basic_stats.get('word_count', 0)}")
            click.echo(f"  句数: {basic_stats.get('sentence_count', 0)}")
            click.echo(f"  平均句长: {basic_stats.get('avg_words_per_sentence', 0):.1f} 词")
        
        # 显示建议
        recommendations = scores.get('recommendations', [])
        if recommendations:
            click.echo(f"\n💡 改进建议:")
            for i, rec in enumerate(recommendations, 1):
                click.echo(f"  {i}. {rec}")
        
        click.echo("\n✅ 质量评估完成!")
        
    except Exception as e:
        click.echo(f"❌ 评估过程中出现错误: {str(e)}", err=True)
        logger.exception("评估失败")
        sys.exit(1)

@cli.command()
def status():
    """查看系统状态"""
    click.echo("📊 系统状态检查...")
    
    try:
        # 检查配置
        Config.validate()
        click.echo("✅ 配置验证通过")
        
        # 检查数据目录
        data_dirs = [
            Config.JOURNALS_DIR,
            Config.EXTRACTED_DIR,
            Config.INDIVIDUAL_REPORTS_DIR,
            Config.BATCH_SUMMARIES_DIR
        ]
        
        for dir_path in data_dirs:
            if Path(dir_path).exists():
                file_count = len(list(Path(dir_path).glob('*')))
                click.echo(f"✅ {dir_path}: {file_count} 个文件")
            else:
                click.echo(f"❌ {dir_path}: 目录不存在")
        
        # 检查混合风格指南
        hybrid_guide_path = Path('data/hybrid_style_guide.json')
        if hybrid_guide_path.exists():
            with open(hybrid_guide_path, 'r', encoding='utf-8') as f:
                guide = json.load(f)
            rules_count = guide.get('total_rules', 0)
            official_count = guide.get('official_rules_count', 0)
            empirical_count = guide.get('empirical_rules_count', 0)
            click.echo(f"✅ 混合风格指南: {rules_count} 条规则 (官方: {official_count}, 经验: {empirical_count})")
        else:
            click.echo("❌ 混合风格指南: 不存在")
        
        # 检查分析日志
        if Path(Config.ANALYSIS_LOG).exists():
            with open(Config.ANALYSIS_LOG, 'r', encoding='utf-8') as f:
                log = json.load(f)
            batches_count = len(log.get('batches', []))
            click.echo(f"✅ 分析日志: {batches_count} 个批次")
        else:
            click.echo("❌ 分析日志: 不存在")
        
        # 检查PDF提取结果
        extractor = PyMuPDFExtractor(Config.JOURNALS_DIR, Config.EXTRACTED_DIR)
        summary = extractor.get_extraction_summary()
        if 'total_files' in summary:
            click.echo(f"✅ PDF提取: {summary['successful_extractions']}/{summary['total_files']} 成功")
        else:
            click.echo("❌ PDF提取: 尚未执行")
        
    except Exception as e:
        click.echo(f"❌ 状态检查失败: {str(e)}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--input', '-i', default=Config.JOURNALS_DIR, 
              help='期刊PDF文件目录')
@click.option('--output', '-o', default=Config.EXTRACTED_DIR,
              help='提取文本输出目录')
def extract(input, output):
    """提取PDF文本"""
    click.echo("📄 开始PDF文本提取...")
    
    try:
        # 使用PyMuPDF提取器
        extractor = PyMuPDFExtractor(input, output)
        
        # 执行提取
        results = extractor.extract_all_pdfs()
        
        if results.get('success') is False:
            click.echo(f"❌ 提取失败: {results.get('message', '未知错误')}", err=True)
            sys.exit(1)
        
        # 显示结果
        click.echo(f"\n📊 提取结果:")
        click.echo(f"  总文件数: {results.get('total_files', 0)}")
        click.echo(f"  成功提取: {results.get('successful_extractions', 0)}")
        click.echo(f"  提取失败: {results.get('failed_extractions', 0)}")
        click.echo(f"  总字符数: {results.get('total_characters', 0):,}")
        
        # 显示布局分析结果
        if 'extraction_details' in results:
            two_column_files = 0
            for detail in results['extraction_details']:
                if detail.get('success') and 'layout_info' in detail:
                    if detail['layout_info'].get('is_two_column', False):
                        two_column_files += 1
            click.echo(f"  双栏布局文件: {two_column_files}")
        
        click.echo(f"\n✅ 文本提取完成，结果保存到: {output}")
        
    except Exception as e:
        click.echo(f"❌ 提取过程中出现错误: {str(e)}", err=True)
        logger.exception("提取失败")
        sys.exit(1)

@cli.command()
def guide():
    """查看风格指南"""
    click.echo("📖 风格指南...")
    
    try:
        # 检查风格指南是否存在
        if not Path(Config.STYLE_GUIDE_JSON).exists():
            click.echo("❌ 风格指南不存在，请先运行分析命令", err=True)
            click.echo("   运行: python main.py analyze", err=True)
            sys.exit(1)
        
        # 加载风格指南
        with open(Config.STYLE_GUIDE_JSON, 'r', encoding='utf-8') as f:
            guide = json.load(f)
        
        # 显示摘要
        click.echo(f"\n📊 风格指南摘要:")
        click.echo(f"  版本: {guide.get('style_guide_version', '未知')}")
        click.echo(f"  生成时间: {guide.get('generation_date', '未知')}")
        click.echo(f"  分析论文数: {guide.get('total_papers_analyzed', 0)}")
        
        rule_summary = guide.get('rule_summary', {})
        click.echo(f"  总规则数: {rule_summary.get('total_rules', 0)}")
        click.echo(f"  核心规则: {rule_summary.get('core_rules', 0)}")
        click.echo(f"  可选规则: {rule_summary.get('optional_rules', 0)}")
        
        # 显示核心规则
        rules = guide.get('rules', [])
        core_rules = [r for r in rules if r.get('rule_type') == 'core']
        
        if core_rules:
            click.echo(f"\n🎯 核心规则 (前5条):")
            for i, rule in enumerate(core_rules[:5], 1):
                click.echo(f"  {i}. {rule.get('description', '')}")
                click.echo(f"     遵循率: {rule.get('frequency', 0):.1%}")
                click.echo()
        
        # 显示类别
        categories = guide.get('categories', {})
        if categories:
            click.echo(f"\n📂 规则类别:")
            for category, category_rules in categories.items():
                click.echo(f"  {category}: {len(category_rules)} 条规则")
        
        click.echo(f"\n💡 完整风格指南请查看: {Config.STYLE_GUIDE_MD}")
        
    except Exception as e:
        click.echo(f"❌ 查看风格指南失败: {str(e)}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--official-guide', default=os.path.join(Config.OFFICIAL_GUIDES_DIR, 'AMJ_style_guide.pdf'), 
              help='官方风格指南PDF文件路径')
@click.option('--output', default='data/hybrid_style_guide.json',
              help='输出混合风格指南文件路径')
@click.option('--validate', is_flag=True, help='是否进行规则验证')
@click.option('--force-refresh', is_flag=True, help='强制重新解析官方指南（忽略缓存）')
def integrate_guide(official_guide, output, validate, force_refresh):
    """整合官方风格指南与往期期刊分析结果"""
    try:
        click.echo("🔄 开始整合官方风格指南...")
        
        # 导入必要的模块
        from src.core.official_guide_parser import OfficialGuideParser
        from src.analysis.style_guide_generator import StyleGuideGenerator
        from src.analysis.rule_validator import RuleValidator
        import json
        from pathlib import Path
        
        # 1. 解析官方指南
        parser = OfficialGuideParser()
        
        if parser.has_cache() and not force_refresh:
            click.echo("📖 发现官方规则缓存，直接加载...")
        else:
            if force_refresh:
                click.echo("📖 强制重新解析官方风格指南...")
            else:
                click.echo("📖 首次解析官方风格指南...")
        
        official_result = parser.parse_official_guide(official_guide, force_refresh=force_refresh)
        
        if 'error' in official_result:
            click.echo(f"❌ 解析官方指南失败: {official_result['error']}", err=True)
            sys.exit(1)
        
        official_rules = official_result.get('rules', [])
        click.echo(f"✅ 成功解析 {len(official_rules)} 条官方规则")
        
        # 2. 加载经验规则
        click.echo("📊 加载往期期刊分析结果...")
        generator = StyleGuideGenerator()
        empirical_data = None
        
        if Path(Config.STYLE_GUIDE_JSON).exists():
            with open(Config.STYLE_GUIDE_JSON, 'r', encoding='utf-8') as f:
                empirical_data = json.load(f)
            click.echo("✅ 成功加载经验规则")
        else:
            click.echo("⚠️  未找到往期期刊分析结果，将仅使用官方规则")
        
        # 3. 生成混合指南
        click.echo("🔀 生成混合风格指南...")
        hybrid_guide = generator.generate_hybrid_guide(
            official_rules=official_rules,
            empirical_data=empirical_data
        )
        
        if 'error' in hybrid_guide:
            click.echo(f"❌ 生成混合指南失败: {hybrid_guide['error']}", err=True)
            sys.exit(1)
        
        # 4. 规则验证（如果启用）
        if validate:
            click.echo("🔍 进行规则验证...")
            validator = RuleValidator()
            validation_report = validator.validate_rules(
                official_rules=official_rules,
                empirical_rules=empirical_data.get('rules', []) if empirical_data else []
            )
            
            if 'error' not in validation_report:
                validator.save_validation_report(validation_report)
                click.echo("✅ 规则验证完成")
            else:
                click.echo(f"⚠️  规则验证失败: {validation_report['error']}")
        
        # 5. 保存混合指南
        click.echo("💾 保存混合风格指南...")
        output_file = Path(output)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(hybrid_guide, f, ensure_ascii=False, indent=2)
        
        # 6. 生成人类可读版本
        markdown_output = output.replace('.json', '.md')
        generator.save_style_guide_markdown(hybrid_guide, markdown_output)
        
        # 7. 显示结果摘要
        click.echo("\n🎉 混合风格指南整合完成!")
        click.echo(f"📄 官方规则: {hybrid_guide.get('official_rules_count', 0)} 条")
        click.echo(f"📊 经验规则: {hybrid_guide.get('empirical_rules_count', 0)} 条")
        click.echo(f"📋 总规则数: {hybrid_guide.get('total_rules', 0)} 条")
        click.echo(f"📁 JSON文件: {output}")
        click.echo(f"📖 Markdown文件: {markdown_output}")
        
        if validate:
            click.echo(f"📊 验证报告: data/rule_validation_report.json")
        
    except Exception as e:
        click.echo(f"❌ 整合失败: {str(e)}", err=True)
        sys.exit(1)

@cli.command()
def cache_status():
    """检查官方规则缓存状态"""
    try:
        from src.core.official_guide_parser import OfficialGuideParser
        parser = OfficialGuideParser()
        
        if parser.has_cache():
            click.echo("✅ 官方规则缓存存在")
            # 尝试加载缓存信息
            cached_result = parser._load_from_cache()
            if cached_result:
                click.echo(f"   规则数量: {cached_result.get('total_rules', 0)}")
                click.echo(f"   解析时间: {cached_result.get('parsing_date', '未知')}")
                click.echo(f"   源文件: {cached_result.get('source_file', '未知')}")
            else:
                click.echo("   ⚠️ 缓存文件损坏")
        else:
            click.echo("❌ 官方规则缓存不存在")
            click.echo("   运行 'python main.py integrate_guide' 生成缓存")
        
    except Exception as e:
        click.echo(f"❌ 检查缓存状态失败: {str(e)}", err=True)
        sys.exit(1)

@cli.command()
def clear_cache():
    """清除官方规则缓存"""
    try:
        click.echo("🗑️ 清除官方规则缓存...")
        
        from src.core.official_guide_parser import OfficialGuideParser
        parser = OfficialGuideParser()
        parser.clear_cache()
        
        click.echo("✅ 缓存已清除")
        
    except Exception as e:
        click.echo(f"❌ 清除缓存失败: {str(e)}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--input-dir', default='data/batch_summaries', 
              help='批次汇总文件目录')
@click.option('--output', default='data/style_guide.json',
              help='输出风格指南文件路径')
def generate_guide(input_dir, output):
    """从批次汇总文件生成最终的风格指南"""
    click.echo("🔄 开始从批次汇总生成风格指南...")
    
    try:
        # 导入必要的模块
        from src.analysis.layered_analyzer import LayeredAnalyzer
        import json
        from pathlib import Path
        
        # 检查输入目录
        input_path = Path(input_dir)
        if not input_path.exists():
            click.echo(f"❌ 输入目录不存在: {input_dir}", err=True)
            sys.exit(1)
        
        # 收集所有批次汇总文件
        batch_files = sorted(input_path.glob('batch_*.json'))
        if not batch_files:
            click.echo(f"❌ 在 {input_dir} 中未找到批次汇总文件", err=True)
            sys.exit(1)
        
        click.echo(f"📊 找到 {len(batch_files)} 个批次汇总文件")
        
        # 加载批次汇总数据
        batch_summaries = []
        for batch_file in batch_files:
            with open(batch_file, 'r', encoding='utf-8') as f:
                batch_data = json.load(f)
                batch_summaries.append(batch_data)
                
                # 显示批次信息
                batch_id = batch_data.get('batch_id', batch_file.stem)
                paper_count = batch_data.get('paper_count', 0)
                rules_count = len(batch_data.get('comprehensive_rules', []))
                click.echo(f"  📄 {batch_id}: {paper_count} 篇论文, {rules_count} 条规则")
        
        # 创建分析器并生成风格指南
        click.echo("🤖 开始全局风格整合...")
        analyzer = LayeredAnalyzer()
        
        style_guide = analyzer.integrate_global_style_union(batch_summaries)
        
        if 'error' in style_guide:
            click.echo(f"❌ 生成风格指南失败: {style_guide['error']}", err=True)
            sys.exit(1)
        
        # 显示结果摘要
        total_papers = style_guide.get('total_papers_analyzed', 0)
        total_batches = style_guide.get('total_batches', 0)
        
        click.echo(f"\n🎉 风格指南生成完成!")
        click.echo(f"📊 处理摘要:")
        click.echo(f"  批次数: {total_batches}")
        click.echo(f"  论文数: {total_papers}")
        
        # 显示规则分类详情
        rule_categories = style_guide.get('rule_categories', {})
        if rule_categories:
            click.echo(f"\n📋 规则分类详情:")
            total_rules = 0
            
            for category_name, category_data in rule_categories.items():
                if isinstance(category_data, dict) and 'rules' in category_data:
                    rule_count = len(category_data['rules'])
                    total_rules += rule_count
                    
                    # 获取类别信息
                    threshold = category_data.get('threshold', 'N/A')
                    description = category_data.get('description', 'N/A')
                    
                    click.echo(f"  📌 {category_name}:")
                    click.echo(f"    阈值: {threshold}")
                    click.echo(f"    描述: {description}")
                    click.echo(f"    规则数: {rule_count} 条")
            
            click.echo(f"\n📊 总规则数: {total_rules} 条")
        else:
            click.echo(f"📋 总规则数: 0 条")
        
        click.echo(f"\n💾 风格指南已保存到: {output}")
        
        # 验证文件是否正确生成
        output_path = Path(output)
        if output_path.exists():
            with open(output_path, 'r', encoding='utf-8') as f:
                saved_guide = json.load(f)
            
            # 统计保存文件中的规则数量
            saved_rule_categories = saved_guide.get('rule_categories', {})
            saved_rules = 0
            
            click.echo(f"\n🔍 文件验证详情:")
            for category_name, category_data in saved_rule_categories.items():
                if isinstance(category_data, dict) and 'rules' in category_data:
                    rule_count = len(category_data['rules'])
                    saved_rules += rule_count
                    
                    threshold = category_data.get('threshold', 'N/A')
                    click.echo(f"  ✅ {category_name}: {rule_count} 条规则 (阈值: {threshold})")
            
            click.echo(f"✅ 验证成功: 文件包含 {saved_rules} 条规则")
        else:
            click.echo("⚠️ 警告: 输出文件未找到")
        
    except Exception as e:
        click.echo(f"❌ 生成过程中出现错误: {str(e)}", err=True)
        logger.exception("生成风格指南失败")
        sys.exit(1)

if __name__ == '__main__':
    cli()
