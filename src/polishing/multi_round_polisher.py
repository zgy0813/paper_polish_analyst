"""
多轮交互式润色模块

实现分三轮的论文润色：句式结构、词汇优化、段落衔接，支持用户交互确认。
"""

import json
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

        # 回退到原始风格指南
        if not self.style_guide_generator.load_style_guide():
            logger.warning("无法加载风格指南，将使用默认设置")
            self.style_guide = {}
        else:
            self.style_guide = self.style_guide_generator.style_guide

    def polish_paper(self, paper_text: str, interactive: bool = True) -> Dict:
        """
        润色论文

        Args:
            paper_text: 原始论文文本
            interactive: 是否使用交互模式

        Returns:
            润色结果
        """
        logger.info(f"开始润色论文，交互模式: {interactive}")

        try:
            # 初始化
            self.current_text = paper_text
            self.modification_history = []
            self.user_selections = {}

            # 计算润色前评分
            before_scores = self.quality_scorer.score_paper(paper_text)

            if interactive:
                # 交互式润色
                result = self._interactive_polishing()
            else:
                # 非交互式润色（一次性处理）
                self._batch_polishing()

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

    def polish_paper_with_choices(
        self,
        paper_text: str,
        style_preference: str = "balanced",
        interactive: bool = True,
    ) -> Dict:
        """
        基于风格选择的论文润色

        Args:
            paper_text: 原始论文文本
            style_preference: 风格偏好 ("conservative", "balanced", "innovative")
            interactive: 是否使用交互模式

        Returns:
            润色结果
        """
        logger.info(f"开始基于风格选择的论文润色，风格: {style_preference}")

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

            if interactive:
                # 交互式润色
                result = self._interactive_polishing_with_style()
            else:
                # 非交互式润色
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
        批量润色（非交互式）

        Returns:
            润色结果
        """
        logger.info("开始批量润色")

        # 三轮润色：句式结构调整、词汇优化、段落衔接
        rounds = [
            {"round": 1, "name": "句式结构调整", "focus": "sentence_structure"},
            {"round": 2, "name": "词汇优化", "focus": "vocabulary"},
            {"round": 3, "name": "段落衔接", "focus": "transitions"},
        ]

        for round_info in rounds:
            logger.info(f"执行第{round_info['round']}轮润色: {round_info['name']}")

            # 生成修改建议
            modifications = self._generate_round_modifications(round_info)

            if not modifications:
                continue

            # 自动应用所有修改
            self._apply_all_modifications(round_info, modifications)

            # 记录修改历史
            self.modification_history.append(
                {
                    "round": round_info["round"],
                    "round_name": round_info["name"],
                    "modifications_proposed": len(modifications),
                    "modifications_applied": len(modifications),
                    "auto_applied": True,
                }
            )

        return {"batch_completed": True}

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
        基于风格选择的批量润色（非交互式）

        Returns:
            润色结果
        """
        logger.info(f"开始基于风格选择的批量润色，风格: {self.selected_style}")

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
                continue

            # 自动应用所有修改
            self._apply_all_modifications(round_info, modifications)

            # 记录修改历史
            self.modification_history.append(
                {
                    "round": round_info["round"],
                    "round_name": round_info["name"],
                    "style": self.selected_style,
                    "modifications_proposed": len(modifications),
                    "modifications_applied": len(modifications),
                    "auto_applied": True,
                }
            )

        return {"batch_completed": True}

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
        for modification in modifications:
            original_text = modification.get("original_text", "")
            modified_text = modification.get("modified_text", "")

            if original_text in self.current_text:
                self.current_text = self.current_text.replace(
                    original_text, modified_text, 1
                )
                logger.info(f"自动应用修改: {original_text[:50]}...")

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

            return json.loads(json_text)

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"解析GPT响应失败: {str(e)}")
            logger.error(f"响应文本: {response_text[:500]}...")
            return {"error": str(e)}

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
