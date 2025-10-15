"""
增量式分析模块

实现分批处理策略，智能判断何时停止分析，节省API成本。
"""

import json
import os
from typing import Dict, List, Any, Tuple
from pathlib import Path
import logging
from datetime import datetime
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from ..core.pymupdf_extractor import PyMuPDFExtractor
from .layered_analyzer import LayeredAnalyzer
from config import Config

# 设置日志
from ..utils.logger_config import get_logger
logger = get_logger(__name__)

class IncrementalAnalyzer:
    """增量式分析器"""
    
    def __init__(self):
        """初始化增量分析器"""
        self.layered_analyzer = LayeredAnalyzer()
        self.pdf_extractor = PyMuPDFExtractor(Config.JOURNALS_DIR, Config.EXTRACTED_DIR)
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        
        # 分析状态
        self.current_batch = 0
        self.total_papers = 0
        self.processed_papers = 0
        self.analysis_log = []
        
        # 确保日志文件存在
        self.log_file = Path(Config.ANALYSIS_LOG)
    
    def run_incremental_analysis(self) -> Dict:
        """
        运行增量式分析
        
        Returns:
            分析结果摘要
        """
        logger.info("开始增量式分析")
        
        try:
            # 获取所有提取的文本
            texts = self.pdf_extractor.get_extracted_texts()
            
            if not texts:
                return {'error': '没有找到提取的文本，请先运行PDF提取'}
            
            self.total_papers = len(texts)
            logger.info(f"找到 {self.total_papers} 篇论文")
            
            # 分批处理
            batches = self._create_batches(texts, Config.BATCH_SIZE)
            
            # 分析日志
            analysis_log = {
                'start_time': datetime.now().isoformat(),
                'total_papers': self.total_papers,
                'batch_size': Config.BATCH_SIZE,
                'batches': []
            }
            
            # 逐批分析
            for batch_idx, batch_texts in enumerate(batches):
                batch_id = f"batch_{batch_idx + 1:02d}"
                logger.info(f"处理批次 {batch_id}: {len(batch_texts)} 篇论文")
                
                batch_result = self._analyze_batch(batch_id, batch_texts)
                analysis_log['batches'].append(batch_result)
                
                # 检查是否应该停止
                if self._should_stop_analysis(batch_result, analysis_log['batches']):
                    logger.info(f"风格已稳定，在第 {batch_idx + 1} 批停止分析")
                    break
            
            # 生成最终风格指南
            final_guide = self._generate_final_style_guide(analysis_log['batches'])
            
            # 完成分析日志
            analysis_log['end_time'] = datetime.now().isoformat()
            analysis_log['final_guide'] = final_guide
            analysis_log['early_stop'] = len(analysis_log['batches']) < len(batches)
            
            # 保存分析日志
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(analysis_log, f, ensure_ascii=False, indent=2)
            
            logger.info("增量式分析完成")
            return analysis_log
            
        except Exception as e:
            logger.error(f"增量式分析失败: {str(e)}")
            return {'error': str(e)}
    
    def _create_batches(self, texts: List[Tuple[str, str]], batch_size: int) -> List[List[Tuple[str, str]]]:
        """
        创建分析批次
        
        Args:
            texts: 文本列表
            batch_size: 批次大小
            
        Returns:
            批次列表
        """
        batches = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batches.append(batch)
        
        return batches
    
    def _check_existing_reports(self, paper_ids: List[str]) -> Dict[str, bool]:
        """
        检查哪些论文已经有有效的分析报告
        
        Args:
            paper_ids: 论文ID列表
            
        Returns:
            论文ID到是否存在有效报告的映射
        """
        existing_reports = {}
        individual_reports_dir = Path(Config.INDIVIDUAL_REPORTS_DIR)
        
        for paper_id in paper_ids:
            report_file = individual_reports_dir / f"{paper_id}.json"
            
            if not report_file.exists():
                existing_reports[paper_id] = False
                continue
            
            # 检查报告是否有效（没有解析错误）
            try:
                with open(report_file, 'r', encoding='utf-8') as f:
                    report_data = json.load(f)
                
                # 检查是否有GPT解析错误
                gpt_analysis = report_data.get('gpt_analysis', {})
                if 'parse_error' in gpt_analysis:
                    logger.warning(f"发现解析错误的报告，将重新分析: {paper_id}")
                    existing_reports[paper_id] = False
                else:
                    existing_reports[paper_id] = True
                    
            except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
                logger.warning(f"报告文件损坏，将重新分析: {paper_id}, 错误: {str(e)}")
                existing_reports[paper_id] = False
        
        return existing_reports
    
    def _load_existing_report(self, paper_id: str) -> Dict:
        """
        加载已存在的分析报告
        
        Args:
            paper_id: 论文ID
            
        Returns:
            分析报告
        """
        report_file = Path(Config.INDIVIDUAL_REPORTS_DIR) / f"{paper_id}.json"
        try:
            with open(report_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"加载已存在报告失败 {paper_id}: {str(e)}")
            return None

    def _analyze_batch(self, batch_id: str, batch_texts: List[Tuple[str, str]]) -> Dict:
        """
        分析单个批次
        
        Args:
            batch_id: 批次ID
            batch_texts: 批次文本列表
            
        Returns:
            批次分析结果
        """
        start_time = datetime.now()
        
        try:
            # 检查已存在的报告
            paper_ids = [paper_id for paper_id, _ in batch_texts]
            existing_reports = self._check_existing_reports(paper_ids)
            
            # 统计跳过和需要分析的论文
            skipped_count = sum(existing_reports.values())
            need_analysis_count = len(paper_ids) - skipped_count
            
            logger.info(f"批次 {batch_id}: {skipped_count} 篇已分析，{need_analysis_count} 篇需要分析")
            
            # 单篇分析
            individual_reports = []
            for paper_id, paper_text in batch_texts:
                if existing_reports[paper_id]:
                    # 加载已存在的报告
                    logger.info(f"跳过已分析的论文: {paper_id}")
                    existing_report = self._load_existing_report(paper_id)
                    if existing_report:
                        individual_reports.append(existing_report)
                    else:
                        # 如果加载失败，重新分析
                        logger.warning(f"重新分析论文: {paper_id}")
                        report = self.layered_analyzer.analyze_individual_paper(paper_id, paper_text)
                        individual_reports.append(report)
                else:
                    # 使用完整文本进行分析
                    logger.info(f"分析新论文: {paper_id}")
                    report = self.layered_analyzer.analyze_individual_paper(paper_id, paper_text)
                    individual_reports.append(report)
            
            # 批次汇总 - 总是重新生成，因为批次结构可能变化
            logger.info(f"生成批次汇总: {batch_id}")
            batch_summary = self.layered_analyzer.analyze_batch(batch_id, individual_reports)
            
            # 计算批次统计
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            batch_result = {
                'batch_id': batch_id,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_seconds': duration,
                'paper_count': len(batch_texts),
                'skipped_count': skipped_count,
                'analyzed_count': need_analysis_count,
                'individual_reports': [report.get('paper_id') for report in individual_reports],
                'batch_summary': batch_summary,
                'success': 'error' not in batch_summary
            }
            
            self.processed_papers += len(batch_texts)
            logger.info(f"完成批次 {batch_id}: {len(batch_texts)} 篇论文 (跳过 {skipped_count} 篇individual_reports，分析 {need_analysis_count} 篇，重新生成batch_summary)，耗时 {duration:.2f} 秒")
            
            return batch_result
            
        except Exception as e:
            logger.error(f"批次分析失败 {batch_id}: {str(e)}")
            return {
                'batch_id': batch_id,
                'error': str(e),
                'start_time': start_time.isoformat(),
                'end_time': datetime.now().isoformat(),
                'success': False
            }
    
    def _should_stop_analysis(self, current_batch: Dict, all_batches: List[Dict]) -> bool:
        """
        判断是否应该停止分析
        
        Args:
            current_batch: 当前批次结果
            all_batches: 所有批次结果
            
        Returns:
            是否应该停止
        """
        # 如果当前批次失败，继续分析
        if not current_batch.get('success', False):
            return False
        
        # 至少需要2个批次才能比较
        if len(all_batches) < 2:
            return False
        
        # 检查连续相似性
        if len(all_batches) >= 2:
            last_two_batches = all_batches[-2:]
            
            # 计算最近两个批次的相似度
            similarity = self._calculate_batch_similarity(
                last_two_batches[0]['batch_summary'],
                last_two_batches[1]['batch_summary']
            )
            
            logger.info(f"批次相似度: {similarity:.3f}")
            
            # 如果相似度超过阈值，停止分析
            if similarity > Config.SIMILARITY_THRESHOLD:
                return True
        
        # 检查是否已分析足够多的论文
        if self.processed_papers >= Config.MAX_PAPERS:
            logger.info(f"已分析 {self.processed_papers} 篇论文，达到最大限制")
            return True
        
        return False
    
    def _calculate_batch_similarity(self, batch1: Dict, batch2: Dict) -> float:
        """
        计算两个批次的相似度
        
        Args:
            batch1: 第一个批次汇总
            batch2: 第二个批次汇总
            
        Returns:
            相似度分数 (0-1)
        """
        try:
            # 提取批次的文本特征
            text1 = self._extract_batch_features(batch1)
            text2 = self._extract_batch_features(batch2)
            
            if not text1 or not text2:
                return 0.0
            
            # 使用TF-IDF计算相似度
            tfidf_matrix = self.vectorizer.fit_transform([text1, text2])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"计算批次相似度失败: {str(e)}")
            return 0.0
    
    def _extract_batch_features(self, batch_summary: Dict) -> str:
        """
        从批次汇总中提取文本特征
        
        Args:
            batch_summary: 批次汇总结果
            
        Returns:
            特征文本
        """
        if 'error' in batch_summary:
            return ""
        
        features = []
        
        # 提取共同模式
        if 'common_patterns' in batch_summary:
            patterns = batch_summary['common_patterns']
            for pattern_type, pattern_data in patterns.items():
                if isinstance(pattern_data, dict):
                    for key, value in pattern_data.items():
                        if isinstance(value, (str, int, float)):
                            features.append(f"{pattern_type}_{key}_{value}")
        
        # 提取初步规则
        if 'preliminary_rules' in batch_summary:
            for rule in batch_summary['preliminary_rules']:
                if isinstance(rule, dict) and 'description' in rule:
                    features.append(rule['description'])
        
        return " ".join(features)
    
    def _generate_final_style_guide(self, batch_results: List[Dict]) -> Dict:
        """
        生成最终风格指南
        
        Args:
            batch_results: 所有批次结果
            
        Returns:
            最终风格指南
        """
        try:
            # 收集所有成功的批次汇总
            successful_summaries = []
            for batch in batch_results:
                if batch.get('success', False) and 'batch_summary' in batch:
                    summary = batch['batch_summary']
                    if 'error' not in summary:
                        successful_summaries.append(summary)
            
            if not successful_summaries:
                return {'error': '没有成功的批次汇总'}
            
            # 使用分层分析器生成最终风格指南
            final_guide = self.layered_analyzer.integrate_global_style(successful_summaries)
            
            return final_guide
            
        except Exception as e:
            logger.error(f"生成最终风格指南失败: {str(e)}")
            return {'error': str(e)}
    
    def get_analysis_progress(self) -> Dict:
        """
        获取分析进度
        
        Returns:
            分析进度信息
        """
        if not self.log_file.exists():
            return {'status': 'not_started'}
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
            
            return {
                'status': 'in_progress' if 'end_time' not in log_data else 'completed',
                'total_papers': log_data.get('total_papers', 0),
                'batches_completed': len(log_data.get('batches', [])),
                'early_stop': log_data.get('early_stop', False),
                'start_time': log_data.get('start_time'),
                'end_time': log_data.get('end_time')
            }
            
        except Exception as e:
            return {'error': f'读取分析日志失败: {str(e)}'}
    
    def resume_analysis(self) -> Dict:
        """
        恢复中断的分析
        
        Returns:
            恢复分析结果
        """
        if not self.log_file.exists():
            return {'error': '没有找到分析日志'}
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
            
            # 检查是否已完成
            if 'end_time' in log_data:
                return {'message': '分析已完成', 'log': log_data}
            
            # 恢复分析
            logger.info("恢复中断的分析")
            return self.run_incremental_analysis()
            
        except Exception as e:
            return {'error': f'恢复分析失败: {str(e)}'}

def main():
    """测试增量分析功能"""
    # 验证配置
    Config.validate()
    
    # 创建增量分析器
    analyzer = IncrementalAnalyzer()
    
    # 运行分析
    result = analyzer.run_incremental_analysis()
    
    print("增量分析结果:")
    print(f"状态: {'error' in result and '错误' or '成功'}")
    if 'error' not in result:
        print(f"总论文数: {result.get('total_papers', 0)}")
        print(f"完成批次数: {len(result.get('batches', []))}")
        print(f"是否提前停止: {result.get('early_stop', False)}")
    else:
        print(f"错误: {result['error']}")

if __name__ == "__main__":
    main()
