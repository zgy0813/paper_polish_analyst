"""
风格选择器模块

基于规则补充思路，为用户提供多样化的风格选择选项。
支持保守、平衡、创新三种预设风格模板。
"""

import json
from typing import Dict, List, Optional
from pathlib import Path

from config import Config

# 设置日志
from ..utils.logger_config import get_logger

logger = get_logger(__name__)


class StyleSelector:
    """风格选择器"""

    def __init__(self, style_guide: Optional[Dict] = None):
        """
        初始化风格选择器

        Args:
            style_guide: 风格指南数据，如果为None则自动加载
        """
        self.style_guide = style_guide or self._load_style_guide()
        self.rule_sets = self._build_rule_sets()

    def _load_style_guide(self) -> Dict:
        """加载风格指南"""
        try:
            style_guide_file = Path(Config.STYLE_GUIDE_JSON)
            if style_guide_file.exists():
                with open(style_guide_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                logger.warning("风格指南文件不存在，使用空指南")
                return {}
        except Exception as e:
            logger.error(f"加载风格指南失败: {str(e)}")
            return {}

    def _build_rule_sets(self) -> Dict:
        """
        构建不同风格的规则集

        Returns:
            不同风格的规则集字典
        """
        rule_sets = {
            "conservative": {
                "description": "保守风格 - 遵循高频规则，稳定可靠",
                "rule_sources": ["frequent_rules"],
                "characteristics": ["stable", "formal", "consistent"],
                "rules": [],
            },
            "balanced": {
                "description": "平衡风格 - 结合高频和常见规则，适度创新",
                "rule_sources": ["frequent_rules", "common_rules"],
                "characteristics": ["flexible", "adaptable", "professional"],
                "rules": [],
            },
            "innovative": {
                "description": "创新风格 - 包含所有规则类型，多样化选择",
                "rule_sources": ["frequent_rules", "common_rules", "alternative_rules"],
                "characteristics": ["diverse", "creative", "expressive"],
                "rules": [],
            },
        }

        # 从风格指南中提取规则
        if "rule_categories" in self.style_guide:
            categories = self.style_guide["rule_categories"]

            # 保守风格：只使用高频规则
            if "frequent_rules" in categories:
                rule_sets["conservative"]["rules"] = categories["frequent_rules"].get(
                    "rules", []
                )

            # 平衡风格：使用高频+常见规则
            balanced_rules = []
            if "frequent_rules" in categories:
                balanced_rules.extend(categories["frequent_rules"].get("rules", []))
            if "common_rules" in categories:
                balanced_rules.extend(categories["common_rules"].get("rules", []))
            rule_sets["balanced"]["rules"] = balanced_rules

            # 创新风格：使用所有规则
            innovative_rules = []
            for category_name in [
                "frequent_rules",
                "common_rules",
                "alternative_rules",
            ]:
                if category_name in categories:
                    innovative_rules.extend(categories[category_name].get("rules", []))
            rule_sets["innovative"]["rules"] = innovative_rules

        return rule_sets

    def get_available_styles(self) -> List[str]:
        """
        获取可用的风格选项

        Returns:
            可用风格列表
        """
        return list(self.rule_sets.keys())

    def get_style_info(self, style: str) -> Dict:
        """
        获取指定风格的详细信息

        Args:
            style: 风格名称

        Returns:
            风格信息字典
        """
        if style not in self.rule_sets:
            return {"error": f"未知风格: {style}"}

        return self.rule_sets[style]

    def get_rules_for_style(self, style: str) -> List[Dict]:
        """
        获取指定风格的规则列表

        Args:
            style: 风格名称

        Returns:
            规则列表
        """
        if style not in self.rule_sets:
            return []

        return self.rule_sets[style]["rules"]

    def get_rules_by_category(self, style: str, category: str) -> List[Dict]:
        """
        获取指定风格和类别的规则

        Args:
            style: 风格名称
            category: 规则类别 (Sentence Structure, Vocabulary, etc.)

        Returns:
            指定类别的规则列表
        """
        rules = self.get_rules_for_style(style)
        return [rule for rule in rules if rule.get("category", "") == category]

    def recommend_style(self, paper_features: Dict) -> str:
        """
        基于论文特征推荐合适的风格

        Args:
            paper_features: 论文特征字典

        Returns:
            推荐的风格名称
        """
        try:
            # 分析论文特征
            complexity_score = paper_features.get("sentence_complexity", 0.5)
            academic_level = paper_features.get("academic_level", 0.5)
            innovation_need = paper_features.get("innovation_need", 0.5)

            # 推荐逻辑
            if academic_level > 0.8 and complexity_score > 0.7:
                # 高学术水平 + 高复杂度 -> 保守风格
                return "conservative"
            elif innovation_need > 0.7 or academic_level < 0.4:
                # 高创新需求 或 低学术水平 -> 创新风格
                return "innovative"
            else:
                # 其他情况 -> 平衡风格
                return "balanced"

        except Exception as e:
            logger.error(f"风格推荐失败: {str(e)}")
            return "balanced"  # 默认返回平衡风格

    def analyze_paper_features(self, paper_text: str) -> Dict:
        """
        分析论文特征

        Args:
            paper_text: 论文文本

        Returns:
            论文特征字典
        """
        try:
            # 简单的特征分析（可以后续扩展为更复杂的NLP分析）
            features = {
                "sentence_complexity": self._calculate_sentence_complexity(paper_text),
                "academic_level": self._calculate_academic_level(paper_text),
                "innovation_need": self._calculate_innovation_need(paper_text),
                "text_length": len(paper_text),
                "word_count": len(paper_text.split()),
            }

            return features

        except Exception as e:
            logger.error(f"论文特征分析失败: {str(e)}")
            return {
                "sentence_complexity": 0.5,
                "academic_level": 0.5,
                "innovation_need": 0.5,
                "text_length": len(paper_text),
                "word_count": len(paper_text.split()),
            }

    def _calculate_sentence_complexity(self, text: str) -> float:
        """计算句式复杂度"""
        sentences = text.split(".")
        if not sentences:
            return 0.5

        # 简单的复杂度计算：平均句长
        avg_length = sum(len(s.split()) for s in sentences) / len(sentences)

        # 归一化到0-1范围
        if avg_length < 10:
            return 0.2
        elif avg_length < 20:
            return 0.5
        else:
            return 0.8

    def _calculate_academic_level(self, text: str) -> float:
        """计算学术水平"""
        academic_words = [
            "research",
            "study",
            "analysis",
            "methodology",
            "hypothesis",
            "theoretical",
            "empirical",
            "framework",
            "model",
            "approach",
        ]

        text_lower = text.lower()
        academic_count = sum(1 for word in academic_words if word in text_lower)

        # 归一化到0-1范围
        return min(academic_count / 10, 1.0)

    def _calculate_innovation_need(self, text: str) -> float:
        """计算创新需求"""
        innovation_words = [
            "novel",
            "innovative",
            "creative",
            "unique",
            "original",
            "breakthrough",
            "pioneering",
            "cutting-edge",
            "state-of-the-art",
        ]

        text_lower = text.lower()
        innovation_count = sum(1 for word in innovation_words if word in text_lower)

        # 归一化到0-1范围
        return min(innovation_count / 5, 1.0)

    def get_style_comparison(self) -> Dict:
        """
        获取不同风格的对比信息

        Returns:
            风格对比字典
        """
        comparison = {}

        for style, info in self.rule_sets.items():
            comparison[style] = {
                "description": info["description"],
                "rule_count": len(info["rules"]),
                "characteristics": info["characteristics"],
                "rule_sources": info["rule_sources"],
            }

        return comparison

    def filter_rules_by_focus(self, style: str, focus: str) -> List[Dict]:
        """
        根据润色焦点过滤规则

        Args:
            style: 风格名称
            focus: 润色焦点 (sentence_structure, vocabulary, paragraph_organization, academic_expression)

        Returns:
            过滤后的规则列表
        """
        rules = self.get_rules_for_style(style)

        # 焦点映射
        focus_mapping = {
            "sentence_structure": "Sentence Structure",
            "vocabulary": "Vocabulary",
            "paragraph_organization": "Paragraph Organization",
            "academic_expression": "Academic Expression",
        }

        target_category = focus_mapping.get(focus, focus)
        return [rule for rule in rules if rule.get("category", "") == target_category]

    def get_rule_statistics(self) -> Dict:
        """
        获取规则统计信息

        Returns:
            规则统计字典
        """
        stats = {
            "total_rules": 0,
            "by_style": {},
            "by_category": {},
            "by_frequency": {},
        }

        # 按风格统计
        for style, info in self.rule_sets.items():
            rule_count = len(info["rules"])
            stats["by_style"][style] = rule_count
            stats["total_rules"] += rule_count

        # 按类别统计
        all_rules = []
        for info in self.rule_sets.values():
            all_rules.extend(info["rules"])

        for rule in all_rules:
            category = rule.get("category", "Unknown")
            if category not in stats["by_category"]:
                stats["by_category"][category] = 0
            stats["by_category"][category] += 1

        # 按频率统计
        if "rule_categories" in self.style_guide:
            for category_name, category_data in self.style_guide[
                "rule_categories"
            ].items():
                if isinstance(category_data, dict) and "count" in category_data:
                    stats["by_frequency"][category_name] = category_data["count"]

        return stats


def main():
    """测试风格选择器功能"""
    # 创建风格选择器
    selector = StyleSelector()

    # 测试基本功能
    print("可用风格:", selector.get_available_styles())

    # 测试风格信息
    for style in selector.get_available_styles():
        info = selector.get_style_info(style)
        print(f"\n{style}:")
        print(f"  描述: {info['description']}")
        print(f"  规则数量: {len(info['rules'])}")
        print(f"  特征: {', '.join(info['characteristics'])}")

    # 测试规则统计
    stats = selector.get_rule_statistics()
    print(f"\n规则统计:")
    print(f"  总规则数: {stats['total_rules']}")
    print(f"  按风格: {stats['by_style']}")
    print(f"  按类别: {stats['by_category']}")


if __name__ == "__main__":
    main()
