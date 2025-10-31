"""
写作维度映射工具

提供统一的规则描述到8大历史期刊写作维度的映射，确保分析、生成和前端模块使用一致的分类结果。
"""

from __future__ import annotations

from typing import Dict, Iterable

# 8大写作维度的显示名称
DIMENSION_LABELS = [
    "Narrative Strategies",
    "Argumentation Patterns",
    "Rhetorical Devices",
    "Rhythm & Flow",
    "Voice & Tone",
    "Terminology Management",
    "Section Patterns",
    "Citation Artistry",
]

# 将旧版类别或常见别名映射到新版维度
LEGACY_CATEGORY_MAPPING: Dict[str, str] = {
    "叙事策略": "Narrative Strategies",
    "论证模式": "Argumentation Patterns",
    "修辞手法": "Rhetorical Devices",
    "节奏流畅度": "Rhythm & Flow",
    "语态语气": "Voice & Tone",
    "术语管理": "Terminology Management",
    "章节模式": "Section Patterns",
    "引用艺术": "Citation Artistry",
    "sentence structure": "Rhythm & Flow",
    "句式结构": "Rhythm & Flow",
    "paragraph organization": "Section Patterns",
    "段落组织": "Section Patterns",
    "段落衔接": "Rhythm & Flow",
    "vocabulary": "Terminology Management",
    "词汇选择": "Terminology Management",
    "academic expression": "Voice & Tone",
    "学术表达": "Voice & Tone",
    "transitions": "Rhythm & Flow",
    "flow": "Rhythm & Flow",
    "引用论证": "Citation Artistry",
    "citation": "Citation Artistry",
    "references": "Citation Artistry",
    "逻辑论证": "Argumentation Patterns",
    "general": "General Patterns",
    "general rules": "General Patterns",
    "general patterns": "General Patterns",
    "其他": "General Patterns",
}

# 针对新版维度的关键词特征，用于启发式打分
DIMENSION_KEYWORDS: Dict[str, Iterable[str]] = {
    "Narrative Strategies": [
        "narrative",
        "story",
        "opening",
        "hook",
        "arc",
        "context",
        "plot",
        "motivate",
        "背景",
        "叙事",
        "引入",
        "故事",
    ],
    "Argumentation Patterns": [
        "argument",
        "logic",
        "reasoning",
        "evidence",
        "claim",
        "hypothesis",
        "theor",
        "论证",
        "推理",
        "假设",
        "证据",
    ],
    "Rhetorical Devices": [
        "rhetoric",
        "metaphor",
        "analogy",
        "contrast",
        "emphasis",
        "parallel",
        "hedge",
        "强化",
        "修辞",
        "强调",
    ],
    "Rhythm & Flow": [
        "sentence",
        "length",
        "structure",
        "transition",
        "cohesion",
        "flow",
        "节奏",
        "过渡",
        "衔接",
        "句式",
    ],
    "Voice & Tone": [
        "voice",
        "tone",
        "first person",
        "we ",
        "our ",
        "assertive",
        "confidence",
        "态度",
        "语态",
        "语气",
    ],
    "Terminology Management": [
        "terminology",
        "term",
        "definition",
        "define",
        "jargon",
        "glossary",
        "术语",
        "定义",
        "名词",
    ],
    "Section Patterns": [
        "section",
        "introduction",
        "methods",
        "results",
        "discussion",
        "paragraph",
        "章节",
        "段落",
        "结构",
    ],
    "Citation Artistry": [
        "cite",
        "citation",
        "reference",
        "et al",
        "footnote",
        "bibliography",
        "引用",
        "文献",
        "参考",
    ],
}

DEFAULT_DIMENSION = "General Patterns"


def normalize_dimension_label(label: str) -> str:
    """
    将输入的类别名称规整到8大维度之一。

    Args:
        label: 原始类别名称（可能是旧版名称或中英文混合）

    Returns:
        统一后的类别名称
    """
    if not label:
        return DEFAULT_DIMENSION

    label_clean = label.strip()
    label_lower = label_clean.lower()

    # 已经是标准维度
    if label_clean in DIMENSION_LABELS:
        return label_clean

    if label_lower in LEGACY_CATEGORY_MAPPING:
        return LEGACY_CATEGORY_MAPPING[label_lower]

    # 若输入本身就是新版维度但大小写不同
    for dim in DIMENSION_LABELS:
        if label_lower == dim.lower():
            return dim

    return label_clean or DEFAULT_DIMENSION


def map_rule_to_dimension(description: str) -> str:
    """
    根据规则描述映射到8大写作维度。

    Args:
        description: 规则描述文本

    Returns:
        维度名称
    """
    if not description:
        return DEFAULT_DIMENSION

    text = description.lower()

    # 先处理旧版类别或显式关键词
    for legacy_phrase, dimension in LEGACY_CATEGORY_MAPPING.items():
        if legacy_phrase in text:
            return dimension

    # 计算各维度关键词命中次数
    best_dimension = DEFAULT_DIMENSION
    best_score = 0

    for dimension, keywords in DIMENSION_KEYWORDS.items():
        score = sum(text.count(keyword.lower()) for keyword in keywords)
        if score > best_score:
            best_score = score
            best_dimension = dimension

    return best_dimension
