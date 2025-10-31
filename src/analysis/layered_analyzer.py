"""
分层风格分析引擎

实现单篇→批次→全局三层分析，区分核心规则和可选规则。
"""

import json
import os
from typing import Dict, List, Tuple
from pathlib import Path
from datetime import datetime

from ..utils.nlp_utils import NLPUtils
from ..core.prompts import PromptTemplates
from ..core.ai_client import get_ai_client, AICallError
from config import Config
from ..utils.style_dimensions import (
    map_rule_to_dimension,
    normalize_dimension_label,
)

# 设置日志
from ..utils.logger_config import get_logger

logger = get_logger(__name__)


class LayeredAnalyzer:
    """分层风格分析器"""

    def __init__(self, task_type: str = 'default'):
        """
        初始化分析器
        
        Args:
            task_type: 任务类型
                - 'default': 默认配置
                - 'individual': 单篇分析（使用deepseek-reasoner）
                - 'batch': 批次汇总
                - 'global': 全局整合
        """
        self.nlp_utils = NLPUtils()
        self.ai_client = get_ai_client()
        self.prompts = PromptTemplates()
        self.ai_config = Config.get_ai_config(task_type=task_type)
        self.task_type = task_type

        # 分层温度配置
        self.temperature_config = {
            "individual_analysis": 0.4,
            "batch_summary": 0.3,
            "global_integration": 0.2,
            "rule_generation": 0.35,
            "example_extraction": 0.4,
            "quality_assessment": 0.3,
            "consistency_check": 0.1,
        }

        # 分层max_tokens配置
        self.max_tokens_config = {
            "individual_analysis": 15000,
            "batch_summary": 20000,
            "global_integration": 25000,
            "rule_generation": 12000,
            "example_extraction": 10000,
            "quality_assessment": 8000,
            "consistency_check": 5000,
        }

        # 绝对最大值（防止API限制）
        self.absolute_max_tokens = 30000

        # 确保输出目录存在
        os.makedirs(Config.INDIVIDUAL_REPORTS_DIR, exist_ok=True)
        os.makedirs(Config.BATCH_SUMMARIES_DIR, exist_ok=True)

        # 分析进度跟踪
        self.analysis_progress = {
            "total_files": 0,
            "completed_files": 0,
            "failed_files": 0,
            "current_file": None,
        }

    def analyze_individual_paper(self, paper_id: str, paper_text: str) -> Dict:
        """
        第一层：单篇论文分析

        Args:
            paper_id: 论文ID
            paper_text: 论文文本

        Returns:
            单篇分析结果
        """
        logger.info(f"开始分析论文: {paper_id}")

        try:
            # 使用NLP工具进行基础分析
            nlp_analysis = {
                "sentence_structure": self.nlp_utils.analyze_sentence_structure(
                    paper_text
                ),
                "vocabulary": self.nlp_utils.analyze_vocabulary(paper_text),
                "paragraph_structure": self.nlp_utils.analyze_paragraph_structure(
                    paper_text
                ),
                "academic_expression": self.nlp_utils.analyze_academic_expression(
                    paper_text
                ),
            }

            # 使用GPT-4进行深度分析（使用风格特征分析方法）
            prompt = self.prompts.format_prompt(
                self.prompts.get_style_features_analysis_prompt(), paper_text=paper_text
            )

            logger.info(f"完整Prompt长度: {len(prompt)} 字符")

            # 输出完整的提示词到日志
            # logger.info("=" * 80)
            # logger.info("单个文件分析 - 完整提示词:")
            # logger.info("=" * 80)
            # logger.info(prompt)
            # logger.info("=" * 80)
            # logger.info("提示词结束")
            # logger.info("=" * 80)

            # 使用新的AI调用方法
            response_text = self._call_ai_api(prompt, "individual_analysis")
            gpt_analysis = self._parse_gpt_response(response_text)

            # 记录解析错误
            if "parse_error" in gpt_analysis:
                self._log_parsing_error(
                    Exception(gpt_analysis["parse_error"]),
                    response_text,
                    "individual_analysis:" + " + " + paper_id,
                )

            # 合并NLP分析和GPT分析
            combined_analysis = {
                "paper_id": paper_id,
                "analysis_date": datetime.now().isoformat(),
                "nlp_analysis": nlp_analysis,
                "gpt_analysis": gpt_analysis,
                "text_length": len(paper_text),
                "word_count": len(paper_text.split()),
            }

            # 保存分析结果
            output_file = Path(Config.INDIVIDUAL_REPORTS_DIR) / f"{paper_id}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(combined_analysis, f, ensure_ascii=False, indent=2)

            logger.info(f"完成论文分析: {paper_id}")
            return combined_analysis

        except Exception as e:
            logger.error(f"分析论文失败 {paper_id}: {str(e)}")
            return {
                "paper_id": paper_id,
                "error": str(e),
                "analysis_date": datetime.now().isoformat(),
            }

    def analyze_all_individual_papers(
        self, max_papers: int = None, resume: bool = False
    ) -> Dict:
        """
        分析所有单个PDF文件（独立于批量分析）

        Args:
            max_papers: 最大分析论文数量，None表示分析所有
            resume: 是否从上次中断的地方继续

        Returns:
            分析结果摘要
        """
        logger.info("开始分析所有单个PDF文件")

        try:
            # 获取所有提取的文本文件
            extracted_files = self._get_extracted_files()

            if not extracted_files:
                logger.warning("没有找到提取的文本文件")
                return {
                    "error": "没有找到提取的文本文件",
                    "analysis_date": datetime.now().isoformat(),
                }

            # 过滤已分析的文件（如果resume=False）
            if not resume:
                extracted_files = self._filter_unanalyzed_files(extracted_files)

            # 限制分析数量
            if max_papers and max_papers < len(extracted_files):
                extracted_files = extracted_files[:max_papers]

            # 更新进度信息
            self.analysis_progress.update(
                {
                    "total_files": len(extracted_files),
                    "completed_files": 0,
                    "failed_files": 0,
                    "current_file": None,
                }
            )

            logger.info(f"准备分析 {len(extracted_files)} 个文件")

            # 分析每个文件
            results = []
            for i, (paper_id, paper_text) in enumerate(extracted_files, 1):
                self.analysis_progress["current_file"] = paper_id
                logger.info(f"正在分析第 {i}/{len(extracted_files)} 个文件: {paper_id}")

                try:
                    result = self.analyze_individual_paper(paper_id, paper_text)
                    results.append(result)
                    self.analysis_progress["completed_files"] += 1

                    # 每分析10个文件输出一次进度
                    if i % 10 == 0:
                        logger.info(f"已完成 {i}/{len(extracted_files)} 个文件的分析")

                except Exception as e:
                    logger.error(f"分析文件 {paper_id} 失败: {str(e)}")
                    self.analysis_progress["failed_files"] += 1

                    # 记录失败的文件
                    error_result = {
                        "paper_id": paper_id,
                        "error": str(e),
                        "analysis_date": datetime.now().isoformat(),
                    }
                    results.append(error_result)

            # 生成分析摘要
            summary = self._generate_analysis_summary(results)

            logger.info(
                f"单个文件分析完成: 成功 {self.analysis_progress['completed_files']} 个, 失败 {self.analysis_progress['failed_files']} 个"
            )

            return summary

        except Exception as e:
            logger.error(f"分析所有单个文件失败: {str(e)}")
            return {"error": str(e), "analysis_date": datetime.now().isoformat()}

    def _get_extracted_files(self) -> List[Tuple[str, str]]:
        """
        获取所有提取的文本文件

        Returns:
            (paper_id, paper_text) 元组列表
        """
        extracted_files = []
        extracted_dir = Path(Config.EXTRACTED_DIR)

        if not extracted_dir.exists():
            logger.warning(f"提取目录不存在: {extracted_dir}")
            return extracted_files

        for txt_file in extracted_dir.glob("*.txt"):
            try:
                with open(txt_file, "r", encoding="utf-8") as f:
                    paper_text = f.read()

                # 使用文件名（不含扩展名）作为paper_id
                paper_id = txt_file.stem
                extracted_files.append((paper_id, paper_text))

            except Exception as e:
                logger.warning(f"读取文件 {txt_file} 失败: {str(e)}")
                continue

        # 按文件名排序
        extracted_files.sort(key=lambda x: x[0])
        return extracted_files

    def _filter_unanalyzed_files(
        self, extracted_files: List[Tuple[str, str]]
    ) -> List[Tuple[str, str]]:
        """
        过滤掉已经分析过的文件

        Args:
            extracted_files: 提取的文件列表

        Returns:
            未分析的文件列表
        """
        unanalyzed_files = []
        reports_dir = Path(Config.INDIVIDUAL_REPORTS_DIR)

        for paper_id, paper_text in extracted_files:
            report_file = reports_dir / f"{paper_id}.json"

            # 如果报告文件不存在，或者文件为空，或者包含错误，则重新分析
            if not report_file.exists():
                unanalyzed_files.append((paper_id, paper_text))
                continue

            try:
                with open(report_file, "r", encoding="utf-8") as f:
                    report = json.load(f)

                # 如果报告包含错误，重新分析
                if "error" in report or "parse_error" in report:
                    unanalyzed_files.append((paper_id, paper_text))
                    logger.info(f"文件 {paper_id} 之前的分析有错误，将重新分析")

            except Exception as e:
                logger.warning(f"检查文件 {paper_id} 的分析状态失败: {str(e)}")
                unanalyzed_files.append((paper_id, paper_text))

        logger.info(
            f"过滤后需要分析的文件数量: {len(unanalyzed_files)}/{len(extracted_files)}"
        )
        return unanalyzed_files

    def _generate_analysis_summary(self, results: List[Dict]) -> Dict:
        """
        生成分析摘要

        Args:
            results: 分析结果列表

        Returns:
            分析摘要
        """
        successful_results = [
            r for r in results if "error" not in r and "parse_error" not in r
        ]
        failed_results = [r for r in results if "error" in r or "parse_error" in r]

        # 统计基本信息
        total_papers = len(results)
        successful_papers = len(successful_results)
        failed_papers = len(failed_results)

        # 统计文本长度
        text_lengths = []
        word_counts = []

        for result in successful_results:
            if "text_length" in result:
                text_lengths.append(result["text_length"])
            if "word_count" in result:
                word_counts.append(result["word_count"])

        summary = {
            "analysis_type": "individual_only",
            "analysis_date": datetime.now().isoformat(),
            "total_papers": total_papers,
            "successful_papers": successful_papers,
            "failed_papers": failed_papers,
            "success_rate": successful_papers / total_papers if total_papers > 0 else 0,
            "text_statistics": {
                "avg_text_length": (
                    sum(text_lengths) / len(text_lengths) if text_lengths else 0
                ),
                "min_text_length": min(text_lengths) if text_lengths else 0,
                "max_text_length": max(text_lengths) if text_lengths else 0,
                "avg_word_count": (
                    sum(word_counts) / len(word_counts) if word_counts else 0
                ),
                "min_word_count": min(word_counts) if word_counts else 0,
                "max_word_count": max(word_counts) if word_counts else 0,
            },
            "progress": self.analysis_progress.copy(),
        }

        return summary

    def get_analysis_progress(self) -> Dict:
        """
        获取当前分析进度

        Returns:
            分析进度信息
        """
        return self.analysis_progress.copy()

    def analyze_batch(self, batch_id: str, individual_reports: List[Dict]) -> Dict:
        """
        第二层：批次汇总分析

        Args:
            batch_id: 批次ID
            individual_reports: 单篇分析报告列表

        Returns:
            批次汇总结果
        """
        logger.info(f"开始批次汇总分析: {batch_id}")

        try:

            # 使用GPT-4进行批次汇总（使用风格特征批次汇总方法）
            prompt = self.prompts.format_prompt(
                self.prompts.get_style_features_batch_summary_prompt(),
                paper_count=len(individual_reports),
                individual_analyses=json.dumps(
                    individual_reports, ensure_ascii=False, indent=2
                ),
            )

            logger.info(f"批次汇总Prompt长度: {len(prompt)} 字符")

            # 使用新的AI调用方法
            response_text = self._call_ai_api(prompt, "batch_summary")
            batch_summary = self._parse_gpt_response(response_text)

            # 记录解析错误
            if "parse_error" in batch_summary:
                self._log_parsing_error(
                    Exception(batch_summary["parse_error"]),
                    response_text,
                    "batch_summary",
                )
            batch_summary["batch_id"] = batch_id
            batch_summary["analysis_date"] = datetime.now().isoformat()
            batch_summary["input_papers"] = [
                report["paper_id"] for report in individual_reports
            ]

            # 保存批次汇总结果
            output_file = Path(Config.BATCH_SUMMARIES_DIR) / f"{batch_id}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(batch_summary, f, ensure_ascii=False, indent=2)

            logger.info(f"完成批次汇总分析: {batch_id}")
            return batch_summary

        except Exception as e:
            logger.error(f"批次汇总分析失败 {batch_id}: {str(e)}")
            return {
                "batch_id": batch_id,
                "error": str(e),
                "analysis_date": datetime.now().isoformat(),
            }

    def integrate_global_style(self, batch_summaries: List[Dict]) -> Dict:
        """
        第三层：全局风格整合 (保持向后兼容)

        Args:
            batch_summaries: 所有批次汇总结果

        Returns:
            全局风格指南
        """
        # 调用新的并集整合方法
        return self.integrate_global_style_union(batch_summaries)

    def integrate_global_style_union(self, batch_summaries: List[Dict]) -> Dict:
        """
        基于并集思维的全局风格整合

        Args:
            batch_summaries: 所有批次汇总结果

        Returns:
            全局风格指南
        """
        logger.info("开始基于并集思维的全局风格整合")

        try:
            # 收集所有批次的补充规则
            all_rules = []
            rule_evolution = {}

            for i, batch in enumerate(batch_summaries):
                batch_id = f"batch_{i+1:02d}"
                batch_rules = self._extract_batch_rules(batch)

                if i == 0:
                    # batch_01: 核心基准规则
                    rule_evolution[batch_id] = {
                        "description": "建立核心基准规则",
                        "rules_count": len(batch_rules),
                        "new_rules_count": len(batch_rules),
                    }
                else:
                    # 后续批次: 补充规则
                    new_rules = self._find_new_rules(batch_rules, all_rules)
                    rule_evolution[batch_id] = {
                        "description": f"补充了{len(new_rules)}条新规则",
                        "rules_count": len(batch_rules),
                        "new_rules_count": len(new_rules),
                    }

                all_rules.extend(batch_rules)

            # 3. 使用AI进行全局整合
            prompt = self.prompts.format_prompt(
                self.prompts.get_global_integration_union_prompt(),
                batch_summaries=json.dumps(
                    batch_summaries, ensure_ascii=False, indent=2
                ),
            )

            logger.info(f"并集整合Prompt长度: {len(prompt)} 字符")

            # 使用新的AI调用方法
            response_text = self._call_ai_api(prompt, "global_integration_union")
            style_guide = self._parse_gpt_response(response_text)

            # 记录解析错误
            if "parse_error" in style_guide:
                self._log_parsing_error(
                    Exception(style_guide["parse_error"]),
                    response_text,
                    "global_integration_union",
                )
                logger.error("并集风格指南解析失败")

            # 5. 添加规则演进信息
            style_guide["rule_evolution"] = rule_evolution
            style_guide["analysis_date"] = datetime.now().isoformat()
            style_guide["total_batches"] = len(batch_summaries)

            # 计算总体统计
            total_papers = sum(batch.get("paper_count", 0) for batch in batch_summaries)
            style_guide["total_papers_analyzed"] = total_papers

            # 保存全局风格指南
            with open(Config.STYLE_GUIDE_JSON, "w", encoding="utf-8") as f:
                json.dump(style_guide, f, ensure_ascii=False, indent=2)

            logger.info(f"完成全局风格整合，分析了{total_papers}篇论文")
            return style_guide

        except Exception as e:
            logger.error(f"全局风格整合失败: {str(e)}")
            return {"error": str(e), "analysis_date": datetime.now().isoformat()}

    def _extract_core_rules(self, base_batch: Dict) -> List[Dict]:
        """
        从batch_01提取核心基准规则

        Args:
            base_batch: 基准批次数据

        Returns:
            核心规则列表
        """
        return self._extract_batch_rules(base_batch)

    def _extract_batch_rules(self, batch: Dict) -> List[Dict]:
        """
        从批次数据中提取规则（支持新旧格式）

        Args:
            batch: 批次数据

        Returns:
            规则列表
        """
        rules = []

        # 检查新格式 (comprehensive_rules)
        if "comprehensive_rules" in batch:
            for rule in batch["comprehensive_rules"]:
                if isinstance(rule, dict) and "description" in rule:
                    rules.append(
                        {
                            "rule_id": rule.get("rule_id", ""),
                            "description": rule["description"],
                            "consistency_rate": rule.get("consistency_rate", 0.0),
                            "evidence": rule.get("evidence", ""),
                            "category": rule.get(
                                "category",
                                self._categorize_rule_type(rule["description"]),
                            ),
                            "rule_type": rule.get("rule_type", "unknown"),
                            "frequency": rule.get("frequency", 0.0),
                            "variations": rule.get("variations", []),
                        }
                    )

        # 兼容旧格式：从preliminary_rules提取
        elif "preliminary_rules" in batch:
            for rule in batch["preliminary_rules"]:
                if isinstance(rule, dict) and "description" in rule:
                    rules.append(
                        {
                            "rule_id": rule.get("rule_id", ""),
                            "description": rule["description"],
                            "consistency_rate": rule.get("consistency_rate", 0.0),
                            "evidence": rule.get("evidence", ""),
                            "category": self._categorize_rule_type(rule["description"]),
                            "rule_type": "preliminary",
                            "frequency": rule.get("consistency_rate", 0.0),
                            "variations": [],
                        }
                    )

        return rules

    def _find_new_rules(
        self, current_rules: List[Dict], existing_rules: List[Dict]
    ) -> List[Dict]:
        """
        找出新增的规则

        Args:
            current_rules: 当前批次的规则
            existing_rules: 已存在的规则

        Returns:
            新规则列表
        """
        existing_descriptions = {rule["description"] for rule in existing_rules}
        new_rules = []

        for rule in current_rules:
            if rule["description"] not in existing_descriptions:
                new_rules.append(rule)

        return new_rules

    def _categorize_rules_by_frequency(self, all_rules: List[Dict]) -> Dict:
        """
        按使用频率分类规则

        Args:
            all_rules: 所有规则列表

        Returns:
            分类后的规则字典
        """
        frequent_rules = []
        common_rules = []
        alternative_rules = []

        for rule in all_rules:
            frequency = rule.get("consistency_rate", 0.0)

            if frequency >= Config.FREQUENT_RULE_THRESHOLD:
                frequent_rules.append(rule)
            elif frequency >= Config.COMMON_RULE_THRESHOLD:
                common_rules.append(rule)
            elif frequency >= Config.ALTERNATIVE_RULE_THRESHOLD:
                alternative_rules.append(rule)

        return {
            "frequent_rules": frequent_rules,
            "common_rules": common_rules,
            "alternative_rules": alternative_rules,
        }

    def _categorize_rule_type(self, description: str) -> str:
        """
        根据规则描述映射到统一的写作维度

        Args:
            description: 规则描述

        Returns:
            规则维度名称
        """
        dimension = map_rule_to_dimension(description or "")
        return normalize_dimension_label(dimension)

    def _parse_gpt_response(self, response_text: str) -> Dict:
        """
        解析GPT-4的JSON响应（改进版）

        Args:
            response_text: GPT-4的响应文本

        Returns:
            解析后的JSON对象
        """
        try:
            # 清理响应文本
            cleaned_text = response_text.strip()

            # 移除可能的markdown标记
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]

            cleaned_text = cleaned_text.strip()

            # 方法1：尝试直接解析
            try:
                return json.loads(cleaned_text)
            except json.JSONDecodeError:
                pass

            # 方法2：提取JSON代码块
            if "```json" in cleaned_text:
                json_start = cleaned_text.find("```json") + 7
                json_end = cleaned_text.find("```", json_start)
                if json_end == -1:
                    # 如果没有找到结束标记，使用整个响应
                    json_text = cleaned_text[json_start:].strip()
                else:
                    json_text = cleaned_text[json_start:json_end].strip()

                if json_text:
                    return json.loads(json_text)

            # 方法3：使用括号匹配找到正确的结束位置
            json_start = cleaned_text.find("{")
            if json_start == -1:
                raise ValueError("未找到JSON开始标记")

            # 使用括号匹配来找到正确的结束位置
            brace_count = 0
            json_end = json_start
            for i, char in enumerate(cleaned_text[json_start:], json_start):
                if char == "{":
                    brace_count += 1
                elif char == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        json_end = i + 1
                        break

            json_text = cleaned_text[json_start:json_end]

            # 验证JSON是否完整
            if not json_text.strip():
                raise ValueError("提取的JSON内容为空")

            return json.loads(json_text)

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"解析GPT响应失败: {str(e)}")
            logger.error(f"响应文本长度: {len(response_text)}")
            logger.error(f"响应文本前500字符: {response_text[:500]}...")

            # 尝试备用解析方法
            try:
                # 使用正则表达式提取JSON
                import re

                json_pattern = r"\{.*\}"
                matches = re.findall(json_pattern, response_text, re.DOTALL)
                if matches:
                    # 选择最长的匹配（通常是最完整的）
                    longest_match = max(matches, key=len)
                    return json.loads(longest_match)
            except (json.JSONDecodeError, ValueError):
                pass

            # 返回错误信息，但不覆盖现有文件
            return {
                "parse_error": str(e),
                "raw_response": response_text[:1000],
                "response_length": len(response_text),
            }

    def _call_ai_api(self, prompt: str, task_type: str = "default") -> str:
        """
        调用AI API，使用任务特定的参数

        Args:
            prompt: 提示词
            task_type: 任务类型

        Returns:
            AI响应文本
        """
        try:
            temperature = self.temperature_config.get(task_type, 0.3)
            max_tokens = min(
                self.max_tokens_config.get(task_type, 15000), self.absolute_max_tokens
            )

            # 获取任务特定的系统消息
            system_message = self._get_system_message(task_type)

            # 将任务类型映射到模型配置类型
            model_task_type = self._map_task_type_to_model_config(task_type)
            logger.debug(f"任务类型映射: {task_type} -> {model_task_type} (用于模型选择)")

            try:
                response_text = self.ai_client.call_ai(
                    prompt=prompt,
                    system_message=system_message,
                    task_name=f"分层分析 - {task_type}",
                    temperature=temperature,
                    max_tokens=max_tokens,
                    additional_params={
                        "top_p": 0.9,
                        "frequency_penalty": 0.1,
                        "presence_penalty": 0.1
                    },
                    task_type=model_task_type
                )
                return response_text.strip()

            except AICallError as e:
                logger.error(f"AI API调用失败: {str(e)}")
                raise

        except Exception as e:
            logger.error(f"AI API调用失败: {str(e)}")
            raise

    def _map_task_type_to_model_config(self, task_type: str) -> str:
        """
        将任务类型映射到模型配置类型
        
        Args:
            task_type: 任务类型（如 'batch_summary', 'individual_analysis' 等）
            
        Returns:
            模型配置类型（'individual', 'batch', 'global', 'default'）
        """
        # 任务类型到模型配置的映射
        mapping = {
            'individual_analysis': 'individual',
            'batch_summary': 'batch',
            'global_integration': 'global',
            'global_integration_union': 'global',
        }
        
        # 如果找到映射，返回对应的模型配置类型
        if task_type in mapping:
            return mapping[task_type]
        
        # 如果初始化时指定了特定的任务类型，使用它
        if self.task_type != 'default':
            return self.task_type
        
        # 否则使用默认配置
        return 'default'

    def _get_system_message(self, task_type: str) -> str:
        """
        获取任务特定的系统消息

        Args:
            task_type: 任务类型

        Returns:
            系统消息
        """
        messages = {
            "individual_analysis": (
                "You are a detailed academic writing analyst. "
                "Analyze writing patterns creatively and comprehensively. "
                "Respond with valid JSON only."
            ),
            "batch_summary": (
                "You are a pattern recognition expert. "
                "Identify common writing patterns across multiple papers. "
                "Respond with valid JSON only."
            ),
            "global_integration": (
                "You are a style guide generator. "
                "Create comprehensive, well-structured style guides in valid JSON "
                "format only. No markdown, no code blocks, no explanations."
            ),
            "rule_generation": (
                "You are a writing rule expert. "
                "Generate clear, actionable writing rules based on patterns. "
                "Respond with valid JSON only."
            ),
            "example_extraction": (
                "You are an example finder. "
                "Extract relevant, illustrative examples from text. "
                "Respond with valid JSON only."
            ),
            "quality_assessment": (
                "You are a quality evaluator. "
                "Assess writing quality objectively and consistently. "
                "Respond with valid JSON only."
            ),
            "consistency_check": (
                "You are a format validator. "
                "Ensure strict adherence to JSON format requirements. "
                "Respond with valid JSON only."
            ),
        }
        return messages.get(
            task_type, "You are an AI assistant. Respond with valid JSON only."
        )

    def _log_parsing_error(self, error: Exception, response_text: str, task_type: str):
        """
        记录JSON解析错误的详细信息

        Args:
            error: 错误对象
            response_text: 响应文本
            task_type: 任务类型
        """
        logger.error(f"任务类型: {task_type}")
        logger.error(f"错误信息: {str(error)}")
        logger.error(f"响应长度: {len(response_text)}")
        logger.error(f"响应前500字符: {response_text[:500]}")

        # 保存错误详情到文件
        error_log = {
            "timestamp": datetime.now().isoformat(),
            "task_type": task_type,
            "error": str(error),
            "response_length": len(response_text),
            "response_preview": response_text[:1000],
        }

        # 确保日志目录存在
        os.makedirs("logs", exist_ok=True)

        with open("logs/json_parse_errors.json", "a", encoding="utf-8") as f:
            f.write(json.dumps(error_log, ensure_ascii=False) + "\n")

    def get_individual_report(self, paper_id: str) -> Dict:
        """
        获取单篇分析报告

        Args:
            paper_id: 论文ID

        Returns:
            单篇分析报告
        """
        report_file = Path(Config.INDIVIDUAL_REPORTS_DIR) / f"{paper_id}.json"

        if not report_file.exists():
            return {"error": f"报告文件不存在: {paper_id}"}

        try:
            with open(report_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            return {"error": f"读取报告失败: {str(e)}"}

    def get_batch_summary(self, batch_id: str) -> Dict:
        """
        获取批次汇总报告

        Args:
            batch_id: 批次ID

        Returns:
            批次汇总报告
        """
        summary_file = Path(Config.BATCH_SUMMARIES_DIR) / f"{batch_id}.json"

        if not summary_file.exists():
            return {"error": f"批次汇总文件不存在: {batch_id}"}

        try:
            with open(summary_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            return {"error": f"读取批次汇总失败: {str(e)}"}

    def get_style_guide(self) -> Dict:
        """
        获取全局风格指南

        Returns:
            全局风格指南
        """
        if not Path(Config.STYLE_GUIDE_JSON).exists():
            return {"error": "风格指南文件不存在"}

        try:
            with open(Config.STYLE_GUIDE_JSON, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            return {"error": f"读取风格指南失败: {str(e)}"}


def main():
    """测试分层分析功能"""
    from ..core.pymupdf_extractor import PyMuPDFExtractor

    # 验证配置
    Config.validate()

    # 创建分析器
    analyzer = LayeredAnalyzer()

    # 测试单篇分析（如果有提取的文本）
    extractor = PyMuPDFExtractor(Config.JOURNALS_DIR, Config.EXTRACTED_DIR)
    texts = extractor.get_extracted_texts()

    if texts:
        # 分析第一篇论文
        paper_id, paper_text = texts[0]
        result = analyzer.analyze_individual_paper(
            f"test_{paper_id}", paper_text[:2000]
        )  # 限制长度用于测试

        print("单篇分析结果:")
        print(f"论文ID: {result.get('paper_id')}")
        print(f"文本长度: {result.get('text_length')}")
        print(f"是否有错误: {'error' in result}")
    else:
        print("没有找到提取的文本文件")


if __name__ == "__main__":
    main()
