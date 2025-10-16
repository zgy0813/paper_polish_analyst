"""
质量评分系统

提供三个维度的质量评分：风格匹配度、学术规范性、可读性。
"""

import re
from typing import Dict, List
import json
from openai import OpenAI

from ..utils.nlp_utils import NLPUtils
from ..core.prompts import PromptTemplates
from config import Config

# 设置日志
from ..utils.logger_config import get_logger

logger = get_logger(__name__)


class QualityScorer:
    """质量评分器"""

    def __init__(self):
        """初始化评分器"""
        self.nlp_utils = NLPUtils()
        try:
            ai_config = Config.get_ai_config()
            self.client = OpenAI(
                api_key=ai_config["api_key"], base_url=ai_config["base_url"]
            )
            self.prompts = PromptTemplates()
            self.ai_config = ai_config
        except Exception:
            self.client = None
            self.prompts = None
            self.ai_config = None
        self.style_guide = {}

    def load_style_guide(self) -> bool:
        """
        加载风格指南

        Returns:
            是否加载成功
        """
        try:
            with open(Config.STYLE_GUIDE_JSON, "r", encoding="utf-8") as f:
                self.style_guide = json.load(f)
            return True
        except Exception as e:
            logger.error(f"加载风格指南失败: {str(e)}")
            return False

    def score_paper(self, paper_text: str, style_guide: Dict = None) -> Dict:
        """
        对论文进行质量评分

        Args:
            paper_text: 论文文本
            style_guide: 风格指南（可选，不提供则使用默认）

        Returns:
            评分结果
        """
        logger.info("开始论文质量评分")

        try:
            # 使用提供的风格指南或默认的
            guide = style_guide or self.style_guide
            if not guide and not self.load_style_guide():
                return {"error": "无法加载风格指南"}

            guide = guide or self.style_guide

            # 计算三个维度的分数
            style_score = self._calculate_style_match_score(paper_text, guide)
            academic_score = self._calculate_academic_standard_score(paper_text)
            readability_score = self._calculate_readability_score(paper_text)

            # 计算加权总分
            weights = Config.SCORE_WEIGHTS
            total_score = (
                style_score["score"] * weights["style_match"]
                + academic_score["score"] * weights["academic_norm"]
                + readability_score["score"] * weights["readability"]
            )

            # 生成详细分析
            detailed_analysis = self._generate_detailed_analysis(
                paper_text, style_score, academic_score, readability_score
            )

            result = {
                "overall_score": round(total_score, 1),
                "style_match": style_score,
                "academic_standard": academic_score,
                "readability": readability_score,
                "detailed_analysis": detailed_analysis,
                "score_breakdown": {
                    "style_weight": weights["style_match"],
                    "academic_weight": weights["academic_norm"],
                    "readability_weight": weights["readability"],
                },
                "recommendations": self._generate_recommendations(
                    style_score, academic_score, readability_score
                ),
            }

            logger.info(f"质量评分完成，总分: {total_score:.1f}")
            return result

        except Exception as e:
            logger.error(f"质量评分失败: {str(e)}")
            return {"error": str(e)}

    def _calculate_style_match_score(self, paper_text: str, style_guide: Dict) -> Dict:
        """
        计算风格匹配度评分

        Args:
            paper_text: 论文文本
            style_guide: 风格指南

        Returns:
            风格匹配度评分结果
        """
        try:
            rules = style_guide.get("rules", [])
            if not rules:
                return {"score": 0, "description": "无风格规则可匹配"}

            # 计算规则匹配
            matched_rules = 0
            total_rules = len(rules)
            rule_details = []

            for rule in rules:
                rule_id = rule.get("rule_id", "")
                rule_type = rule.get("rule_type", "")
                description = rule.get("description", "")

                # 简化的规则匹配逻辑
                is_matched = self._check_rule_match(paper_text, rule)

                if is_matched:
                    matched_rules += 1

                rule_details.append(
                    {
                        "rule_id": rule_id,
                        "rule_type": rule_type,
                        "description": description,
                        "matched": is_matched,
                        "frequency": rule.get("frequency", 0),
                    }
                )

            # 计算分数
            base_score = (matched_rules / total_rules) * 100

            # 根据规则类型调整权重
            core_rules = [
                r for r in rule_details if r["rule_type"] == "core" and r["matched"]
            ]
            optional_rules = [
                r for r in rule_details if r["rule_type"] == "optional" and r["matched"]
            ]

            # 核心规则权重更高
            weighted_score = (
                (
                    len(core_rules) * 1.5  # 核心规则权重1.5
                    + len(optional_rules) * 1.0  # 可选规则权重1.0
                )
                / (
                    len([r for r in rules if r.get("rule_type") == "core"]) * 1.5
                    + len([r for r in rules if r.get("rule_type") == "optional"]) * 1.0
                )
                * 100
            )

            final_score = max(base_score, weighted_score)

            return {
                "score": round(final_score, 1),
                "description": f"匹配了 {matched_rules}/{total_rules} 条规则",
                "matched_rules": matched_rules,
                "total_rules": total_rules,
                "core_rules_matched": len(core_rules),
                "optional_rules_matched": len(optional_rules),
                "rule_details": rule_details,
                "strengths": [r["description"] for r in core_rules[:3]],
                "weaknesses": [
                    r["description"]
                    for r in rule_details
                    if not r["matched"] and r["rule_type"] == "core"
                ][:3],
            }

        except Exception as e:
            logger.error(f"计算风格匹配度失败: {str(e)}")
            return {"score": 0, "error": str(e)}

    def _check_rule_match(self, paper_text: str, rule: Dict) -> bool:
        """
        检查论文是否匹配特定规则

        Args:
            paper_text: 论文文本
            rule: 规则定义

        Returns:
            是否匹配
        """
        try:
            description = rule.get("description", "").lower()

            # 基于规则描述进行匹配
            if "examine" in description and "investigate" in description:
                # 检查是否使用examine而非investigate
                examine_count = len(re.findall(r"\bexamine\b", paper_text.lower()))
                investigate_count = len(
                    re.findall(r"\binvestigate\b", paper_text.lower())
                )
                return examine_count > investigate_count

            elif "passive" in description or "voice" in description:
                # 检查被动语态使用
                passive_ratio = self.nlp_utils.analyze_academic_expression(
                    paper_text
                ).get("passive_voice_ratio", 0)
                return passive_ratio > 0.1  # 被动语态比例超过10%

            elif "sentence" in description and "length" in description:
                # 检查句长
                sentence_analysis = self.nlp_utils.analyze_sentence_structure(
                    paper_text
                )
                avg_length = sentence_analysis.get("avg_sentence_length", 0)
                return 10 <= avg_length <= 25  # 理想句长范围

            elif "academic" in description or "vocabulary" in description:
                # 检查学术词汇
                vocab_analysis = self.nlp_utils.analyze_vocabulary(paper_text)
                academic_ratio = vocab_analysis.get("academic_word_ratio", 0)
                return academic_ratio > 0.1  # 学术词汇比例超过10%

            # 默认匹配逻辑
            return True

        except Exception as e:
            logger.error(f"检查规则匹配失败: {str(e)}")
            return False

    def _calculate_academic_standard_score(self, paper_text: str) -> Dict:
        """
        计算学术规范性评分

        Args:
            paper_text: 论文文本

        Returns:
            学术规范性评分结果
        """
        try:
            # 如果OpenAI不可用，直接使用NLP指标
            if not self.client or not self.prompts:
                nlp_analysis = self.nlp_utils.analyze_academic_expression(paper_text)

                # 基于NLP指标计算分数
                passive_score = min(
                    nlp_analysis.get("passive_voice_ratio", 0) * 100, 30
                )
                first_person_score = max(
                    0,
                    20
                    - nlp_analysis.get("first_person_usage", {}).get(
                        "first_person_ratio", 0
                    )
                    * 100,
                )

                total_score = passive_score + first_person_score + 50  # 基础分50

                return {
                    "score": min(total_score, 100),
                    "description": "基于NLP指标评估",
                    "passive_voice_score": passive_score,
                    "first_person_score": first_person_score,
                }

            # 使用AI进行学术规范性评估
            prompt = self.prompts.format_prompt(
                self.prompts.get_quality_assessment_prompt(),
                paper_text=paper_text,  # 使用完整文本
            )

            # 记录AI请求参数
            request_params = {
                "model": self.ai_config["model"],
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 2000,
                "temperature": self.ai_config["temperature"],
            }
            logger.info(f"质量评估AI请求参数: {request_params}")
            logger.info(f"质量评估Prompt长度: {len(prompt)} 字符")

            response = self.client.chat.completions.create(
                model=self.ai_config["model"],
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=self.ai_config["temperature"],
            )

            # 记录AI响应参数
            response_content = response.choices[0].message.content
            logger.info(
                f"质量评估AI响应参数: model={response.model}, usage={response.usage}, finish_reason={response.choices[0].finish_reason}"
            )
            logger.info(f"质量评估AI响应内容长度: {len(response_content)} 字符")
            logger.info(f"质量评估AI完整响应内容: {response_content}")

            # 解析GPT响应
            gpt_result = self._parse_gpt_response(response.choices[0].message.content)

            # 提取学术规范性评分
            academic_score = gpt_result.get("assessment", {}).get(
                "academic_standard", {}
            )

            # 如果没有GPT结果，使用NLP指标
            if not academic_score:
                nlp_analysis = self.nlp_utils.analyze_academic_expression(paper_text)

                # 基于NLP指标计算分数
                passive_score = min(
                    nlp_analysis.get("passive_voice_ratio", 0) * 100, 30
                )
                first_person_score = max(
                    0,
                    20
                    - nlp_analysis.get("first_person_usage", {}).get(
                        "first_person_ratio", 0
                    )
                    * 100,
                )

                total_score = passive_score + first_person_score + 50  # 基础分50

                academic_score = {
                    "score": min(total_score, 100),
                    "description": "基于NLP指标评估",
                    "passive_voice_score": passive_score,
                    "first_person_score": first_person_score,
                }

            return academic_score

        except Exception as e:
            logger.error(f"计算学术规范性评分失败: {str(e)}")
            # 返回默认评分
            return {
                "score": 70,
                "description": "评估失败，使用默认分数",
                "error": str(e),
            }

    def _calculate_readability_score(self, paper_text: str) -> Dict:
        """
        计算可读性评分

        Args:
            paper_text: 论文文本

        Returns:
            可读性评分结果
        """
        try:
            # 使用NLP工具计算可读性
            sentence_analysis = self.nlp_utils.analyze_sentence_structure(paper_text)
            vocab_analysis = self.nlp_utils.analyze_vocabulary(paper_text)

            # 句长评分（理想范围10-25词）
            avg_sentence_length = sentence_analysis.get("avg_sentence_length", 20)
            if 10 <= avg_sentence_length <= 25:
                length_score = 100
            else:
                length_score = max(0, 100 - abs(avg_sentence_length - 17.5) * 4)

            # 句长变化评分（适度的变化是好的）
            length_variance = sentence_analysis.get("sentence_length_variance", 0)
            variance_score = min(100, max(0, 100 - length_variance * 2))

            # 词汇丰富度评分
            vocab_richness = vocab_analysis.get("vocabulary_richness", 0)
            richness_score = min(100, vocab_richness * 200)

            # 综合可读性评分
            readability_score = (
                length_score * 0.5 + variance_score * 0.3 + richness_score * 0.2
            )

            return {
                "score": round(readability_score, 1),
                "description": "基于句式和词汇分析",
                "sentence_length_score": round(length_score, 1),
                "sentence_variation_score": round(variance_score, 1),
                "vocabulary_richness_score": round(richness_score, 1),
                "details": {
                    "avg_sentence_length": round(avg_sentence_length, 1),
                    "sentence_variance": round(length_variance, 2),
                    "vocabulary_richness": round(vocab_richness, 3),
                },
            }

        except Exception as e:
            logger.error(f"计算可读性评分失败: {str(e)}")
            return {
                "score": 70,
                "description": "评估失败，使用默认分数",
                "error": str(e),
            }

    def _generate_detailed_analysis(
        self,
        paper_text: str,
        style_score: Dict,
        academic_score: Dict,
        readability_score: Dict,
    ) -> Dict:
        """
        生成详细分析报告

        Args:
            paper_text: 论文文本
            style_score: 风格评分
            academic_score: 学术规范性评分
            readability_score: 可读性评分

        Returns:
            详细分析结果
        """
        # 基础统计
        word_count = len(paper_text.split())
        try:
            sentence_count = len(
                self.nlp_utils.analyze_sentence_structure(paper_text).get(
                    "total_sentences", 1
                )
            )
        except Exception:
            sentence_count = len([s for s in paper_text.split(".") if s.strip()])

        return {
            "basic_stats": {
                "word_count": word_count,
                "sentence_count": sentence_count,
                "avg_words_per_sentence": (
                    round(word_count / sentence_count, 1) if sentence_count > 0 else 0
                ),
            },
            "style_analysis": {
                "matched_rules": style_score.get("matched_rules", 0),
                "core_rules_matched": style_score.get("core_rules_matched", 0),
                "top_strengths": style_score.get("strengths", [])[:3],
                "main_weaknesses": style_score.get("weaknesses", [])[:3],
            },
            "academic_analysis": {
                "score_breakdown": academic_score,
                "passive_voice_usage": academic_score.get("passive_voice_score", 0),
                "first_person_usage": academic_score.get("first_person_score", 0),
            },
            "readability_analysis": {
                "overall_score": readability_score.get("score", 0),
                "sentence_complexity": readability_score.get(
                    "sentence_length_score", 0
                ),
                "vocabulary_diversity": readability_score.get(
                    "vocabulary_richness_score", 0
                ),
                "transition_usage": readability_score.get("transition_score", 0),
            },
        }

    def _generate_recommendations(
        self, style_score: Dict, academic_score: Dict, readability_score: Dict
    ) -> List[str]:
        """
        生成改进建议

        Args:
            style_score: 风格评分
            academic_score: 学术规范性评分
            readability_score: 可读性评分

        Returns:
            建议列表
        """
        recommendations = []

        # 风格匹配建议
        if style_score.get("score", 0) < 70:
            recommendations.append("建议更多遵循目标期刊的写作风格规则")
            if style_score.get("core_rules_matched", 0) < 5:
                recommendations.append("重点关注核心规则的遵循")

        # 学术规范性建议
        if academic_score.get("score", 0) < 70:
            recommendations.append("提高学术写作的规范性，注意引用格式和术语使用")

        # 可读性建议
        if readability_score.get("score", 0) < 70:
            if readability_score.get("sentence_length_score", 0) < 60:
                recommendations.append("调整句子长度，避免过长或过短的句子")
            if readability_score.get("transition_score", 0) < 60:
                recommendations.append("增加过渡词的使用，提高段落间的连贯性")
            if readability_score.get("vocabulary_richness_score", 0) < 60:
                recommendations.append("丰富词汇使用，避免重复用词")

        return recommendations[:5]  # 最多5条建议

    def _parse_gpt_response(self, response_text: str) -> Dict:
        """
        解析GPT响应

        Args:
            response_text: GPT响应文本

        Returns:
            解析后的JSON对象
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
            return {}

    def compare_scores(self, before_scores: Dict, after_scores: Dict) -> Dict:
        """
        比较润色前后的评分

        Args:
            before_scores: 润色前评分
            after_scores: 润色后评分

        Returns:
            比较结果
        """
        try:
            comparison = {
                "overall_improvement": after_scores.get("overall_score", 0)
                - before_scores.get("overall_score", 0),
                "style_improvement": after_scores.get("style_match", {}).get("score", 0)
                - before_scores.get("style_match", {}).get("score", 0),
                "academic_improvement": after_scores.get("academic_standard", {}).get(
                    "score", 0
                )
                - before_scores.get("academic_standard", {}).get("score", 0),
                "readability_improvement": after_scores.get("readability", {}).get(
                    "score", 0
                )
                - before_scores.get("readability", {}).get("score", 0),
                "before_scores": before_scores,
                "after_scores": after_scores,
            }

            # 计算改进百分比
            for key in [
                "overall_improvement",
                "style_improvement",
                "academic_improvement",
                "readability_improvement",
            ]:
                before_key = key.replace("_improvement", "")
                before_value = (
                    before_scores.get(before_key, {}).get("score", 0)
                    if isinstance(before_scores.get(before_key), dict)
                    else before_scores.get(before_key, 0)
                )

                if before_value > 0:
                    improvement_pct = (comparison[key] / before_value) * 100
                    comparison[f"{key}_percentage"] = round(improvement_pct, 1)

            return comparison

        except Exception as e:
            logger.error(f"比较评分失败: {str(e)}")
            return {"error": str(e)}


def main():
    """测试质量评分功能"""
    # 创建评分器
    scorer = QualityScorer()

    # 测试文本
    test_text = """
    This study investigates the impact of climate change on agricultural productivity.
    The research methodology involves analyzing data from multiple sources. Furthermore,
    the findings demonstrate significant correlations between temperature increases and
    crop yield reductions. Therefore, we recommend implementing adaptive strategies.
    """

    # 评分
    scores = scorer.score_paper(test_text)

    print("质量评分结果:")
    print(f"总分: {scores.get('overall_score', 0)}")
    print(f"风格匹配: {scores.get('style_match', {}).get('score', 0)}")
    print(f"学术规范: {scores.get('academic_standard', {}).get('score', 0)}")
    print(f"可读性: {scores.get('readability', {}).get('score', 0)}")


if __name__ == "__main__":
    main()
