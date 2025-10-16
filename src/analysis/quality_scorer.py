"""
质量评分系统

提供三个维度的质量评分：风格匹配度、学术规范性、可读性。
"""

import re
from typing import Dict, List
import json

from ..utils.nlp_utils import NLPUtils
from config import Config

# 设置日志
from ..utils.logger_config import get_logger

logger = get_logger(__name__)


class QualityScorer:
    """质量评分器"""

    def __init__(self):
        """初始化评分器"""
        self.nlp_utils = NLPUtils()
        self.style_guide = {}
        logger.info("质量评分器初始化完成（纯NLP模式）")

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
        计算学术规范性评分（基于NLP指标）

        Args:
            paper_text: 论文文本

        Returns:
            学术规范性评分结果
        """
        try:
            logger.info("开始基于NLP指标计算学术规范性评分")
            
            # 获取多种NLP分析结果
            academic_analysis = self.nlp_utils.analyze_academic_expression(paper_text)
            sentence_analysis = self.nlp_utils.analyze_sentence_structure(paper_text)
            vocab_analysis = self.nlp_utils.analyze_vocabulary(paper_text)
            
            # 1. 被动语态评分（适度使用被动语态，比例在0.1-0.3之间为最佳）
            passive_ratio = academic_analysis.get("passive_voice_ratio", 0)
            if 0.1 <= passive_ratio <= 0.3:
                passive_score = 100
            elif passive_ratio < 0.1:
                passive_score = 60 + passive_ratio * 400  # 0-0.1映射到60-100
            else:
                passive_score = max(0, 100 - (passive_ratio - 0.3) * 300)  # 0.3以上递减
            
            # 2. 第一人称使用评分（学术写作中应适度使用）
            first_person_ratio = academic_analysis.get("first_person_usage", {}).get("first_person_ratio", 0)
            if first_person_ratio <= 0.05:
                first_person_score = 100
            elif first_person_ratio <= 0.15:
                first_person_score = 80
            else:
                first_person_score = max(0, 80 - (first_person_ratio - 0.15) * 400)
            
            # 3. 学术词汇比例评分
            academic_word_ratio = vocab_analysis.get("academic_word_ratio", 0)
            if academic_word_ratio >= 0.05:
                academic_vocab_score = min(100, 60 + academic_word_ratio * 800)
            else:
                academic_vocab_score = academic_word_ratio * 1200
            
            # 4. 句子复杂度评分（适度的复杂度）
            avg_sentence_length = sentence_analysis.get("avg_sentence_length", 20)
            if 15 <= avg_sentence_length <= 25:
                complexity_score = 100
            elif avg_sentence_length < 15:
                complexity_score = 60 + avg_sentence_length * 2.67
            else:
                complexity_score = max(0, 100 - (avg_sentence_length - 25) * 4)
            
            # 5. 词汇多样性评分
            vocab_richness = vocab_analysis.get("vocabulary_richness", 0)
            diversity_score = min(100, vocab_richness * 300)
            
            # 6. 连接词使用评分
            transition_words = ["however", "therefore", "furthermore", "moreover", "consequently", "nevertheless"]
            transition_count = sum(paper_text.lower().count(word) for word in transition_words)
            word_count = len(paper_text.split())
            transition_ratio = transition_count / word_count if word_count > 0 else 0
            
            if 0.01 <= transition_ratio <= 0.03:
                transition_score = 100
            else:
                transition_score = max(0, 100 - abs(transition_ratio - 0.02) * 5000)
            
            # 加权计算总分
            weights = {
                "passive": 0.25,
                "first_person": 0.15,
                "academic_vocab": 0.20,
                "complexity": 0.15,
                "diversity": 0.15,
                "transitions": 0.10
            }
            
            total_score = (
                passive_score * weights["passive"] +
                first_person_score * weights["first_person"] +
                academic_vocab_score * weights["academic_vocab"] +
                complexity_score * weights["complexity"] +
                diversity_score * weights["diversity"] +
                transition_score * weights["transitions"]
            )
            
            # 生成详细描述
            descriptions = []
            if passive_score >= 80:
                descriptions.append("被动语态使用恰当")
            if first_person_score >= 80:
                descriptions.append("第一人称使用适度")
            if academic_vocab_score >= 80:
                descriptions.append("学术词汇丰富")
            if complexity_score >= 80:
                descriptions.append("句子复杂度适中")
            if diversity_score >= 80:
                descriptions.append("词汇多样性良好")
            if transition_score >= 80:
                descriptions.append("连接词使用恰当")
            
            description = "基于NLP指标评估" + ("，" + "，".join(descriptions) if descriptions else "")
            
            return {
                "score": round(total_score, 1),
                "description": description,
                "details": {
                    "passive_voice_score": round(passive_score, 1),
                    "passive_voice_ratio": round(passive_ratio, 3),
                    "first_person_score": round(first_person_score, 1),
                    "first_person_ratio": round(first_person_ratio, 3),
                    "academic_vocab_score": round(academic_vocab_score, 1),
                    "academic_word_ratio": round(academic_word_ratio, 3),
                    "complexity_score": round(complexity_score, 1),
                    "avg_sentence_length": round(avg_sentence_length, 1),
                    "diversity_score": round(diversity_score, 1),
                    "vocab_richness": round(vocab_richness, 3),
                    "transition_score": round(transition_score, 1),
                    "transition_ratio": round(transition_ratio, 3)
                }
            }

        except Exception as e:
            logger.error(f"计算学术规范性评分失败: {str(e)}")
            return {
                "score": 70,
                "description": "评估失败，使用默认分数",
                "error": str(e),
            }

    def _calculate_readability_score(self, paper_text: str) -> Dict:
        """
        计算可读性评分（增强版NLP指标）

        Args:
            paper_text: 论文文本

        Returns:
            可读性评分结果
        """
        try:
            logger.info("开始基于增强NLP指标计算可读性评分")
            
            # 获取多种NLP分析结果
            sentence_analysis = self.nlp_utils.analyze_sentence_structure(paper_text)
            vocab_analysis = self.nlp_utils.analyze_vocabulary(paper_text)
            academic_analysis = self.nlp_utils.analyze_academic_expression(paper_text)

            # 1. 句长评分（学术写作理想范围15-25词）
            avg_sentence_length = sentence_analysis.get("avg_sentence_length", 20)
            if 15 <= avg_sentence_length <= 25:
                length_score = 100
            elif avg_sentence_length < 15:
                length_score = 70 + avg_sentence_length * 2  # 15以下映射到70-100
            else:
                length_score = max(0, 100 - (avg_sentence_length - 25) * 3)  # 25以上递减

            # 2. 句长变化评分（适度的变化是好的）
            length_variance = sentence_analysis.get("sentence_length_variance", 0)
            if 0.2 <= length_variance <= 0.6:
                variance_score = 100
            else:
                variance_score = max(0, 100 - abs(length_variance - 0.4) * 200)

            # 3. 词汇丰富度评分
            vocab_richness = vocab_analysis.get("vocabulary_richness", 0)
            if vocab_richness >= 0.6:
                richness_score = 100
            else:
                richness_score = vocab_richness * 166.67  # 映射到0-100

            # 4. 复合句比例评分
            compound_ratio = sentence_analysis.get("compound_sentence_ratio", 0)
            if 0.3 <= compound_ratio <= 0.7:
                compound_score = 100
            elif compound_ratio < 0.3:
                compound_score = 60 + compound_ratio * 133.33
            else:
                compound_score = max(0, 100 - (compound_ratio - 0.7) * 333.33)

            # 5. 词汇复杂度评分（基于学术词汇比例）
            academic_word_ratio = vocab_analysis.get("academic_word_ratio", 0)
            if 0.05 <= academic_word_ratio <= 0.15:
                complexity_score = 100
            elif academic_word_ratio < 0.05:
                complexity_score = academic_word_ratio * 2000
            else:
                complexity_score = max(0, 100 - (academic_word_ratio - 0.15) * 500)

            # 6. 段落结构评分（基于句子数量）
            sentences = sentence_analysis.get("sentence_count", 0)
            words = len(paper_text.split())
            if words > 0:
                sentences_per_word = sentences / words * 1000  # 每千词的句子数
                if 15 <= sentences_per_word <= 35:
                    structure_score = 100
                else:
                    structure_score = max(0, 100 - abs(sentences_per_word - 25) * 5)
            else:
                structure_score = 50

            # 7. 连接词密度评分
            transition_words = ["however", "therefore", "furthermore", "moreover", "consequently", "nevertheless", "meanwhile", "additionally"]
            transition_count = sum(paper_text.lower().count(word) for word in transition_words)
            word_count = len(paper_text.split())
            transition_density = transition_count / word_count if word_count > 0 else 0
            
            if 0.01 <= transition_density <= 0.03:
                transition_score = 100
            else:
                transition_score = max(0, 100 - abs(transition_density - 0.02) * 5000)

            # 加权计算总分
            weights = {
                "length": 0.25,
                "variance": 0.15,
                "richness": 0.20,
                "compound": 0.15,
                "complexity": 0.15,
                "structure": 0.05,
                "transition": 0.05
            }

            total_score = (
                length_score * weights["length"] +
                variance_score * weights["variance"] +
                richness_score * weights["richness"] +
                compound_score * weights["compound"] +
                complexity_score * weights["complexity"] +
                structure_score * weights["structure"] +
                transition_score * weights["transition"]
            )

            # 生成详细描述
            descriptions = []
            if length_score >= 80:
                descriptions.append("句子长度适中")
            if variance_score >= 80:
                descriptions.append("句式变化丰富")
            if richness_score >= 80:
                descriptions.append("词汇丰富多样")
            if compound_score >= 80:
                descriptions.append("复合句使用恰当")
            if complexity_score >= 80:
                descriptions.append("词汇复杂度适中")
            if transition_score >= 80:
                descriptions.append("连接词使用恰当")

            description = "基于增强NLP指标评估" + ("，" + "，".join(descriptions) if descriptions else "")

            return {
                "score": round(total_score, 1),
                "description": description,
                "details": {
                    "sentence_length_score": round(length_score, 1),
                    "avg_sentence_length": round(avg_sentence_length, 1),
                    "sentence_variation_score": round(variance_score, 1),
                    "sentence_variance": round(length_variance, 2),
                    "vocabulary_richness_score": round(richness_score, 1),
                    "vocabulary_richness": round(vocab_richness, 3),
                    "compound_sentence_score": round(compound_score, 1),
                    "compound_sentence_ratio": round(compound_ratio, 3),
                    "complexity_score": round(complexity_score, 1),
                    "academic_word_ratio": round(academic_word_ratio, 3),
                    "structure_score": round(structure_score, 1),
                    "sentences_per_1000_words": round(sentences_per_word if words > 0 else 0, 1),
                    "transition_score": round(transition_score, 1),
                    "transition_density": round(transition_density, 3)
                }
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
