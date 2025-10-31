"""
风格指南生成器

基于分析结果生成带示例库的结构化风格指南，包括JSON和Markdown格式。
"""

import json
from typing import Dict, List
from pathlib import Path
from datetime import datetime

from config import Config

# 设置日志
from ..utils.logger_config import get_logger
from ..utils.style_dimensions import (
    DIMENSION_LABELS,
    map_rule_to_dimension,
    normalize_dimension_label,
)

logger = get_logger(__name__)


class StyleGuideGenerator:
    """风格指南生成器"""

    def __init__(self):
        """初始化生成器"""
        self.style_guide = {}
        self.markdown_content = ""

    def generate_style_guide(self, analysis_data: Dict) -> Dict:
        """
        生成风格指南

        Args:
            analysis_data: 分析数据（来自增量分析或分层分析）

        Returns:
            生成的风格指南
        """
        logger.info("Starting style guide generation")

        try:
            # 处理不同类型的输入数据
            if "final_guide" in analysis_data:
                # 来自增量分析的完整结果
                style_data = analysis_data["final_guide"]
            elif "rules" in analysis_data:
                # 直接的风格指南数据
                style_data = analysis_data
            else:
                # 从批次汇总生成
                batch_summaries = analysis_data.get("batches", [])
                style_data = self._generate_from_batches(batch_summaries)

            # 生成结构化风格指南
            self.style_guide = self._create_structured_guide(style_data)

            # 生成Markdown版本
            self.markdown_content = self._generate_markdown_guide()

            # 保存文件
            self._save_guide_files()

            logger.info("Style guide generation completed")
            return self.style_guide

        except Exception as e:
            logger.error(f"Style guide generation failed: {str(e)}")
            return {"error": str(e)}

    def _generate_from_batches(self, batch_summaries: List[Dict]) -> Dict:
        """
        从批次汇总生成风格指南

        Args:
            batch_summaries: 批次汇总列表

        Returns:
            风格指南数据
        """
        # 收集所有规则
        all_rules = []
        total_papers = 0

        for batch in batch_summaries:
            if batch.get("success", False) and "batch_summary" in batch:
                summary = batch["batch_summary"]
                if "preliminary_rules" in summary:
                    all_rules.extend(summary["preliminary_rules"])
                total_papers += batch.get("paper_count", 0)

        # 整合规则
        integrated_rules = self._integrate_rules(all_rules)

        return {
            "rules": integrated_rules,
            "total_papers_analyzed": total_papers,
            "analysis_date": datetime.now().isoformat(),
        }

    def _integrate_rules(self, all_rules: List[Dict]) -> List[Dict]:
        """
        整合重复的规则

        Args:
            all_rules: 所有规则列表

        Returns:
            整合后的规则列表
        """
        # 按规则类型分组
        rule_groups = {}

        for rule in all_rules:
            if not isinstance(rule, dict) or "description" not in rule:
                continue

            # 使用描述的前几个词作为分组键
            key_words = rule["description"].split()[:3]
            group_key = " ".join(key_words)

            if group_key not in rule_groups:
                rule_groups[group_key] = []
            rule_groups[group_key].append(rule)

        # 整合每个组
        integrated_rules = []

        for group_key, rules in rule_groups.items():
            if not rules:
                continue

            # 选择最具代表性的规则
            representative_rule = max(rules, key=lambda r: r.get("consistency_rate", 0))

            # 合并统计信息
            total_consistency = sum(r.get("consistency_rate", 0) for r in rules)
            avg_consistency = total_consistency / len(rules)

            # 确定规则类型
            if avg_consistency >= Config.CORE_RULE_THRESHOLD:
                rule_type = "core"
            elif avg_consistency >= Config.OPTIONAL_RULE_THRESHOLD:
                rule_type = "optional"
            else:
                rule_type = "suggested"

            # 创建整合后的规则
            integrated_rule = {
                "rule_id": f"{rule_type}-{group_key.replace(' ', '-').lower()}",
                "rule_type": rule_type,
                "category": self._categorize_rule(representative_rule["description"]),
                "description": representative_rule["description"],
                "frequency": avg_consistency,
                "consistency_rate": avg_consistency,
                "examples": self._collect_examples(rules),
                "statistics": self._aggregate_statistics(rules),
                "evidence": f"基于{len(rules)}个批次的分析，平均遵循率{avg_consistency:.2%}",
            }

            integrated_rules.append(integrated_rule)

        # 按频率排序
        integrated_rules.sort(key=lambda r: r["frequency"], reverse=True)

        return integrated_rules

    def _categorize_rule(self, description: str) -> str:
        """
        将规则描述映射到8大写作维度

        Args:
            description: 规则描述

        Returns:
            规则类别（统一后的维度标签）
        """
        dimension = map_rule_to_dimension(description or "")
        return normalize_dimension_label(dimension)

    def _collect_examples(self, rules: List[Dict]) -> List[Dict]:
        """
        收集规则示例

        Args:
            rules: 规则列表

        Returns:
            示例列表
        """
        examples = []

        for rule in rules:
            if "examples" in rule and isinstance(rule["examples"], list):
                examples.extend(rule["examples"])
            elif "evidence" in rule:
                # 从证据中提取示例
                evidence = rule["evidence"]
                if "→" in evidence or "to" in evidence:
                    # 简单的示例提取
                    examples.append(
                        {
                            "before": (
                                evidence.split("→")[0].strip()
                                if "→" in evidence
                                else evidence
                            ),
                            "after": (
                                evidence.split("→")[1].strip()
                                if "→" in evidence
                                else evidence
                            ),
                            "source": "batch_analysis",
                            "context": "风格分析结果",
                        }
                    )

        return examples[:5]  # 限制示例数量

    def _aggregate_statistics(self, rules: List[Dict]) -> Dict:
        """
        聚合规则统计信息

        Args:
            rules: 规则列表

        Returns:
            聚合的统计信息
        """
        stats = {}

        for rule in rules:
            if "statistics" in rule and isinstance(rule["statistics"], dict):
                for key, value in rule["statistics"].items():
                    if key not in stats:
                        stats[key] = 0
                    if isinstance(value, (int, float)):
                        stats[key] += value

        return stats

    def _create_structured_guide(self, style_data: Dict) -> Dict:
        """
        创建结构化的风格指南

        Args:
            style_data: 风格数据

        Returns:
            结构化风格指南
        """
        # 计算规则统计
        rules = style_data.get("rules", [])
        core_rules = [r for r in rules if r.get("rule_type") == "core"]
        optional_rules = [r for r in rules if r.get("rule_type") == "optional"]
        suggested_rules = [r for r in rules if r.get("rule_type") == "suggested"]

        # 按类别分组
        categories = {}
        for rule in rules:
            original_category = rule.get("category", "")

            if original_category:
                normalized_category = normalize_dimension_label(original_category)
                if normalized_category not in DIMENSION_LABELS:
                    normalized_category = normalize_dimension_label(
                        map_rule_to_dimension(rule.get("description", ""))
                    )
            else:
                normalized_category = normalize_dimension_label(
                    map_rule_to_dimension(rule.get("description", ""))
                )

            rule["category"] = normalized_category

            if normalized_category not in categories:
                categories[normalized_category] = []
            categories[normalized_category].append(rule)

        structured_guide = {
            "style_guide_version": "1.0",
            "generation_date": datetime.now().isoformat(),
            "total_papers_analyzed": style_data.get("total_papers_analyzed", 0),
            "analysis_method": "incremental_layered_analysis",
            "rule_summary": {
                "total_rules": len(rules),
                "core_rules": len(core_rules),
                "optional_rules": len(optional_rules),
                "suggested_rules": len(suggested_rules),
            },
            "categories": categories,
            "rules": rules,
            "usage_guidelines": {
                "core_rules": "核心规则：80%以上论文遵循，建议严格遵循",
                "optional_rules": "可选规则：50%-80%论文遵循，可根据情况选择",
                "suggested_rules": "建议规则：遵循率较低，仅供参考",
            },
            "quality_metrics": self._calculate_quality_metrics(rules),
        }

        return structured_guide

    def _calculate_quality_metrics(self, rules: List[Dict]) -> Dict:
        """
        计算质量指标

        Args:
            rules: 规则列表

        Returns:
            质量指标
        """
        if not rules:
            return {}

        frequencies = [rule.get("frequency", 0) for rule in rules]
        consistency_rates = [rule.get("consistency_rate", 0) for rule in rules]

        return {
            "avg_frequency": sum(frequencies) / len(frequencies),
            "avg_consistency": sum(consistency_rates) / len(consistency_rates),
            "high_consistency_rules": len(
                [r for r in rules if r.get("consistency_rate", 0) > 0.8]
            ),
            "coverage_score": len(rules) / 50,  # 假设50个规则为满分
            "reliability_score": sum(consistency_rates) / len(consistency_rates),
        }

    def _generate_markdown_guide(self) -> str:
        """
        生成Markdown格式的风格指南

        Returns:
            Markdown内容
        """
        if not self.style_guide:
            return ""

        md_content = []

        # 标题和概述
        md_content.append("# 学术论文写作风格指南")
        md_content.append("")
        md_content.append(
            f"**生成时间**: {self.style_guide.get('generation_date', '')}"
        )
        md_content.append(
            f"**分析论文数**: {self.style_guide.get('total_papers_analyzed', 0)}"
        )
        md_content.append(
            f"**规则总数**: {self.style_guide.get('rule_summary', {}).get('total_rules', 0)}"
        )
        md_content.append("")

        # 规则摘要
        summary = self.style_guide.get("rule_summary", {})
        md_content.append("## 规则摘要")
        md_content.append("")
        md_content.append(
            f"- **核心规则**: {summary.get('core_rules', 0)} 条 (80%+论文遵循)"
        )
        md_content.append(
            f"- **可选规则**: {summary.get('optional_rules', 0)} 条 (50%-80%论文遵循)"
        )
        md_content.append(
            f"- **建议规则**: {summary.get('suggested_rules', 0)} 条 (遵循率较低)"
        )
        md_content.append("")

        # 使用指南
        guidelines = self.style_guide.get("usage_guidelines", {})
        md_content.append("## 使用指南")
        md_content.append("")
        for rule_type, guideline in guidelines.items():
            md_content.append(
                f"- **{rule_type.replace('_', ' ').title()}**: {guideline}"
            )
        md_content.append("")

        # 按类别展示规则
        categories = self.style_guide.get("categories", {})
        for category, rules in categories.items():
            md_content.append(f"## {category}")
            md_content.append("")

            for rule in rules:
                rule_type = rule.get("rule_type", "unknown")
                frequency = rule.get("frequency", 0)

                # 规则标题
                md_content.append(f"### {rule.get('description', '')}")
                md_content.append("")
                md_content.append(f"- **类型**: {rule_type}")
                md_content.append(f"- **遵循率**: {frequency:.1%}")
                md_content.append(f"- **规则ID**: `{rule.get('rule_id', '')}`")
                md_content.append("")

                # 示例
                examples = rule.get("examples", [])
                if examples:
                    md_content.append("**示例**:")
                    md_content.append("")
                    for i, example in enumerate(examples[:3], 1):  # 最多显示3个示例
                        if "before" in example and "after" in example:
                            md_content.append(f"{i}. **原文**: {example['before']}")
                            md_content.append(f"   **修改后**: {example['after']}")
                            md_content.append("")

                # 统计信息
                statistics = rule.get("statistics", {})
                if statistics:
                    md_content.append("**统计数据**:")
                    for key, value in statistics.items():
                        md_content.append(f"- {key}: {value}")
                    md_content.append("")

                md_content.append("---")
                md_content.append("")

        # 质量指标
        quality_metrics = self.style_guide.get("quality_metrics", {})
        if quality_metrics:
            md_content.append("## 质量指标")
            md_content.append("")
            md_content.append(
                f"- **平均遵循率**: {quality_metrics.get('avg_frequency', 0):.1%}"
            )
            md_content.append(
                f"- **平均一致性**: {quality_metrics.get('avg_consistency', 0):.1%}"
            )
            md_content.append(
                f"- **高一致性规则数**: {quality_metrics.get('high_consistency_rules', 0)}"
            )
            md_content.append(
                f"- **覆盖度评分**: {quality_metrics.get('coverage_score', 0):.2f}"
            )
            md_content.append(
                f"- **可靠性评分**: {quality_metrics.get('reliability_score', 0):.2f}"
            )
            md_content.append("")

        return "\n".join(md_content)

    def _save_guide_files(self):
        """保存风格指南文件"""
        try:
            # 保存JSON版本
            with open(Config.STYLE_GUIDE_JSON, "w", encoding="utf-8") as f:
                json.dump(self.style_guide, f, ensure_ascii=False, indent=2)

            # 保存Markdown版本
            with open(Config.STYLE_GUIDE_MD, "w", encoding="utf-8") as f:
                f.write(self.markdown_content)

            logger.info(
                f"风格指南已保存到 {Config.STYLE_GUIDE_JSON} 和 {Config.STYLE_GUIDE_MD}"
            )

        except Exception as e:
            logger.error(f"保存风格指南文件失败: {str(e)}")

    def load_style_guide(self) -> Dict:
        """
        加载现有的风格指南

        Returns:
            风格指南数据
        """
        if not Path(Config.STYLE_GUIDE_JSON).exists():
            return {"error": "风格指南文件不存在"}

        try:
            with open(Config.STYLE_GUIDE_JSON, "r", encoding="utf-8") as f:
                self.style_guide = json.load(f)
            return self.style_guide
        except Exception as e:
            return {"error": f"加载风格指南失败: {str(e)}"}

    def get_rules_by_category(self, category: str) -> List[Dict]:
        """
        获取指定类别的规则

        Args:
            category: 规则类别

        Returns:
            规则列表
        """
        if not self.style_guide:
            self.load_style_guide()

        categories = self.style_guide.get("categories", {})
        return categories.get(category, [])

    def get_core_rules(self) -> List[Dict]:
        """获取核心规则"""
        if not self.style_guide:
            self.load_style_guide()

        rules = self.style_guide.get("rules", [])
        return [rule for rule in rules if rule.get("rule_type") == "core"]

    def generate_hybrid_guide(
        self, official_rules: List[Dict] = None, empirical_data: Dict = None
    ) -> Dict:
        """
        生成混合风格指南（官方规则 + 经验规则）
        使用简单的字段拼接，避免不必要的AI调用

        Args:
            official_rules: 官方规则列表
            empirical_data: 经验分析数据

        Returns:
            混合风格指南
        """
        logger.info("Starting hybrid style guide generation (field merging mode)")

        try:
            # 1. 直接从经验数据中提取规则（无需AI调用）
            empirical_rules = []
            if empirical_data:
                empirical_rules = self._extract_rules_from_categories(empirical_data)

            # 2. 简单字段拼接，无需AI整合
            all_rules = []

            # 添加官方规则（最高优先级）
            for rule in official_rules or []:
                rule_copy = rule.copy()
                rule_copy.update(
                    {
                        "source": "official_guide",
                        "priority": "highest",
                        "enforcement_level": "mandatory",
                    }
                )
                all_rules.append(rule_copy)

            # 添加经验规则
            for rule in empirical_rules:
                rule_copy = rule.copy()
                rule_copy.update(
                    {
                        "source": "empirical_analysis",
                        "priority": self._determine_empirical_priority(rule),
                        "enforcement_level": self._determine_enforcement_level(rule),
                    }
                )
                all_rules.append(rule_copy)

            # 3. 生成混合指南（无需冲突解决）
            hybrid_guide = {
                "style_guide_version": "2.0",
                "generation_date": self._get_current_timestamp(),
                "guide_type": "hybrid",
                "total_rules": len(all_rules),
                "official_rules_count": len(
                    [r for r in all_rules if r.get("source") == "official_guide"]
                ),
                "empirical_rules_count": len(
                    [r for r in all_rules if r.get("source") == "empirical_analysis"]
                ),
                "rule_summary": self._generate_rule_summary(all_rules),
                "categories": self._categorize_rules(all_rules),
                "rules": all_rules,
                "usage_guidelines": self._generate_usage_guidelines(),
                "quality_metrics": self._calculate_hybrid_quality_metrics(all_rules),
            }

            logger.info(
                f"Hybrid style guide generation completed with {len(all_rules)} rules (fast merge mode)"
            )
            return hybrid_guide

        except Exception as e:
            logger.error(f"Hybrid style guide generation failed: {str(e)}")
            return {"error": str(e)}

    def _integrate_official_and_empirical(
        self, official_rules: List[Dict], empirical_rules: List[Dict]
    ) -> List[Dict]:
        """整合官方规则和经验规则"""
        integrated_rules = []

        # 添加官方规则（最高优先级）
        for rule in official_rules:
            integrated_rule = rule.copy()
            integrated_rule.update(
                {
                    "rule_type": "official",
                    "priority": "highest",
                    "source": "official_guide",
                    "enforcement_level": "mandatory",
                }
            )
            integrated_rules.append(integrated_rule)

        # 添加经验规则
        for rule in empirical_rules:
            # 检查是否与官方规则冲突
            if not self._has_conflict_with_official(rule, official_rules):
                integrated_rule = rule.copy()
                integrated_rule.update(
                    {
                        "source": "empirical_analysis",
                        "enforcement_level": self._determine_enforcement_level(rule),
                    }
                )
                integrated_rules.append(integrated_rule)

        return integrated_rules

    def _has_conflict_with_official(
        self, empirical_rule: Dict, official_rules: List[Dict]
    ) -> bool:
        """检查经验规则是否与官方规则冲突"""
        empirical_desc = empirical_rule.get("description", "").lower()

        for official_rule in official_rules:
            official_desc = official_rule.get("description", "").lower()

            # 检查关键词冲突
            if self._is_rule_conflict(empirical_desc, official_desc):
                return True

        return False

    def _is_rule_conflict(self, desc1: str, desc2: str) -> bool:
        """判断两个规则描述是否冲突"""
        conflict_pairs = [
            ("use", "avoid"),
            ("should", "should not"),
            ("always", "never"),
            ("prefer", "avoid"),
            ("active", "passive"),
            ("examine", "investigate"),
        ]

        for positive, negative in conflict_pairs:
            if (positive in desc1 and negative in desc2) or (
                negative in desc1 and positive in desc2
            ):
                return True

        return False

    def _determine_enforcement_level(self, rule: Dict) -> str:
        """确定规则的执行级别"""
        frequency = rule.get("frequency", 0)
        rule_type = rule.get("rule_type", "suggested")

        # 处理新的规则类型（frequent, common, alternative）
        if rule_type in ["core", "frequent"] or frequency >= 0.8:
            return "strongly_recommended"
        elif rule_type in ["optional", "common"] or 0.5 <= frequency < 0.8:
            return "recommended"
        else:
            return "suggested"

    def _extract_rules_from_categories(self, style_guide_data: Dict) -> List[Dict]:
        """
        从 rule_categories 结构中提取所有规则

        Args:
            style_guide_data: 包含 rule_categories 的风格指南数据

        Returns:
            规则列表
        """
        rules = []
        rule_categories = style_guide_data.get("rule_categories", {})

        for category_name, category_data in rule_categories.items():
            if isinstance(category_data, dict) and "rules" in category_data:
                category_rules = category_data["rules"]
                # 为每个规则添加类别信息
                for rule in category_rules:
                    rule_copy = rule.copy()
                    rule_copy["category_name"] = category_name
                    # 确保规则有正确的来源标识
                    if "source" not in rule_copy:
                        rule_copy["source"] = "empirical_analysis"
                    rules.append(rule_copy)

        logger.info(
            f"Extracted {len(rules)} empirical rules from {len(rule_categories)} categories"
        )
        return rules

    def _determine_empirical_priority(self, rule: Dict) -> str:
        """根据经验规则的频率确定优先级"""
        frequency = rule.get("frequency", 0)
        if frequency >= 0.8:
            return "high"  # 高频规则
        elif frequency >= 0.5:
            return "medium"  # 中频规则
        else:
            return "low"  # 低频规则

    def _resolve_conflicts(self, rules: List[Dict]) -> List[Dict]:
        """解决规则冲突"""
        resolved_rules = []

        # 按优先级排序：官方规则 > 核心经验规则 > 可选经验规则 > 建议规则
        priority_order = {"official": 0, "core": 1, "optional": 2, "suggested": 3}

        sorted_rules = sorted(
            rules,
            key=lambda x: (
                priority_order.get(x.get("rule_type", "suggested"), 3),
                -x.get("frequency", 0),
            ),
        )

        for rule in sorted_rules:
            # 检查是否与已添加的规则冲突
            has_conflict = False
            for existing_rule in resolved_rules:
                if self._is_rule_conflict(
                    rule.get("description", "").lower(),
                    existing_rule.get("description", "").lower(),
                ):
                    has_conflict = True
                    break

            if not has_conflict:
                resolved_rules.append(rule)

        return resolved_rules

    def _generate_rule_summary(self, rules: List[Dict]) -> Dict:
        """生成规则摘要"""
        official_count = len([r for r in rules if r.get("source") == "official_guide"])
        empirical_count = len(
            [r for r in rules if r.get("source") == "empirical_analysis"]
        )

        core_count = len([r for r in rules if r.get("rule_type") == "core"])
        optional_count = len([r for r in rules if r.get("rule_type") == "optional"])
        suggested_count = len([r for r in rules if r.get("rule_type") == "suggested"])

        return {
            "total_rules": len(rules),
            "official_rules": official_count,
            "empirical_rules": empirical_count,
            "core_rules": core_count,
            "optional_rules": optional_count,
            "suggested_rules": suggested_count,
        }

    def _categorize_rules(self, rules: List[Dict]) -> Dict[str, List[Dict]]:
        """对规则进行分类"""
        categories = {}

        for rule in rules:
            current_category = rule.get("category", "")
            if current_category:
                category = normalize_dimension_label(current_category)
                if category not in DIMENSION_LABELS:
                    category = normalize_dimension_label(
                        map_rule_to_dimension(rule.get("description", ""))
                    )
            else:
                category = normalize_dimension_label(
                    map_rule_to_dimension(rule.get("description", ""))
                )
                rule["category"] = category

            rule["category"] = category

            if category not in categories:
                categories[category] = []
            categories[category].append(rule)

        return categories

    def _generate_usage_guidelines(self) -> Dict:
        """生成使用指南"""
        return {
            "official_rules": "Official Rules: Journal requirements that must be strictly followed",
            "core_rules": "Core Rules: Followed by 80%+ papers, strongly recommended",
            "optional_rules": "Optional Rules: Followed by 50%-80% papers, choose as appropriate",
            "suggested_rules": "Suggested Rules: Lower adherence rate, for reference only",
            "conflict_resolution": "When rules conflict, official rules take priority over empirical rules",
        }

    def _calculate_hybrid_quality_metrics(self, rules: List[Dict]) -> Dict:
        """计算混合指南质量指标"""
        if not rules:
            return {}

        frequencies = [
            r.get("frequency", 0) for r in rules if r.get("frequency") is not None
        ]
        avg_frequency = sum(frequencies) / len(frequencies) if frequencies else 0

        official_rules = [r for r in rules if r.get("source") == "official_guide"]
        empirical_rules = [r for r in rules if r.get("source") == "empirical_analysis"]

        return {
            "avg_frequency": avg_frequency,
            "official_rule_ratio": len(official_rules) / len(rules),
            "empirical_rule_ratio": len(empirical_rules) / len(rules),
            "high_consistency_rules": len(
                [r for r in rules if r.get("frequency", 0) >= 0.8]
            ),
            "coverage_score": min(1.0, len(rules) / 50),  # 假设50条规则为满分
            "reliability_score": avg_frequency,
        }

    def _get_current_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime

        return datetime.now().isoformat()

    def save_style_guide_markdown(self, style_guide: Dict, output_path: str):
        """保存风格指南为Markdown格式"""
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, "w", encoding="utf-8") as f:
                f.write(self._generate_markdown_content(style_guide))

            logger.info(f"风格指南Markdown已保存到: {output_path}")

        except Exception as e:
            logger.error(f"保存风格指南Markdown失败: {str(e)}")

    def _generate_markdown_content(self, style_guide: Dict) -> str:
        """生成Markdown内容"""
        content = []

        # 标题和基本信息
        guide_type = style_guide.get("guide_type", "Style Guide")
        if guide_type == "hybrid":
            guide_type = "Hybrid Style Guide"
        elif guide_type == "风格指南":
            guide_type = "Style Guide"

        content.append(f"# {guide_type}")
        content.append("")
        content.append(f"**Generation Date**: {style_guide.get('generation_date', '')}")
        content.append(f"**Version**: {style_guide.get('style_guide_version', '1.0')}")
        content.append(f"**Total Rules**: {style_guide.get('total_rules', 0)}")

        if "official_rules_count" in style_guide:
            content.append(
                f"**Official Rules**: {style_guide.get('official_rules_count', 0)}"
            )
        if "empirical_rules_count" in style_guide:
            content.append(
                f"**Empirical Rules**: {style_guide.get('empirical_rules_count', 0)}"
            )

        content.append("")

        # 规则摘要
        if "rule_summary" in style_guide:
            summary = style_guide["rule_summary"]
            content.append("## Rule Summary")
            content.append("")
            content.append(f"- Total Rules: {summary.get('total_rules', 0)}")
            content.append(f"- Official Rules: {summary.get('official_rules', 0)}")
            content.append(f"- Empirical Rules: {summary.get('empirical_rules', 0)}")
            content.append(f"- Core Rules: {summary.get('core_rules', 0)}")
            content.append(f"- Optional Rules: {summary.get('optional_rules', 0)}")
            content.append(f"- Suggested Rules: {summary.get('suggested_rules', 0)}")
            content.append("")

        # 使用指南
        if "usage_guidelines" in style_guide:
            content.append("## Usage Guidelines")
            content.append("")
            guidelines = style_guide["usage_guidelines"]
            for key, value in guidelines.items():
                # 翻译使用指南
                key_translation = {
                    "core_rules": "Core Rules",
                    "optional_rules": "Optional Rules",
                    "suggested_rules": "Suggested Rules",
                }
                translated_key = key_translation.get(key, key.replace("_", " ").title())
                content.append(f"- **{translated_key}**: {value}")
            content.append("")

        # 规则详情
        if "rules" in style_guide:
            content.append("## Rule Details")
            content.append("")

            # 按类别分组
            categories = style_guide.get("categories", {})
            for category, category_rules in categories.items():
                content.append(f"### {category}")
                content.append("")

                for rule in category_rules:
                    content.append(f"#### {rule.get('rule_id', 'Unknown')}")
                    content.append("")
                    content.append(f"**Description**: {rule.get('description', '')}")
                    content.append("")

                    if rule.get("priority"):
                        content.append(f"**Priority**: {rule.get('priority', '')}")
                    if rule.get("rule_type"):
                        content.append(f"**Type**: {rule.get('rule_type', '')}")
                    if rule.get("source"):
                        source_translation = {
                            "official_guide": "Official Guide",
                            "empirical_analysis": "Empirical Analysis",
                        }
                        source = source_translation.get(
                            rule.get("source", ""), rule.get("source", "")
                        )
                        content.append(f"**Source**: {source}")
                    if rule.get("frequency"):
                        content.append(
                            f"**Adherence Rate**: {rule.get('frequency', 0):.1%}"
                        )

                    content.append("")

                    # 示例
                    if rule.get("examples"):
                        content.append("**Examples**:")
                        content.append("")
                        for example in rule.get("examples", []):
                            if isinstance(example, dict):
                                if "correct" in example and "incorrect" in example:
                                    content.append(
                                        f"- ✅ **Correct**: {example['correct']}"
                                    )
                                    content.append(
                                        f"- ❌ **Incorrect**: {example['incorrect']}"
                                    )
                                    if "explanation" in example:
                                        content.append(
                                            f"  - **Explanation**: {example['explanation']}"
                                        )
                                elif "before" in example and "after" in example:
                                    content.append(f"- **Before**: {example['before']}")
                                    content.append(f"- **After**: {example['after']}")
                            else:
                                content.append(f"- {example}")
                        content.append("")

                    content.append("---")
                    content.append("")

        return "\n".join(content)

    # ============ 官方规则加载与综合指南生成 ============
    
    def load_official_rules_from_json(self, json_path: str = "data/official_guides/AMJ_style_guide.json") -> Dict:
        """
        直接加载官方规则JSON（不做AI解析）
        
        Args:
            json_path: JSON文件路径
            
        Returns:
            官方规则原始内容
        """
        from ..core.official_guide_parser import OfficialGuideParser
        
        parser = OfficialGuideParser()
        return parser.load_manual_json_guide(json_path)
    
    def generate_comprehensive_hybrid_guide(
        self,
        official_rules_path: str = "data/official_guides/AMJ_style_guide.json",
        style_features_data: Dict = None
    ) -> Dict:
        """
        生成综合Hybrid Style Guide
        
        Part 1: 官方规则（直接从JSON加载）
        Part 2: 风格特征（从历史分析得出）
        
        Args:
            official_rules_path: 官方规则JSON路径
            style_features_data: 风格特征数据
            
        Returns:
            综合Hybrid Style Guide
        """
        logger.info("生成综合Hybrid Style Guide")
        
        # Part 1: 加载官方规则
        official_rules = self.load_official_rules_from_json(official_rules_path)
        
        # Part 2: 风格特征
        if not style_features_data:
            style_features_data = self._load_style_features_from_cache()
        
        # 合并两部分
        hybrid_guide = {
            "guide_type": "comprehensive_hybrid",
            "generation_date": datetime.now().isoformat(),
            "part_1_official_rules": {
                "description": "AMJ Official Style Guide - Mandatory Format Rules",
                "source": "AMJ_style_guide.json",
                "content": official_rules
            },
            "part_2_writing_style_features": {
                "description": "AMJ Writing Style Features - Soft Writing Characteristics",
                "source": "Historical Paper Analysis",
                "features": style_features_data.get("features", {})
            }
        }
        
        # 保存JSON和Markdown两种格式
        self._save_hybrid_guide_json(hybrid_guide)
        self._save_hybrid_guide_markdown(hybrid_guide)
        
        return hybrid_guide
    
    def _load_style_features_from_cache(self) -> Dict:
        """从缓存加载风格特征数据"""
        cache_path = Path("data/style_features_cache.json")
        if not cache_path.exists():
            logger.warning("风格特征缓存文件不存在")
            return {"features": {}}
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载风格特征缓存失败: {str(e)}")
            return {"features": {}}
    
    def _save_hybrid_guide_json(self, hybrid_guide: Dict):
        """保存Hybrid Style Guide为JSON格式"""
        try:
            output_path = Path("data/hybrid_style_guide.json")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(hybrid_guide, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Hybrid Style Guide JSON已保存到: {output_path}")
        except Exception as e:
            logger.error(f"保存JSON失败: {str(e)}")
    
    def _save_hybrid_guide_markdown(self, hybrid_guide: Dict):
        """
        生成Markdown格式的Hybrid Style Guide
        
        优化点：
        - 添加目录导航
        - 改进视觉层次
        - 美化官方规则展示
        - 增强可读性
        """
        md_content = []
        
        # 标题和生成时间
        md_content.append("# AMJ Comprehensive Style Guide\n")
        md_content.append(f"**Generated**: {hybrid_guide['generation_date']}\n\n")
        
        # 添加目录导航
        md_content.append("## 📑 Table of Contents\n\n")
        md_content.append("- [Part 1: Official Rules (官方规范)](#part-1-official-rules-官方规范)\n")
        md_content.append("- [Part 2: Writing Style Features (写作风格特征)](#part-2-writing-style-features-写作风格特征)\n\n")
        md_content.append("---\n\n")
        
        # Part 1: 官方规则
        md_content.append("## Part 1: Official Rules (官方规范)\n")
        md_content.append("*Must follow - Mandatory format and citation rules*\n\n")
        md_content.append("> 💡 **Note**: These are official AMJ style requirements. Follow them strictly for accepted papers.\n\n")
        
        official_content = hybrid_guide["part_1_official_rules"]["content"]
        
        # 获取AMJ内容
        amj_key = "Academy of Management STYLE GUIDE FOR AUTHORS"
        if amj_key in official_content:
            amj_content = official_content[amj_key]
            
            section_count = 0
            for section_name, section_data in amj_content.items():
                # 跳过introduction
                if section_name == "introduction":
                    continue
                
                section_count += 1
                
                # 使用更醒目的章节标题
                md_content.append(f"### {section_count}. {section_name}\n\n")
                
                # 处理不同类型的内容
                if isinstance(section_data, dict):
                    if "content" in section_data:
                        # 使用引用块美化长段落
                        content = section_data['content']
                        if len(content) > 200:
                            # 长段落使用缩进
                            md_content.append(f"    {content}\n\n")
                        else:
                            md_content.append(f"{content}\n\n")
                    else:
                        # 如果是字典但没有content字段，遍历子项
                        for sub_key, sub_value in section_data.items():
                            md_content.append(f"**{sub_key}**: ")
                            if isinstance(sub_value, str):
                                md_content.append(f"{sub_value}\n\n")
                            elif isinstance(sub_value, dict):
                                md_content.append("\n")
                                for k, v in sub_value.items():
                                    md_content.append(f"  - *{k}*: {v}\n")
                                md_content.append("\n")
                elif isinstance(section_data, str):
                    md_content.append(f"{section_data}\n\n")
        
        md_content.append("---\n\n")
        
        # Part 2: 风格特征
        md_content.append("## Part 2: Writing Style Features (写作风格特征)\n")
        md_content.append("*Recommended - Soft writing characteristics of excellent AMJ papers*\n\n")
        md_content.append("> 🎨 **Tip**: These style features are derived from analysis of published AMJ papers. They represent patterns commonly found in high-quality manuscripts.\n\n")
        
        features = hybrid_guide["part_2_writing_style_features"]["features"]
        
        feature_titles = {
            "narrative_strategies": "Narrative Strategies (叙事策略)",
            "argumentation_patterns": "Argumentation Patterns (论证模式)",
            "rhetorical_devices": "Rhetorical Devices (修辞手法)",
            "rhythm_flow": "Rhythm & Flow (节奏流畅度)",
            "voice_tone": "Voice & Tone (语态语气)",
            "terminology_management": "Terminology Management (术语管理)",
            "section_patterns": "Section-Specific Patterns (章节模式)",
            "citation_artistry": "Citation Integration Artistry (引用艺术)"
        }
        
        feature_descriptions = {
            "narrative_strategies": "How AMJ papers structure their narrative flow",
            "argumentation_patterns": "Common argumentation and theory-building approaches",
            "rhetorical_devices": "Language techniques for emphasis and persuasion",
            "rhythm_flow": "Sentence variety and paragraph transition patterns",
            "voice_tone": "Author presence and communication style",
            "terminology_management": "Handling of technical terms and jargon",
            "section_patterns": "Section-specific writing patterns",
            "citation_artistry": "Citation density and integration techniques"
        }
        
        feature_num = 1
        for feature_key, feature_title in feature_titles.items():
            feature_data = features.get(feature_key, {})
            if not feature_data:
                continue
            
            md_content.append(f"### {feature_num}. {feature_title}\n\n")
            
            # 添加描述
            if feature_key in feature_descriptions:
                md_content.append(f"*{feature_descriptions[feature_key]}*\n\n")
            
            # 格式化特征数据（美化版）
            self._format_feature_markdown_enhanced(feature_data, md_content)
            
            md_content.append("\n")
            feature_num += 1
        
        # 保存文件
        output_path = Path("data/hybrid_style_guide.md")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(''.join(md_content))
        
        logger.info(f"Hybrid Style Guide Markdown已保存到: {output_path}")
    
    def _format_feature_markdown(self, feature_data: Dict, md_content: List[str]):
        """格式化风格特征为Markdown（基础版）"""
        if isinstance(feature_data, dict):
            for key, value in feature_data.items():
                if isinstance(value, dict):
                    md_content.append(f"**{key}**:\n")
                    self._format_feature_markdown(value, md_content)
                elif isinstance(value, list):
                    md_content.append(f"**{key}**:\n")
                    for item in value:
                        md_content.append(f"- {item}\n")
                else:
                    md_content.append(f"- **{key}**: {value}\n")
        else:
            md_content.append(f"- {feature_data}\n")
    
    def _format_feature_markdown_enhanced(self, feature_data: Dict, md_content: List[str]):
        """格式化风格特征为Markdown（增强版，更美观）"""
        if isinstance(feature_data, dict):
            for key, value in feature_data.items():
                if isinstance(value, dict):
                    # 字典：使用小标题
                    md_content.append(f"#### {key.replace('_', ' ').title()}\n\n")
                    self._format_feature_markdown_enhanced(value, md_content)
                elif isinstance(value, list):
                    # 列表：使用表格（如果元素是字典）或列表
                    if value and isinstance(value[0], dict):
                        # 表格格式
                        md_content.append(f"**{key.replace('_', ' ').title()}**:\n\n")
                        md_content.append("| Key | Value |\n|-----|-------|\n")
                        for item in value:
                            if isinstance(item, dict):
                                for k, v in item.items():
                                    md_content.append(f"| {k} | {v} |\n")
                        md_content.append("\n")
                    else:
                        # 普通列表
                        md_content.append(f"**{key.replace('_', ' ').title()}**:\n")
                        for item in value:
                            md_content.append(f"- {item}\n")
                        md_content.append("\n")
                elif isinstance(value, (int, float)):
                    # 数值：添加百分比或格式化
                    if isinstance(value, float) and 0 <= value <= 1:
                        md_content.append(f"- **{key.replace('_', ' ').title()}**: {value:.1%}\n\n")
                    else:
                        md_content.append(f"- **{key.replace('_', ' ').title()}**: {value}\n\n")
                else:
                    # 字符串
                    md_content.append(f"- **{key.replace('_', ' ').title()}**: {value}\n\n")
        else:
            md_content.append(f"- {feature_data}\n\n")


def main():
    """测试风格指南生成器"""
    # 创建生成器
    generator = StyleGuideGenerator()

    # 测试数据
    test_data = {
        "rules": [
            {
                "rule_id": "vocab-examine",
                "rule_type": "core",
                "description": "优先使用examine而非investigate",
                "frequency": 0.78,
                "examples": [
                    {
                        "before": "This study investigates...",
                        "after": "This study examines...",
                    }
                ],
            }
        ],
        "total_papers_analyzed": 50,
    }

    # 生成风格指南
    result = generator.generate_style_guide(test_data)

    print("风格指南生成结果:")
    print(f"规则数量: {len(result.get('rules', []))}")
    print(f"类别数量: {len(result.get('categories', {}))}")


if __name__ == "__main__":
    main()
