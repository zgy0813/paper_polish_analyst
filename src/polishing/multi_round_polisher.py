"""
多轮交互式润色模块

实现分三轮的论文润色：句式结构、词汇优化、段落衔接，支持用户交互确认。
"""

import json
import re
from typing import Dict, List, Tuple
from pathlib import Path
from datetime import datetime

from ..analysis.quality_scorer import QualityScorer
from ..core.prompts import PromptTemplates
from ..core.ai_client import get_ai_client, AICallError
from config import Config

# 设置日志
from ..utils.logger_config import get_logger
from ..utils.style_dimensions import normalize_dimension_label

logger = get_logger(__name__)


class MultiRoundPolisher:
    """多轮润色器"""

    def __init__(self):
        """初始化润色器"""
        self.ai_client = get_ai_client()
        self.prompts = PromptTemplates()
        self.quality_scorer = QualityScorer()
        self.ai_config = Config.get_ai_config()

        # 加载规则库
        self.style_guide = {}
        self._load_style_guide()

        # 润色状态
        self.current_text = ""
        self.modification_history = []
        self.user_selections = {}
        # 已移除风格选择状态

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

    # 已移除风格设置方法

    def polish_paper(self, paper_text: str, interactive: bool = False) -> Dict:
        """
        润色论文（支持交互/非交互，按规则库执行）

        Args:
            paper_text: 原始论文文本
            interactive: 是否使用交互式润色

        Returns:
            润色结果
        """
        logger.info(f"开始{'交互式' if interactive else '非交互式'}润色论文（基于规则库）")

        try:
            # 初始化
            self.current_text = paper_text
            self.modification_history = []
            self.user_selections = {}

            # 计算润色前评分
            before_scores = self.quality_scorer.score_paper(paper_text)

            # 执行润色
            if interactive:
                self._interactive_polishing()
            else:
                self._batch_polishing()

            # 计算润色后评分
            after_scores = self.quality_scorer.score_paper(self.current_text)

            # 比较评分
            score_comparison = self.quality_scorer.compare_scores(
                before_scores, after_scores
            )

            # 生成最终结果（不包含风格字段）
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
                "interactive_mode": interactive,
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

    def polish_paper_simple(self, paper_text: str) -> Dict:
        """
        简洁润色论文（只返回润色后的文本，不包含详细修改说明）

        Args:
            paper_text: 原始论文文本

        Returns:
            简洁润色结果
        """
        logger.info("开始简洁润色论文（基于规则库）")

        try:
            # 初始化
            self.current_text = paper_text
            self.modification_history = []
            self.user_selections = {}

            # 计算润色前评分
            before_scores = self.quality_scorer.score_paper(paper_text)

            # 执行简洁润色（规则库）
            polished_text = self._simple_polish()

            # 计算润色后评分
            after_scores = self.quality_scorer.score_paper(polished_text)

            # 比较评分
            score_comparison = self.quality_scorer.compare_scores(
                before_scores, after_scores
            )

            # 生成简洁结果（不包含风格字段）
            final_result = {
                "success": True,
                "original_text": paper_text,
                "polished_text": polished_text,
                "before_scores": before_scores,
                "after_scores": after_scores,
                "score_comparison": score_comparison,
                "polishing_summary": {
                    "total_rounds": 1,
                    "total_modifications_applied": 1,
                },
                "timestamp": datetime.now().isoformat(),
                "simple_mode": True,
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
        """已移除风格逻辑。请使用无风格的规则库润色接口。"""
        logger.warning(
            "polish_paper_with_choices 已弃用，改用 polish_paper(paper_text, interactive=False)"
        )
        return self.polish_paper(paper_text, interactive=False)

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

    # 已移除：_interactive_polishing_with_style（风格相关逻辑）

    # 已移除：_batch_polishing_with_style（风格相关逻辑）

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

            # 调用AI
            try:
                response_text = self.ai_client.call_ai(
                    prompt=prompt,
                    system_message="你是一个专业的学术写作编辑专家。",
                    task_name="综合润色",
                    additional_params={"规则数量": len(all_rules)}
                )
            except AICallError as e:
                logger.error(f"AI调用失败: {str(e)}")
                return {
                    "sentence_structure": {"modifications": [], "summary": {"total_modifications": 0}},
                    "vocabulary_optimization": {"modifications": [], "summary": {"total_modifications": 0}},
                    "paragraph_coherence": {"modifications": [], "summary": {"total_modifications": 0}},
                    "error": f"AI调用失败: {str(e)}"
                }
            
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

    # 已移除：_generate_comprehensive_modifications_with_style（风格相关逻辑）

    # 已移除：_display_style_info（风格相关逻辑）

    # 已移除：_generate_round_modifications_with_style（风格相关逻辑）

    # 已移除：_format_style_rules_for_prompt（风格相关逻辑）

    # 已移除：_find_applicable_rule（风格相关逻辑）

    # 已移除：_generate_style_polishing_summary（风格相关逻辑）

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
            response_text = self.ai_client.call_ai(
                prompt=prompt,
                system_message="你是一个专业的学术写作专家。",
                task_name=f"AI分析 - {task_type}",
                temperature=0.3,
                max_tokens=4000,
                additional_params={
                    "top_p": 0.9,
                    "frequency_penalty": 0.1,
                    "presence_penalty": 0.1
                }
            )
            return response_text.strip()

        except AICallError as e:
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

            # 调用AI
            try:
                response_content = self.ai_client.call_ai(
                    prompt=prompt,
                    system_message="你是一个专业的学术写作专家。",
                    task_name=f"润色轮次{round_info['round']} - {round_info['round_name']}",
                    max_tokens=self.ai_config["max_tokens"],
                    temperature=self.ai_config["temperature"]
                )
            except AICallError as e:
                logger.error(f"润色轮次{round_info['round']}AI调用失败: {str(e)}")
                return []

            # 解析响应
            result = self._parse_gpt_response(response_content)

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

        focus_mapping = {
            "sentence_structure": ["Rhythm & Flow", "Section Patterns"],
            "vocabulary": ["Terminology Management", "Voice & Tone"],
            "transitions": [
                "Rhythm & Flow",
                "Narrative Strategies",
                "Section Patterns",
            ],
        }

        target_categories = {
            normalize_dimension_label(cat)
            for cat in focus_mapping.get(focus, [])
        }

        if not target_categories:
            return rules

        relevant_rules = [
            rule
            for rule in rules
            if normalize_dimension_label(rule.get("category", ""))
            in target_categories
        ]

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

    def _simple_polish(self) -> str:
        """
        简洁润色处理（规则库，无风格字段，仅返回润色后的文本）

        Returns:
            润色后的文本
        """
        try:
            # 使用已加载的规则库
            if not self.style_guide:
                logger.warning("规则库未加载，返回原文")
                return self.current_text

            rules_count = self.style_guide.get('total_rules') or len(self.style_guide.get('rules', []))
            logger.info(f"使用规则库进行简洁润色，规则数量: {rules_count}")

            # 使用简洁润色prompt
            prompt_template = self.prompts.get_simple_polish_prompt()

            # 格式化prompt，传入规则库（不含风格选择）
            prompt = self.prompts.format_prompt(
                prompt_template,
                style_rules=json.dumps(self.style_guide, ensure_ascii=False, indent=2),
                paper_text=self.current_text
            )

            # 调用AI
            try:
                polished_text = self.ai_client.call_ai(
                    prompt=prompt,
                    system_message="你是一个专业的学术写作编辑专家。",
                    task_name="简洁润色",
                    additional_params={
                        "规则数量": rules_count
                    }
                ).strip()
            except AICallError as e:
                logger.error(f"AI调用失败: {str(e)}")
                return self.current_text

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
