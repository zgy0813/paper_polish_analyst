"""
规则验证器

对比官方规则与往期期刊的实际使用情况，验证规则一致性。
"""

import json
import re
from typing import Dict, List
from pathlib import Path

from ..core.pymupdf_extractor import PyMuPDFExtractor
from ..utils.nlp_utils import NLPUtils
from config import Config

# 设置日志
from ..utils.logger_config import get_logger

logger = get_logger(__name__)


class RuleValidator:
    """规则验证器"""

    def __init__(self):
        """初始化验证器"""
        self.pdf_extractor = PyMuPDFExtractor(Config.JOURNALS_DIR, Config.EXTRACTED_DIR)
        self.nlp_utils = NLPUtils()

        # 验证阈值
        self.high_consistency_threshold = 0.8  # 80%以上遵循率
        self.low_consistency_threshold = 0.5  # 50%以下遵循率

    def validate_rules(
        self, official_rules: List[Dict], empirical_rules: List[Dict] = None
    ) -> Dict:
        """
        验证规则一致性

        Args:
            official_rules: 官方规则列表
            empirical_rules: 经验规则列表（可选）

        Returns:
            验证结果
        """
        logger.info("开始验证规则一致性")

        try:
            # 获取往期期刊文本
            journal_texts = self._get_journal_texts()

            if not journal_texts:
                return {"error": "没有找到往期期刊文本"}

            # 验证官方规则
            official_validation = self._validate_official_rules(
                official_rules, journal_texts
            )

            # 验证经验规则（如果提供）
            empirical_validation = {}
            if empirical_rules:
                empirical_validation = self._validate_empirical_rules(
                    empirical_rules, journal_texts
                )

            # 检测规则冲突
            conflicts = self._detect_rule_conflicts(
                official_rules, empirical_rules or []
            )

            # 生成验证报告
            validation_report = {
                "validation_date": self._get_current_timestamp(),
                "journal_papers_analyzed": len(journal_texts),
                "official_rules_validation": official_validation,
                "empirical_rules_validation": empirical_validation,
                "rule_conflicts": conflicts,
                "summary": self._generate_validation_summary(
                    official_validation, empirical_validation, conflicts
                ),
            }

            logger.info("规则验证完成")
            return validation_report

        except Exception as e:
            logger.error(f"规则验证失败: {str(e)}")
            return {"error": str(e)}

    def _get_journal_texts(self) -> List[str]:
        """获取往期期刊文本"""
        try:
            texts = self.pdf_extractor.get_extracted_texts()
            return [text for _, text in texts]
        except Exception as e:
            logger.error(f"获取期刊文本失败: {str(e)}")
            return []

    def _validate_official_rules(
        self, official_rules: List[Dict], journal_texts: List[str]
    ) -> Dict:
        """验证官方规则"""
        validation_results = {
            "total_rules": len(official_rules),
            "high_consistency_rules": [],
            "low_consistency_rules": [],
            "medium_consistency_rules": [],
            "rule_details": [],
        }

        for rule in official_rules:
            try:
                # 检查规则在期刊中的遵循情况
                compliance_rate = self._check_rule_compliance(rule, journal_texts)

                rule_result = {
                    "rule_id": rule.get("rule_id", ""),
                    "description": rule.get("description", ""),
                    "category": rule.get("category", ""),
                    "compliance_rate": compliance_rate,
                    "priority": rule.get("priority", "medium"),
                    "source": "official_guide",
                }

                # 分类规则
                if compliance_rate >= self.high_consistency_threshold:
                    validation_results["high_consistency_rules"].append(rule_result)
                elif compliance_rate <= self.low_consistency_threshold:
                    validation_results["low_consistency_rules"].append(rule_result)
                else:
                    validation_results["medium_consistency_rules"].append(rule_result)

                validation_results["rule_details"].append(rule_result)

            except Exception as e:
                logger.warning(f"验证规则失败 {rule.get('rule_id', '')}: {str(e)}")
                continue

        return validation_results

    def _validate_empirical_rules(
        self, empirical_rules: List[Dict], journal_texts: List[str]
    ) -> Dict:
        """验证经验规则"""
        validation_results = {
            "total_rules": len(empirical_rules),
            "high_consistency_rules": [],
            "low_consistency_rules": [],
            "medium_consistency_rules": [],
            "rule_details": [],
        }

        for rule in empirical_rules:
            try:
                # 经验规则已经有遵循率，直接使用
                frequency = rule.get("frequency", 0)

                rule_result = {
                    "rule_id": rule.get("rule_id", ""),
                    "description": rule.get("description", ""),
                    "category": rule.get("category", ""),
                    "compliance_rate": frequency,
                    "rule_type": rule.get("rule_type", ""),
                    "source": "empirical_analysis",
                }

                # 分类规则
                if frequency >= self.high_consistency_threshold:
                    validation_results["high_consistency_rules"].append(rule_result)
                elif frequency <= self.low_consistency_threshold:
                    validation_results["low_consistency_rules"].append(rule_result)
                else:
                    validation_results["medium_consistency_rules"].append(rule_result)

                validation_results["rule_details"].append(rule_result)

            except Exception as e:
                logger.warning(f"验证经验规则失败 {rule.get('rule_id', '')}: {str(e)}")
                continue

        return validation_results

    def _check_rule_compliance(self, rule: Dict, journal_texts: List[str]) -> float:
        """
        检查规则遵循率

        Args:
            rule: 规则定义
            journal_texts: 期刊文本列表

        Returns:
            遵循率 (0-1)
        """
        try:
            description = rule.get("description", "").lower()

            # 基于规则描述进行匹配
            if "examine" in description and "investigate" in description:
                return self._check_vocabulary_preference(
                    journal_texts, "examine", "investigate"
                )

            elif "passive" in description or "voice" in description:
                return self._check_passive_voice_usage(journal_texts)

            elif "sentence" in description and "length" in description:
                return self._check_sentence_length_compliance(journal_texts)

            elif "title" in description and "case" in description:
                return self._check_title_case_compliance(journal_texts)

            elif "citation" in description:
                return self._check_citation_format_compliance(journal_texts)

            # 默认返回中等遵循率
            return 0.5

        except Exception as e:
            logger.warning(f"检查规则遵循率失败: {str(e)}")
            return 0.0

    def _check_vocabulary_preference(
        self, texts: List[str], preferred: str, alternative: str
    ) -> float:
        """检查词汇偏好"""
        preferred_count = 0
        alternative_count = 0

        for text in texts:
            preferred_count += len(re.findall(rf"\b{preferred}\b", text.lower()))
            alternative_count += len(re.findall(rf"\b{alternative}\b", text.lower()))

        total = preferred_count + alternative_count
        return preferred_count / total if total > 0 else 0.5

    def _check_passive_voice_usage(self, texts: List[str]) -> float:
        """检查被动语态使用"""
        total_ratios = []

        for text in texts:
            analysis = self.nlp_utils.analyze_academic_expression(text)
            passive_ratio = analysis.get("passive_voice_ratio", 0)
            total_ratios.append(passive_ratio)

        avg_ratio = sum(total_ratios) / len(total_ratios) if total_ratios else 0
        # 假设理想被动语态比例在0.1-0.3之间
        if 0.1 <= avg_ratio <= 0.3:
            return 1.0
        else:
            return max(0, 1 - abs(avg_ratio - 0.2) * 2)

    def _check_sentence_length_compliance(self, texts: List[str]) -> float:
        """检查句长遵循情况"""
        total_ratios = []

        for text in texts:
            analysis = self.nlp_utils.analyze_sentence_structure(text)
            avg_length = analysis.get("avg_sentence_length", 0)
            # 假设理想句长在15-25词之间
            if 15 <= avg_length <= 25:
                total_ratios.append(1.0)
            else:
                ratio = max(0, 1 - abs(avg_length - 20) / 20)
                total_ratios.append(ratio)

        return sum(total_ratios) / len(total_ratios) if total_ratios else 0.5

    def _check_title_case_compliance(self, texts: List[str]) -> float:
        """检查标题大小写遵循情况"""
        # 这里简化处理，实际需要更复杂的标题识别逻辑
        return 0.8  # 假设80%遵循率

    def _check_citation_format_compliance(self, texts: List[str]) -> float:
        """检查引用格式遵循情况"""
        # 这里简化处理，实际需要更复杂的引用格式识别逻辑
        return 0.7  # 假设70%遵循率

    def _detect_rule_conflicts(
        self, official_rules: List[Dict], empirical_rules: List[Dict]
    ) -> List[Dict]:
        """检测规则冲突"""
        conflicts = []

        for official_rule in official_rules:
            official_desc = official_rule.get("description", "").lower()

            for empirical_rule in empirical_rules:
                empirical_desc = empirical_rule.get("description", "").lower()

                # 简单的冲突检测：检查关键词重叠但建议相反
                if self._is_rule_conflict(official_desc, empirical_desc):
                    conflicts.append(
                        {
                            "official_rule": {
                                "rule_id": official_rule.get("rule_id", ""),
                                "description": official_rule.get("description", ""),
                                "priority": official_rule.get("priority", ""),
                            },
                            "empirical_rule": {
                                "rule_id": empirical_rule.get("rule_id", ""),
                                "description": empirical_rule.get("description", ""),
                                "frequency": empirical_rule.get("frequency", 0),
                            },
                            "conflict_type": "contradictory_advice",
                            "severity": "medium",
                        }
                    )

        return conflicts

    def _is_rule_conflict(self, desc1: str, desc2: str) -> bool:
        """判断两个规则是否冲突"""
        # 简化的冲突检测逻辑
        conflict_keywords = [
            ("use", "avoid"),
            ("should", "should not"),
            ("always", "never"),
            ("prefer", "avoid"),
        ]

        for positive, negative in conflict_keywords:
            if positive in desc1 and negative in desc2:
                return True
            if negative in desc1 and positive in desc2:
                return True

        return False

    def _generate_validation_summary(
        self,
        official_validation: Dict,
        empirical_validation: Dict,
        conflicts: List[Dict],
    ) -> Dict:
        """生成验证摘要"""
        return {
            "total_official_rules": official_validation.get("total_rules", 0),
            "total_empirical_rules": empirical_validation.get("total_rules", 0),
            "high_consistency_official": len(
                official_validation.get("high_consistency_rules", [])
            ),
            "low_consistency_official": len(
                official_validation.get("low_consistency_rules", [])
            ),
            "high_consistency_empirical": len(
                empirical_validation.get("high_consistency_rules", [])
            ),
            "low_consistency_empirical": len(
                empirical_validation.get("low_consistency_rules", [])
            ),
            "rule_conflicts_count": len(conflicts),
            "overall_consistency_score": self._calculate_overall_consistency(
                official_validation, empirical_validation
            ),
        }

    def _calculate_overall_consistency(
        self, official_validation: Dict, empirical_validation: Dict
    ) -> float:
        """计算整体一致性分数"""
        official_high = len(official_validation.get("high_consistency_rules", []))
        official_total = official_validation.get("total_rules", 1)
        official_score = official_high / official_total

        empirical_high = len(empirical_validation.get("high_consistency_rules", []))
        empirical_total = empirical_validation.get("total_rules", 1)
        empirical_score = empirical_high / empirical_total

        return (official_score + empirical_score) / 2

    def _get_current_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime

        return datetime.now().isoformat()

    def save_validation_report(self, report: Dict, output_path: str = None):
        """保存验证报告"""
        if not output_path:
            output_path = "data/rule_validation_report.json"

        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)

            logger.info(f"验证报告已保存到: {output_path}")

        except Exception as e:
            logger.error(f"保存验证报告失败: {str(e)}")


def main():
    """测试规则验证功能"""
    validator = RuleValidator()

    # 模拟官方规则
    official_rules = [
        {
            "rule_id": "test-official-1",
            "description": "Use passive voice in academic writing",
            "category": "学术表达",
            "priority": "high",
        }
    ]

    # 验证规则
    result = validator.validate_rules(official_rules)

    if "error" not in result:
        print("验证成功!")
        print(f"分析论文数: {result.get('journal_papers_analyzed', 0)}")
        print(
            f"官方规则数: {result.get('official_rules_validation', {}).get('total_rules', 0)}"
        )
    else:
        print(f"验证失败: {result['error']}")


if __name__ == "__main__":
    main()
