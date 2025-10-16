"""
多轮交互式润色模块

实现分三轮的论文润色：句式结构、词汇优化、段落衔接，支持用户交互确认。
"""

import json
import re
from typing import Dict, List, Tuple
from pathlib import Path
from datetime import datetime
from openai import OpenAI

from ..analysis.style_guide_generator import StyleGuideGenerator
from ..analysis.quality_scorer import QualityScorer
from ..core.prompts import PromptTemplates
from .style_selector import StyleSelector
from config import Config

# 设置日志
from ..utils.logger_config import get_logger

logger = get_logger(__name__)


class MultiRoundPolisher:
    """多轮润色器"""

    def __init__(self):
        """初始化润色器"""
        ai_config = Config.get_ai_config()
        self.client = OpenAI(
            api_key=ai_config["api_key"], base_url=ai_config["base_url"]
        )
        self.prompts = PromptTemplates()
        self.style_guide_generator = StyleGuideGenerator()
        self.quality_scorer = QualityScorer()
        self.ai_config = ai_config

        # 加载风格指南和风格选择器
        self.style_guide = {}
        self.style_selector = StyleSelector()
        self._load_style_guide()

        # 润色状态
        self.current_text = ""
        self.modification_history = []
        self.user_selections = {}
        self.selected_style = "balanced"  # 默认风格

    def _load_style_guide(self):
        """加载风格指南"""
        # 优先加载混合风格指南
        hybrid_guide_path = "data/hybrid_style_guide.json"
        if Path(hybrid_guide_path).exists():
            try:
                with open(hybrid_guide_path, "r", encoding="utf-8") as f:
                    self.style_guide = json.load(f)
                logger.info("成功加载混合风格指南")
                return
            except Exception as e:
                logger.warning(f"加载混合风格指南失败: {str(e)}")
        else:
            raise FileNotFoundError("混合风格指南不存在")

    def set_style(self, style: str) -> None:
        """
        设置润色风格
        
        Args:
            style: 风格名称 (conservative, balanced, innovative)
        """
        self.selected_style = style
        logger.info(f"设置润色风格: {style}")

    def polish_paper(self, paper_text: str, style: str = "balanced") -> Dict:
        """
        润色论文（仅支持非交互式润色）

        Args:
            paper_text: 原始论文文本
            style: 润色风格 (conservative, balanced, innovative, auto)

        Returns:
            润色结果
        """
        logger.info(f"开始非交互式润色论文，风格: {style}")

        try:
            # 初始化
            self.current_text = paper_text
            self.modification_history = []
            self.user_selections = {}

            # 设置风格
            if style != "auto":
                self.set_style(style)
            else:
                # 自动推荐风格
                paper_features = self.style_selector.analyze_paper_features(paper_text)
                recommended_style = self.style_selector.recommend_style(paper_features)
                logger.info(f"自动推荐风格: {recommended_style}")
                self.set_style(recommended_style)

            # 计算润色前评分
            before_scores = self.quality_scorer.score_paper(paper_text)

            # 执行非交互式润色（一次性处理）
            self._batch_polishing_with_style()

            # 计算润色后评分
            after_scores = self.quality_scorer.score_paper(self.current_text)

            # 比较评分
            score_comparison = self.quality_scorer.compare_scores(
                before_scores, after_scores
            )

            # 生成最终结果
            final_result = {
                "success": True,
                "original_text": paper_text,
                "polished_text": self.current_text,
                "modification_history": self.modification_history,
                "before_scores": before_scores,
                "after_scores": after_scores,
                "score_comparison": score_comparison,
                "user_selections": self.user_selections,
                "polishing_summary": self._generate_polishing_summary(),
                "timestamp": datetime.now().isoformat(),
                "interactive_mode": False,  # 固定为非交互式
                "style_used": self.selected_style if hasattr(self, 'selected_style') else style
            }

            logger.info("论文润色完成")
            return final_result

        except Exception as e:
            logger.error(f"论文润色失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "original_text": paper_text,
                "polished_text": paper_text,
            }

    def polish_paper_simple(self, paper_text: str, style: str = "balanced") -> Dict:
        """
        简洁润色论文（只返回润色后的文本，不包含详细修改说明）

        Args:
            paper_text: 原始论文文本
            style: 润色风格 (conservative, balanced, innovative, auto)

        Returns:
            简洁润色结果
        """
        logger.info(f"开始简洁润色论文，风格: {style}")

        try:
            # 初始化
            self.current_text = paper_text
            self.modification_history = []
            self.user_selections = {}

            # 设置风格
            if style != "auto":
                self.set_style(style)
            else:
                # 自动推荐风格
                paper_features = self.style_selector.analyze_paper_features(paper_text)
                recommended_style = self.style_selector.recommend_style(paper_features)
                logger.info(f"自动推荐风格: {recommended_style}")
                self.set_style(recommended_style)

            # 计算润色前评分
            before_scores = self.quality_scorer.score_paper(paper_text)

            # 执行简洁润色
            polished_text = self._simple_polish_with_style()

            # 计算润色后评分
            after_scores = self.quality_scorer.score_paper(polished_text)

            # 比较评分
            score_comparison = self.quality_scorer.compare_scores(
                before_scores, after_scores
            )

            # 生成简洁结果
            final_result = {
                "success": True,
                "original_text": paper_text,
                "polished_text": polished_text,
                "before_scores": before_scores,
                "after_scores": after_scores,
                "score_comparison": score_comparison,
                "polishing_summary": {
                    "total_rounds": 1,
                    "total_modifications_applied": 1,  # 整体润色
                    "style_used": self.selected_style if hasattr(self, 'selected_style') else style
                },
                "timestamp": datetime.now().isoformat(),
                "simple_mode": True,
                "style_used": self.selected_style if hasattr(self, 'selected_style') else style
            }

            logger.info("简洁润色完成")
            return final_result

        except Exception as e:
            logger.error(f"简洁润色失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "original_text": paper_text,
                "polished_text": paper_text,
            }

    def polish_paper_with_choices(
        self,
        paper_text: str,
        style_preference: str = "balanced",
    ) -> Dict:
        """
        基于风格选择的论文润色（仅支持非交互式润色）

        Args:
            paper_text: 原始论文文本
            style_preference: 风格偏好 ("conservative", "balanced", "innovative", "auto")

        Returns:
            润色结果
        """
        logger.info(f"开始基于风格选择的非交互式论文润色，风格: {style_preference}")

        try:
            # 初始化
            self.current_text = paper_text
            self.modification_history = []
            self.user_selections = {}
            self.selected_style = style_preference

            # 分析论文特征并推荐风格
            paper_features = self.style_selector.analyze_paper_features(paper_text)
            recommended_style = self.style_selector.recommend_style(paper_features)

            # 如果用户没有指定风格，使用推荐风格
            if style_preference == "auto":
                self.selected_style = recommended_style
                logger.info(f"自动推荐风格: {recommended_style}")
            else:
                self.selected_style = style_preference

            # 计算润色前评分
            before_scores = self.quality_scorer.score_paper(paper_text)

            # 执行非交互式润色
            self._batch_polishing_with_style()

            # 计算润色后评分
            after_scores = self.quality_scorer.score_paper(self.current_text)

            # 比较评分
            score_comparison = self.quality_scorer.compare_scores(
                before_scores, after_scores
            )

            # 生成最终结果
            final_result = {
                "success": True,
                "original_text": paper_text,
                "polished_text": self.current_text,
                "selected_style": self.selected_style,
                "recommended_style": recommended_style,
                "paper_features": paper_features,
                "modification_history": self.modification_history,
                "before_scores": before_scores,
                "after_scores": after_scores,
                "score_comparison": score_comparison,
                "user_selections": self.user_selections,
                "polishing_summary": self._generate_style_polishing_summary(),
                "timestamp": datetime.now().isoformat(),
                "interactive_mode": False,  # 固定为非交互式
            }

            logger.info("基于风格选择的论文润色完成")
            return final_result

        except Exception as e:
            logger.error(f"基于风格选择的论文润色失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "original_text": paper_text,
                "polished_text": paper_text,
            }

    def _interactive_polishing(self) -> Dict:
        """
        交互式润色

        Returns:
            润色结果
        """
        logger.info("开始交互式润色")

        # 三轮润色：句式结构调整、词汇优化、段落衔接
        rounds = [
            {"round": 1, "name": "句式结构调整", "focus": "sentence_structure"},
            {"round": 2, "name": "词汇优化", "focus": "vocabulary"},
            {"round": 3, "name": "段落衔接", "focus": "transitions"},
        ]

        for round_info in rounds:
            logger.info(f"开始第{round_info['round']}轮润色: {round_info['name']}")

            # 生成修改建议
            modifications = self._generate_round_modifications(round_info)

            if not modifications:
                logger.info(f"第{round_info['round']}轮无需修改")
                continue

            # 显示修改建议并获取用户选择
            user_choices = self._present_modifications_to_user(
                round_info, modifications
            )

            # 应用用户选择的修改
            self._apply_user_choices(round_info, modifications, user_choices)

            # 记录修改历史
            self.modification_history.append(
                {
                    "round": round_info["round"],
                    "round_name": round_info["name"],
                    "modifications_proposed": len(modifications),
                    "modifications_applied": len(user_choices.get("accepted", [])),
                    "user_choices": user_choices,
                }
            )

        return {"interactive_completed": True}

    def _batch_polishing(self) -> Dict:
        """
        批量润色（非交互式）- 一次性完成所有润色

        Returns:
            润色结果
        """
        logger.info("开始综合批量润色（一次性完成句式、词汇、段落润色）")
        logger.info(f"输入文本长度: {len(self.current_text)} 字符")

        # 生成综合修改建议
        comprehensive_modifications = self._generate_comprehensive_modifications()

        # 按顺序应用三类修改
        total_modifications = 0
        
        # 1. 应用句式结构修改
        sentence_modifications = comprehensive_modifications.get("sentence_structure", {}).get("modifications", [])
        if sentence_modifications:
            logger.info(f"应用句式结构修改: {len(sentence_modifications)}条")
            for i, mod in enumerate(sentence_modifications[:3], 1):  # 只记录前3条修改的详情
                logger.info(f"  修改{i}: {mod.get('original_text', '')[:50]}... -> {mod.get('modified_text', '')[:50]}...")
            if len(sentence_modifications) > 3:
                logger.info(f"  ... 还有{len(sentence_modifications)-3}条修改")
            self._apply_all_modifications({"round": 1, "name": "句式结构调整"}, sentence_modifications)
            total_modifications += len(sentence_modifications)

        # 2. 应用词汇优化修改
        vocabulary_modifications = comprehensive_modifications.get("vocabulary", {}).get("modifications", [])
        if vocabulary_modifications:
            logger.info(f"应用词汇优化修改: {len(vocabulary_modifications)}条")
            for i, mod in enumerate(vocabulary_modifications[:3], 1):  # 只记录前3条修改的详情
                logger.info(f"  修改{i}: {mod.get('word_changed', '')} - {mod.get('reason', '')[:50]}...")
            if len(vocabulary_modifications) > 3:
                logger.info(f"  ... 还有{len(vocabulary_modifications)-3}条修改")
            self._apply_all_modifications({"round": 2, "name": "词汇优化"}, vocabulary_modifications)
            total_modifications += len(vocabulary_modifications)

        # 3. 应用段落衔接修改
        transition_modifications = comprehensive_modifications.get("transitions", {}).get("modifications", [])
        if transition_modifications:
            logger.info(f"应用段落衔接修改: {len(transition_modifications)}条")
            for i, mod in enumerate(transition_modifications[:3], 1):  # 只记录前3条修改的详情
                logger.info(f"  修改{i}: {mod.get('transition_added', '')} - {mod.get('reason', '')[:50]}...")
            if len(transition_modifications) > 3:
                logger.info(f"  ... 还有{len(transition_modifications)-3}条修改")
            self._apply_all_modifications({"round": 3, "name": "段落衔接"}, transition_modifications)
            total_modifications += len(transition_modifications)

        # 记录综合修改历史
        self.modification_history.append(
            {
                "round": 0,  # 0表示综合润色
                "round_name": "综合润色",
                "modifications_proposed": total_modifications,
                "modifications_applied": total_modifications,
                "auto_applied": True,
                "sentence_structure_count": len(sentence_modifications),
                "vocabulary_count": len(vocabulary_modifications),
                "transitions_count": len(transition_modifications),
                "comprehensive_summary": comprehensive_modifications.get("overall_summary", {})
            }
        )

        logger.info(f"综合润色完成，共应用 {total_modifications} 条修改")
        return {"batch_completed": True, "total_modifications": total_modifications}

    def _interactive_polishing_with_style(self) -> Dict:
        """
        基于风格选择的交互式润色

        Returns:
            润色结果
        """
        logger.info(f"开始基于风格选择的交互式润色，风格: {self.selected_style}")

        # 显示风格选择信息
        self._display_style_info()

        # 三轮润色：句式结构调整、词汇优化、段落衔接
        rounds = [
            {"round": 1, "name": "句式结构调整", "focus": "sentence_structure"},
            {"round": 2, "name": "词汇优化", "focus": "vocabulary"},
            {"round": 3, "name": "段落衔接", "focus": "transitions"},
        ]

        for round_info in rounds:
            logger.info(f"开始第{round_info['round']}轮润色: {round_info['name']}")

            # 生成修改建议
            modifications = self._generate_round_modifications_with_style(round_info)

            if not modifications:
                logger.info(f"第{round_info['round']}轮无需修改")
                continue

            # 显示修改建议并获取用户选择
            user_choices = self._present_modifications_to_user(
                round_info, modifications
            )

            # 应用用户选择的修改
            self._apply_user_choices(round_info, modifications, user_choices)

            # 记录修改历史
            self.modification_history.append(
                {
                    "round": round_info["round"],
                    "round_name": round_info["name"],
                    "style": self.selected_style,
                    "modifications_proposed": len(modifications),
                    "modifications_applied": len(user_choices.get("accepted", [])),
                    "user_choices": user_choices,
                }
            )

        return {"interactive_completed": True}

    def _batch_polishing_with_style(self) -> Dict:
        """
        基于风格选择的批量润色（非交互式）- 一次性完成所有润色

        Returns:
            润色结果
        """
        logger.info(f"开始基于风格选择的综合批量润色，风格: {self.selected_style}")
        logger.info(f"输入文本长度: {len(self.current_text)} 字符")

        # 生成综合修改建议
        comprehensive_modifications = self._generate_comprehensive_modifications_with_style()

        # 按顺序应用三类修改
        total_modifications = 0
        all_applied_modifications = []
        
        # 1. 应用句式结构修改
        sentence_modifications = comprehensive_modifications.get("sentence_structure", {}).get("modifications", [])
        sentence_round_info = {"round": 1, "name": "句式结构调整"}
        if sentence_modifications:
            logger.info(f"应用句式结构修改: {len(sentence_modifications)}条")
            for i, mod in enumerate(sentence_modifications[:3], 1):  # 只记录前3条修改的详情
                logger.info(f"  修改{i}: {mod.get('original_text', '')[:50]}... -> {mod.get('modified_text', '')[:50]}...")
            if len(sentence_modifications) > 3:
                logger.info(f"  ... 还有{len(sentence_modifications)-3}条修改")
            self._apply_all_modifications(sentence_round_info, sentence_modifications)
            all_applied_modifications.extend(sentence_round_info.get("applied_modifications", []))
            total_modifications += len(sentence_modifications)

        # 2. 应用词汇优化修改
        vocabulary_modifications = comprehensive_modifications.get("vocabulary", {}).get("modifications", [])
        vocabulary_round_info = {"round": 2, "name": "词汇优化"}
        if vocabulary_modifications:
            logger.info(f"应用词汇优化修改: {len(vocabulary_modifications)}条")
            for i, mod in enumerate(vocabulary_modifications[:3], 1):  # 只记录前3条修改的详情
                logger.info(f"  修改{i}: {mod.get('word_changed', '')} - {mod.get('reason', '')[:50]}...")
            if len(vocabulary_modifications) > 3:
                logger.info(f"  ... 还有{len(vocabulary_modifications)-3}条修改")
            self._apply_all_modifications(vocabulary_round_info, vocabulary_modifications)
            all_applied_modifications.extend(vocabulary_round_info.get("applied_modifications", []))
            total_modifications += len(vocabulary_modifications)

        # 3. 应用段落衔接修改
        transition_modifications = comprehensive_modifications.get("transitions", {}).get("modifications", [])
        transition_round_info = {"round": 3, "name": "段落衔接"}
        if transition_modifications:
            logger.info(f"应用段落衔接修改: {len(transition_modifications)}条")
            for i, mod in enumerate(transition_modifications[:3], 1):  # 只记录前3条修改的详情
                logger.info(f"  修改{i}: {mod.get('transition_added', '')} - {mod.get('reason', '')[:50]}...")
            if len(transition_modifications) > 3:
                logger.info(f"  ... 还有{len(transition_modifications)-3}条修改")
            self._apply_all_modifications(transition_round_info, transition_modifications)
            all_applied_modifications.extend(transition_round_info.get("applied_modifications", []))
            total_modifications += len(transition_modifications)

        # 记录综合修改历史
        self.modification_history.append(
            {
                "round": 0,  # 0表示综合润色
                "round_name": "综合润色",
                "style": self.selected_style,
                "modifications_proposed": total_modifications,
                "modifications_applied": total_modifications,
                "auto_applied": True,
                "sentence_structure_count": len(sentence_modifications),
                "vocabulary_count": len(vocabulary_modifications),
                "transitions_count": len(transition_modifications),
                "comprehensive_summary": comprehensive_modifications.get("overall_summary", {}),
                "applied_modifications": all_applied_modifications  # 添加具体修改内容
            }
        )

        logger.info(f"基于{self.selected_style}风格的综合润色完成，共应用 {total_modifications} 条修改")
        return {"batch_completed": True, "total_modifications": total_modifications}

    def _generate_comprehensive_modifications(self) -> Dict:
        """
        生成综合润色修改建议（一次性完成句式、词汇、段落润色）

        Returns:
            包含三类修改建议的字典
        """
        try:
            # 获取所有相关规则
            sentence_rules = self._get_relevant_rules("sentence_structure")
            vocabulary_rules = self._get_relevant_rules("vocabulary")
            transition_rules = self._get_relevant_rules("transitions")
            
            # 合并所有规则
            all_rules = sentence_rules + vocabulary_rules + transition_rules
            
            if not all_rules:
                logger.warning("没有找到相关的风格规则")
                return {
                    "sentence_structure": {"modifications": [], "summary": {"total_modifications": 0}},
                    "vocabulary": {"modifications": [], "summary": {"total_modifications": 0}},
                    "transitions": {"modifications": [], "summary": {"total_modifications": 0}}
                }

            # 使用综合润色prompt
            prompt_template = self.prompts.get_comprehensive_polish_prompt()
            
            # 格式化prompt
            prompt = self.prompts.format_prompt(
                prompt_template,
                style_rules=json.dumps(all_rules, ensure_ascii=False, indent=2),
                paper_text=self.current_text
            )

            # 记录AI输入
            logger.info("=== AI输入日志 - 综合润色 ===")
            logger.info(f"模型: {self.ai_config['model']}")
            logger.info(f"最大令牌数: {self.ai_config['max_tokens']}")
            logger.info(f"温度参数: {self.ai_config['temperature']}")
            logger.info(f"规则数量: {len(all_rules)}")
            logger.info(f"输入文本长度: {len(self.current_text)} 字符")
            logger.info("--- 完整Prompt ---")
            logger.info(prompt)
            logger.info("--- Prompt结束 ---")

            # 调用AI
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个专业的学术写作编辑专家。"},
                    {"role": "user", "content": prompt}
                ],
                # max_tokens=self.ai_config["max_tokens"],
                temperature=self.ai_config["temperature"]
            )

            # 解析响应
            response_text = response.choices[0].message.content
            
            # 记录AI输出
            logger.info("=== AI输出日志 - 综合润色 ===")
            logger.info(f"响应长度: {len(response_text)} 字符")
            logger.info(f"使用令牌数: {response.usage.total_tokens if hasattr(response, 'usage') else '未知'}")
            logger.info("--- 完整响应 ---")
            logger.info(response_text)
            logger.info("--- 响应结束 ---")
            
            result = self._parse_gpt_response(response_text)
            
            if "error" in result:
                logger.error(f"AI响应解析失败: {result.get('error', '未知错误')}")
                return {
                    "sentence_structure": {"modifications": [], "summary": {"total_modifications": 0}},
                    "vocabulary": {"modifications": [], "summary": {"total_modifications": 0}},
                    "transitions": {"modifications": [], "summary": {"total_modifications": 0}}
                }

            # 返回结构化的修改建议
            return result

        except Exception as e:
            logger.error(f"生成综合润色修改建议失败: {str(e)}")
            return {
                "sentence_structure": {"modifications": [], "summary": {"total_modifications": 0}},
                "vocabulary": {"modifications": [], "summary": {"total_modifications": 0}},
                "transitions": {"modifications": [], "summary": {"total_modifications": 0}}
            }

    def _generate_comprehensive_modifications_with_style(self) -> Dict:
        """
        基于风格选择生成综合润色修改建议

        Returns:
            包含三类修改建议的字典
        """
        try:
            # 获取指定风格的规则
            sentence_rules = self.style_selector.filter_rules_by_focus(
                self.selected_style, "sentence_structure"
            )
            vocabulary_rules = self.style_selector.filter_rules_by_focus(
                self.selected_style, "vocabulary"
            )
            transition_rules = self.style_selector.filter_rules_by_focus(
                self.selected_style, "transitions"
            )
            
            # 合并所有规则
            all_rules = sentence_rules + vocabulary_rules + transition_rules
            
            if not all_rules:
                logger.warning(f"没有找到风格 {self.selected_style} 的相关规则")
                return {
                    "sentence_structure": {"modifications": [], "summary": {"total_modifications": 0}},
                    "vocabulary": {"modifications": [], "summary": {"total_modifications": 0}},
                    "transitions": {"modifications": [], "summary": {"total_modifications": 0}}
                }

            # 使用综合润色prompt
            prompt_template = self.prompts.get_comprehensive_polish_prompt()
            
            # 格式化prompt
            prompt = self.prompts.format_prompt(
                prompt_template,
                style_rules=json.dumps(all_rules, ensure_ascii=False, indent=2),
                paper_text=self.current_text
            )

            # 记录AI输入
            logger.info("=== AI输入日志 - 综合润色（带风格） ===")
            logger.info(f"模型: {self.ai_config['model']}")
            logger.info(f"最大令牌数: {self.ai_config['max_tokens']}")
            logger.info(f"温度参数: {self.ai_config['temperature']}")
            logger.info(f"选择风格: {self.selected_style}")
            logger.info(f"规则数量: {len(all_rules)}")
            logger.info(f"输入文本长度: {len(self.current_text)} 字符")
            logger.info("--- 完整Prompt ---")
            logger.info(prompt)
            logger.info("--- Prompt结束 ---")

            # 调用AI
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": f"你是一个专业的学术写作编辑专家，专门使用{self.selected_style}风格进行润色。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=8000,
                temperature=self.ai_config["temperature"]
            )

            # 解析响应
            response_text = response.choices[0].message.content
            
            # 记录AI输出
            logger.info("=== AI输出日志 - 综合润色（带风格） ===")
            logger.info(f"响应长度: {len(response_text)} 字符")
            logger.info(f"使用令牌数: {response.usage.total_tokens if hasattr(response, 'usage') else '未知'}")
            logger.info("--- 完整响应 ---")
            logger.info(response_text)
            logger.info("--- 响应结束 ---")
            
            result = self._parse_gpt_response(response_text)
            
            if "error" in result:
                logger.error(f"AI响应解析失败: {result.get('error', '未知错误')}")
                return {
                    "sentence_structure": {"modifications": [], "summary": {"total_modifications": 0}},
                    "vocabulary": {"modifications": [], "summary": {"total_modifications": 0}},
                    "transitions": {"modifications": [], "summary": {"total_modifications": 0}}
                }

            # 返回结构化的修改建议
            return result

        except Exception as e:
            logger.error(f"生成基于风格的综合润色修改建议失败: {str(e)}")
            return {
                "sentence_structure": {"modifications": [], "summary": {"total_modifications": 0}},
                "vocabulary": {"modifications": [], "summary": {"total_modifications": 0}},
                "transitions": {"modifications": [], "summary": {"total_modifications": 0}}
            }

    def _display_style_info(self):
        """显示风格选择信息"""
        style_info = self.style_selector.get_style_info(self.selected_style)

        print(f"\n=== 选择的润色风格: {self.selected_style.upper()} ===")
        print(f"描述: {style_info['description']}")
        print(f"规则数量: {len(style_info['rules'])}")
        print(f"特征: {', '.join(style_info['characteristics'])}")
        print("=" * 50)

    def _generate_round_modifications_with_style(self, round_info: Dict) -> List[Dict]:
        """
        基于风格选择生成指定轮次的修改建议

        Args:
            round_info: 轮次信息

        Returns:
            修改建议列表
        """
        try:
            # 获取指定风格的规则
            relevant_rules = self.style_selector.filter_rules_by_focus(
                self.selected_style, round_info["focus"]
            )

            if not relevant_rules:
                logger.warning(
                    f"没有找到风格 {self.selected_style} 在 {round_info['focus']} 方面的规则"
                )
                return []

            # 根据轮次选择prompt
            if round_info["round"] == 1:
                prompt_template = self.prompts.get_sentence_structure_polish_prompt()
            elif round_info["round"] == 2:
                prompt_template = self.prompts.get_vocabulary_polish_prompt()
            elif round_info["round"] == 3:
                prompt_template = self.prompts.get_transition_polish_prompt()
            else:
                return []

            # 格式化prompt，包含风格信息
            style_rules_text = self._format_style_rules_for_prompt(relevant_rules)
            prompt = self.prompts.format_prompt(
                prompt_template,
                style_rules=style_rules_text,
                paper_text=self.current_text,
            )

            # 调用AI API
            response_text = self._call_ai_api(
                prompt, f'polish_round_{round_info["round"]}'
            )

            # 解析响应
            modifications = self._parse_modifications_response(response_text)

            # 添加风格信息到修改建议
            for mod in modifications:
                mod["style"] = self.selected_style
                mod["style_rule_source"] = self._find_applicable_rule(
                    mod, relevant_rules
                )

            return modifications

        except Exception as e:
            logger.error(f"生成风格化修改建议失败: {str(e)}")
            return []

    def _format_style_rules_for_prompt(self, rules: List[Dict]) -> str:
        """
        格式化风格规则用于Prompt

        Args:
            rules: 规则列表

        Returns:
            格式化的规则文本
        """
        if not rules:
            return "无相关规则"

        formatted_rules = []
        for rule in rules:
            rule_text = f"- {rule.get('description', '')}"
            if rule.get("evidence"):
                rule_text += f" (证据: {rule['evidence']})"
            formatted_rules.append(rule_text)

        return "\n".join(formatted_rules)

    def _find_applicable_rule(self, modification: Dict, rules: List[Dict]) -> str:
        """
        为修改建议找到适用的规则

        Args:
            modification: 修改建议
            rules: 规则列表

        Returns:
            适用的规则描述
        """
        # 简单的规则匹配逻辑
        modification_text = modification.get("reason", "").lower()

        for rule in rules:
            rule_keywords = rule.get("description", "").lower().split()
            if any(keyword in modification_text for keyword in rule_keywords):
                return rule.get("description", "")

        return "相关风格规则"

    def _generate_style_polishing_summary(self) -> Dict:
        """
        生成基于风格的润色总结

        Returns:
            润色总结字典
        """
        style_info = self.style_selector.get_style_info(self.selected_style)

        return {
            "selected_style": self.selected_style,
            "style_description": style_info["description"],
            "rules_applied": len(style_info["rules"]),
            "total_modifications": sum(
                round_data.get("modifications_applied", 0)
                for round_data in self.modification_history
            ),
            "rounds_completed": len(self.modification_history),
            "style_characteristics": style_info["characteristics"],
        }

    def _call_ai_api(self, prompt: str, task_type: str = "default") -> str:
        """
        调用AI API

        Args:
            prompt: 提示词
            task_type: 任务类型

        Returns:
            AI响应文本
        """
        try:
            response = self.client.chat.completions.create(
                model=self.ai_config["model"],
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=4000,
                top_p=0.9,
                frequency_penalty=0.1,
                presence_penalty=0.1,
            )

            logger.info(f"AI调用成功 - 任务类型: {task_type}")
            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"AI API调用失败: {str(e)}")
            raise

    def _generate_round_modifications(self, round_info: Dict) -> List[Dict]:
        """
        生成指定轮次的修改建议

        Args:
            round_info: 轮次信息

        Returns:
            修改建议列表
        """
        try:
            # 获取相关的风格规则
            relevant_rules = self._get_relevant_rules(round_info["focus"])

            if not relevant_rules:
                logger.warning(f"没有找到相关的风格规则: {round_info['focus']}")
                return []

            # 根据轮次选择prompt
            if round_info["round"] == 1:
                prompt_template = self.prompts.get_sentence_structure_polish_prompt()
            elif round_info["round"] == 2:
                prompt_template = self.prompts.get_vocabulary_polish_prompt()
            elif round_info["round"] == 3:
                prompt_template = self.prompts.get_transition_polish_prompt()
            else:
                return []

            # 格式化prompt
            prompt = self.prompts.format_prompt(
                prompt_template,
                style_rules=json.dumps(relevant_rules, ensure_ascii=False, indent=2),
                paper_text=self.current_text,
            )

            # 记录AI请求参数
            request_params = {
                "model": self.ai_config["model"],
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": self.ai_config["max_tokens"],
                "temperature": self.ai_config["temperature"],
            }
            logger.info(f"润色轮次{round_info['round']}AI请求参数: {request_params}")
            logger.info(f"润色轮次{round_info['round']}Prompt长度: {len(prompt)} 字符")

            # 调用GPT-4
            response = self.client.chat.completions.create(
                model=self.ai_config["model"],
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.ai_config["max_tokens"],
                temperature=self.ai_config["temperature"],
            )

            # 记录AI响应参数
            response_content = response.choices[0].message.content
            logger.info(
                f"润色轮次{round_info['round']}AI响应参数: model={response.model}, usage={response.usage}, finish_reason={response.choices[0].finish_reason}"
            )
            logger.info(
                f"润色轮次{round_info['round']}AI响应内容长度: {len(response_content)} 字符"
            )
            logger.info(
                f"润色轮次{round_info['round']}AI完整响应内容: {response_content}"
            )

            # 解析响应
            result = self._parse_gpt_response(response.choices[0].message.content)

            if "modifications" in result:
                return result["modifications"]
            else:
                logger.error(f"GPT响应格式错误: {result}")
                return []

        except Exception as e:
            logger.error(f"生成修改建议失败: {str(e)}")
            return []

    def _get_relevant_rules(self, focus: str) -> List[Dict]:
        """
        获取相关的风格规则

        Args:
            focus: 关注点（sentence_structure, vocabulary, transitions）

        Returns:
            相关规则列表
        """
        if not self.style_guide or "rules" not in self.style_guide:
            return []

        rules = self.style_guide["rules"]

        # 根据关注点过滤规则
        if focus == "sentence_structure":
            relevant_categories = ["Sentence Structure", "Paragraph Organization"]
        elif focus == "vocabulary":
            relevant_categories = ["Vocabulary Choice", "Academic Expression"]
        elif focus == "transitions":
            relevant_categories = [
                "Paragraph Organization",
                "Coherence",
                "Transitions",
                "连接词",
                "段落衔接",
            ]
        else:
            return rules

        relevant_rules = []
        for rule in rules:
            category = rule.get("category", "")
            if category in relevant_categories:
                relevant_rules.append(rule)

        return relevant_rules

    def _present_modifications_to_user(
        self, round_info: Dict, modifications: List[Dict]
    ) -> Dict:
        """
        向用户展示修改建议并获取选择

        Args:
            round_info: 轮次信息
            modifications: 修改建议列表

        Returns:
            用户选择结果
        """
        # 这里应该实现用户交互界面
        # 在命令行版本中，可以打印修改建议并等待用户输入
        # 在Web版本中，会通过Streamlit界面展示

        print(f"\n=== 第{round_info['round']}轮润色: {round_info['name']} ===")
        print(f"共有 {len(modifications)} 处修改建议：")
        print()

        accepted_modifications = []
        rejected_modifications = []

        for i, modification in enumerate(modifications, 1):
            print(f"修改 {i}:")
            print(f"  原文: {modification.get('original_text', '')}")
            print(f"  修改后: {modification.get('modified_text', '')}")
            print(f"  理由: {modification.get('reason', '')}")
            print(f"  位置: {modification.get('position', '')}")
            print()

            # 在实际实现中，这里会有用户交互
            # 现在模拟用户选择（接受前70%的修改）
            if i <= len(modifications) * 0.7:
                accepted_modifications.append(modification)
                print("  → 接受此修改")
            else:
                rejected_modifications.append(modification)
                print("  → 拒绝此修改")
            print()

        return {
            "accepted": accepted_modifications,
            "rejected": rejected_modifications,
            "round": round_info["round"],
        }

    def _apply_user_choices(
        self, round_info: Dict, modifications: List[Dict], user_choices: Dict
    ):
        """
        应用用户选择的修改

        Args:
            round_info: 轮次信息
            modifications: 修改建议列表
            user_choices: 用户选择
        """
        accepted_modifications = user_choices.get("accepted", [])

        for modification in accepted_modifications:
            original_text = modification.get("original_text", "")
            modified_text = modification.get("modified_text", "")

            if original_text in self.current_text:
                self.current_text = self.current_text.replace(
                    original_text, modified_text, 1
                )
                logger.info(
                    f"应用修改: {original_text[:50]}... → {modified_text[:50]}..."
                )

        # 保存用户选择
        self.user_selections[f"round_{round_info['round']}"] = user_choices

    def _apply_all_modifications(self, round_info: Dict, modifications: List[Dict]):
        """
        应用所有修改（非交互模式）

        Args:
            round_info: 轮次信息
            modifications: 修改建议列表
        """
        applied_modifications = []
        
        for modification in modifications:
            original_text = modification.get("original_text", "")
            modified_text = modification.get("modified_text", "")

            if original_text in self.current_text:
                self.current_text = self.current_text.replace(
                    original_text, modified_text, 1
                )
                
                # 保存详细的修改信息
                applied_mod = {
                    "modification_id": modification.get("modification_id", ""),
                    "original_text": original_text,
                    "modified_text": modified_text,
                    "reason": modification.get("reason", ""),
                    "rule_applied": modification.get("rule_applied", ""),
                    "rule_evidence": modification.get("rule_evidence", ""),
                    "position": modification.get("position", ""),
                    "word_changed": modification.get("word_changed", ""),
                    "transition_added": modification.get("transition_added", "")
                }
                applied_modifications.append(applied_mod)
                
                logger.info(f"自动应用修改: {original_text[:50]}...")
        
        # 将应用的修改详情保存到round_info中，供后续使用
        round_info["applied_modifications"] = applied_modifications

    def _parse_gpt_response(self, response_text: str) -> Dict:
        """
        解析GPT响应

        Args:
            response_text: GPT响应文本

        Returns:
            解析后的结果
        """
        try:
            # 尝试提取JSON部分
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            else:
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                json_text = response_text[json_start:json_end]

            # 尝试修复常见的JSON格式问题
            json_text = self._fix_json_format(json_text)
            
            return json.loads(json_text)

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"解析GPT响应失败: {str(e)}")
            logger.error(f"响应文本: {response_text[:500]}...")
            logger.error(f"尝试修复后的JSON: {json_text[:500]}...")
            return {"error": str(e)}

    def _fix_json_format(self, json_text: str) -> str:
        """
        修复常见的JSON格式问题
        
        Args:
            json_text: 原始JSON文本
            
        Returns:
            修复后的JSON文本
        """
        # 移除末尾的逗号
        json_text = re.sub(r',\s*}', '}', json_text)
        json_text = re.sub(r',\s*]', ']', json_text)
        
        # 修复未完成的字符串
        # 查找未闭合的字符串
        lines = json_text.split('\n')
        fixed_lines = []
        
        for line in lines:
            # 检查是否有未完成的字符串（以引号开头但没有结尾引号）
            if line.strip().startswith('"') and not line.strip().endswith('",') and not line.strip().endswith('"'):
                # 尝试修复未完成的字符串
                if '"modified_text":' in line:
                    # 对于未完成的modified_text，添加占位符
                    line = line + ' "[INCOMPLETE_RESPONSE]"'
                elif '"reason":' in line:
                    line = line + ' "Incomplete response"'
                elif '"rule_evidence":' in line:
                    line = line + ' "N/A"'
            
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)

    def _simple_polish_with_style(self) -> str:
        """
        简洁润色处理（只返回润色后的文本）

        Returns:
            润色后的文本
        """
        try:
            # 直接加载完整的混合风格指南
            style_guide_path = Path("data/hybrid_style_guide.json")
            if not style_guide_path.exists():
                logger.warning("混合风格指南不存在，返回原文")
                return self.current_text
            
            with open(style_guide_path, 'r', encoding='utf-8') as f:
                style_guide = json.load(f)
            
            logger.info(f"加载完整混合风格指南，包含 {style_guide.get('total_rules', 0)} 条规则")

            # 使用简洁润色prompt
            prompt_template = self.prompts.get_simple_polish_prompt()
            
            # 格式化prompt，使用完整的风格指南
            prompt = self.prompts.format_prompt(
                prompt_template,
                style_rules=json.dumps(style_guide, ensure_ascii=False, indent=2),
                paper_text=self.current_text
            )

            # 记录AI输入
            logger.info("=== AI输入日志 - 简洁润色（完整风格指南） ===")
            logger.info(f"模型: {self.ai_config['model']}")
            logger.info(f"最大令牌数: {self.ai_config['max_tokens']}")
            logger.info(f"温度参数: {self.ai_config['temperature']}")
            logger.info(f"选择风格: {self.selected_style}")
            logger.info(f"使用完整混合风格指南: {style_guide.get('total_rules', 0)} 条规则")
            logger.info(f"输入文本长度: {len(self.current_text)} 字符")
            logger.info("--- 完整Prompt ---")
            logger.info(prompt)
            logger.info("--- Prompt结束 ---")

            # 调用AI
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": f"你是一个专业的学术写作编辑专家，专门使用{self.selected_style}风格进行润色。"},
                    {"role": "user", "content": prompt}
                ],
                # max_tokens=self.ai_config["max_tokens"],
                temperature=self.ai_config["temperature"]
            )

            # 获取润色后的文本
            polished_text = response.choices[0].message.content.strip()
            
            # 记录AI输出
            logger.info("=== AI输出日志 - 简洁润色（完整风格指南） ===")
            logger.info(f"响应长度: {len(polished_text)} 字符")
            logger.info(f"使用令牌数: {response.usage.total_tokens if hasattr(response, 'usage') else '未知'}")
            logger.info("--- 润色后文本 ---")
            logger.info(polished_text[:200] + "..." if len(polished_text) > 200 else polished_text)
            logger.info("--- 文本结束 ---")
            
            return polished_text

        except Exception as e:
            logger.error(f"简洁润色处理失败: {str(e)}")
            return self.current_text

    def _generate_polishing_summary(self) -> Dict:
        """
        生成润色摘要

        Returns:
            润色摘要
        """
        total_modifications = sum(
            round_info.get("modifications_applied", 0)
            for round_info in self.modification_history
        )

        rounds_completed = len(self.modification_history)

        return {
            "total_rounds": rounds_completed,
            "total_modifications_applied": total_modifications,
            "rounds_summary": [
                {
                    "round": r["round"],
                    "name": r["round_name"],
                    "modifications": r["modifications_applied"],
                }
                for r in self.modification_history
            ],
            "interactive_mode": bool(self.user_selections),
        }

    def polish_from_file(self, file_path: str, interactive: bool = True) -> Dict:
        """
        从文件润色论文

        Args:
            file_path: 文件路径
            interactive: 是否使用交互模式

        Returns:
            润色结果
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                paper_text = f.read()

            return self.polish_paper(paper_text, interactive)

        except Exception as e:
            logger.error(f"读取文件失败 {file_path}: {str(e)}")
            return {"success": False, "error": f"读取文件失败: {str(e)}"}

    def save_polished_result(self, result: Dict, output_path: str):
        """
        保存润色结果

        Args:
            result: 润色结果
            output_path: 输出路径
        """
        try:
            # 保存润色后的文本
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(result.get("polished_text", ""))

            # 保存详细结果（JSON）
            json_path = output_path.replace(".txt", "_result.json").replace(
                ".md", "_result.json"
            )
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            logger.info(f"润色结果已保存到 {output_path} 和 {json_path}")

        except Exception as e:
            logger.error(f"保存润色结果失败: {str(e)}")


def main():
    """测试多轮润色功能"""
    # 测试文本
    test_text = """
    This study investigates the impact of climate change on agricultural productivity. 
    The research methodology involves analyzing data from multiple sources. Furthermore, 
    the findings demonstrate significant correlations between temperature increases and 
    crop yield reductions. Therefore, we recommend implementing adaptive strategies.
    """

    # 创建润色器
    polisher = MultiRoundPolisher()

    # 润色论文
    result = polisher.polish_paper(test_text, interactive=False)

    print("润色结果:")
    print(f"成功: {result.get('success', False)}")
    print(f"修改轮数: {len(result.get('modification_history', []))}")
    print(
        f"总分改进: {result.get('score_comparison', {}).get('overall_improvement', 0):.1f}"
    )


if __name__ == "__main__":
    main()
