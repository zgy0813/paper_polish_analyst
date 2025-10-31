"""
AI Prompt模板模块

包含所有与OpenAI API交互的prompt模板。
"""


class PromptTemplates:
    """Prompt模板类"""

    @staticmethod
    def get_global_integration_union_prompt() -> str:
        """获取基于并集思维的全局整合prompt（8大维度版本）"""
        return """
Based on the batch summary analysis results from all batches, please generate a comprehensive global style guide integrating patterns across 8 dimensions using a "union" approach.

Integration Requirements:
1. **Collect All Patterns**: Include ALL style patterns found across all batches, regardless of frequency
2. **Categorize by Frequency**: Classify patterns into three categories based on usage rate across all batches
3. **Calculate Cross-Batch Statistics**: Aggregate frequencies from all batches to determine global frequencies
4. **Preserve Examples**: Include representative examples from different batches

Pattern Categories:
- **Frequent Patterns (50%+ papers)**: High-frequency patterns, stable and reliable
- **Common Patterns (25%-50% papers)**: Moderate-frequency patterns, optional applications
- **Alternative Patterns (<25% papers)**: Lower-frequency patterns, innovative choices

Please output the comprehensive global style guide in JSON format:

```json
{{
  "style_guide_version": "3.0",
  "approach": "union_based_8dimensions",
  "total_batches": 0,
  "total_papers_analyzed": 0,
  "analysis_date": "date",
  "narrative_strategies": {{
    "frequent_patterns": [
      {{
        "pattern": "gap-based opening",
        "global_frequency": 0.85,
        "description": "Open papers by identifying literature gaps",
        "examples": [...],
        "batching_appears_in": ["batch_01", "batch_02"]
      }}
    ],
    "common_patterns": [...],
    "alternative_patterns": [...]
  }},
  "argumentation_patterns": {{
    "frequent_patterns": [...],
    "common_patterns": [...],
    "alternative_patterns": [...]
  }},
  "rhetorical_devices": {{
    "frequent_patterns": [...],
    "common_patterns": [...],
    "alternative_patterns": [...]
  }},
  "rhythm_flow": {{
    "frequent_patterns": [...],
    "common_patterns": [...],
    "alternative_patterns": [...]
  }},
  "voice_tone": {{
    "frequent_patterns": [...],
    "common_patterns": [...],
    "alternative_patterns": [...]
  }},
  "terminology_management": {{
    "frequent_patterns": [...],
    "common_patterns": [...],
    "alternative_patterns": [...]
  }},
  "section_patterns": {{
    "frequent_patterns": [...],
    "common_patterns": [...],
    "alternative_patterns": [...]
  }},
  "citation_artistry": {{
    "frequent_patterns": [...],
    "common_patterns": [...],
    "alternative_patterns": [...]
  }},
  "summary_statistics": {{
    "total_patterns_discovered": 0,
    "frequent_patterns_count": 0,
    "common_patterns_count": 0,
    "alternative_patterns_count": 0,
    "most_consistent_dimensions": ["dimension1", "dimension2"],
    "most_variable_dimensions": ["dimension1", "dimension2"]
  }},
  "style_variations": {{
    "conservative": {{
      "description": "Traditional academic style",
      "pattern_sources": ["frequent_patterns from all dimensions"],
      "characteristics": ["stable", "formal", "consistent"]
    }},
    "balanced": {{
      "description": "Moderate innovation style",
      "pattern_sources": ["frequent_patterns", "common_patterns from all dimensions"],
      "characteristics": ["flexible", "adaptable", "professional"]
    }},
    "innovative": {{
      "description": "Creative academic style",
      "pattern_sources": ["all patterns from all dimensions"],
      "characteristics": ["diverse", "creative", "expressive"]
    }}
  }}
}}
```

Batch Summary Results:
{batch_summaries}
"""

    @staticmethod
    def get_sentence_structure_polish_prompt() -> str:
        """获取句式结构润色的prompt"""
        return """
Based on the following style rules, adjust the sentence structure of the user's paper (Round 1 polishing):

Polishing Requirements:
1. **Only adjust sentence structure**: Do not change vocabulary or paragraph organization
2. **Apply relevant rules**: Make adjustments based on sentence structure rules in the style guide
3. **Maintain original meaning**: Ensure the meaning remains unchanged after modification
4. **Provide modification rationale**: Explain the basis for each modification

Please output modification suggestions in JSON format:

```json
{{
  "round": 1,
  "focus": "Sentence Structure Adjustment",
  "modifications": [
    {{
      "modification_id": "sent_001",
      "original_text": "Original sentence",
      "modified_text": "Modified sentence",
      "position": "Paragraph X, Sentence Y",
      "reason": "Modification rationale",
      "rule_applied": "Rule ID",
      "rule_evidence": "Rule evidence"
    }}
  ],
  "summary": {{
    "total_modifications": 0,
    "rules_applied": ["Rule ID1", "Rule ID2"],
    "improvement_description": "Improvement description"
  }}
}}
```

Style Rules:
{style_rules}

User's Paper:
{paper_text}
"""

    @staticmethod
    def get_vocabulary_polish_prompt() -> str:
        """获取词汇优化的prompt"""
        return """
Based on the following style rules, optimize the vocabulary of the user's paper (Round 2 polishing):

Polishing Requirements:
1. **Only perform vocabulary replacement**: Do not change sentence structure or paragraph organization
2. **Apply vocabulary rules**: Make replacements based on vocabulary rules in the style guide
3. **Maintain academic tone**: Ensure replacements maintain the formality of academic writing
4. **Provide replacement rationale**: Explain the reason for each vocabulary replacement

Please output modification suggestions in JSON format:

```json
{{
  "round": 2,
  "focus": "Vocabulary Optimization",
  "modifications": [
    {{
      "modification_id": "vocab_001",
      "original_text": "Sentence containing original vocabulary",
      "modified_text": "Sentence containing new vocabulary",
      "position": "Paragraph X, Sentence Y",
      "word_changed": "original word → new word",
      "reason": "Replacement rationale",
      "rule_applied": "Rule ID",
      "rule_evidence": "Rule evidence and statistics"
    }}
  ],
  "summary": {{
    "total_modifications": 0,
    "words_replaced": ["word1", "word2"],
    "rules_applied": ["Rule ID1", "Rule ID2"]
  }}
}}
```

Style Rules:
{style_rules}

User's Paper (after Round 2 modifications):
{paper_text}
"""

    @staticmethod
    def get_transition_polish_prompt() -> str:
        """获取段落衔接润色的prompt"""
        return """
You are an expert academic writing editor specializing in paragraph coherence and transitions. Your task is to improve the flow and connectivity between paragraphs and sentences in the provided academic paper.

Focus Areas:
1. **Paragraph Transitions**: Improve connections between paragraphs
2. **Sentence Flow**: Enhance logical flow within paragraphs
3. **Coherence Markers**: Add or improve transitional phrases and words
4. **Logical Structure**: Ensure clear progression of ideas

Polishing Requirements:
1. **Only improve transitions and coherence**: Do not change sentence structure or vocabulary
2. **Apply transition rules**: Make improvements based on coherence rules in the style guide
3. **Maintain academic tone**: Ensure transitions maintain the formality of academic writing
4. **Provide improvement rationale**: Explain the reason for each transition improvement

Please output modification suggestions in JSON format:

```json
{{
  "round": 3,
  "focus": "Transition and Coherence Improvement",
  "modifications": [
    {{
      "modification_id": "trans_001",
      "original_text": "Sentence or paragraph with poor transition",
      "modified_text": "Sentence or paragraph with improved transition",
      "position": "Paragraph X, Sentence Y",
      "transition_added": "transitional phrase or word",
      "reason": "Improvement rationale",
      "rule_applied": "Rule ID",
      "rule_evidence": "Rule evidence and statistics"
    }}
  ],
  "summary": {{
    "total_modifications": 0,
    "transitions_added": ["transition1", "transition2"],
    "rules_applied": ["Rule ID1", "Rule ID2"]
  }}
}}
```

Style Rules:
{style_rules}

User's Paper (after Round 2 modifications):
{paper_text}
"""

    @staticmethod
    def get_comprehensive_polish_prompt() -> str:
        """获取综合润色的prompt（一次性完成句式、词汇、段落润色）"""
        return """
You are an expert academic writing editor. Your task is to comprehensively polish the provided academic paper in one pass, addressing three key areas simultaneously:

**Comprehensive Polishing Requirements:**

1. **Sentence Structure Adjustment**:
   - Improve sentence clarity and flow
   - Adjust sentence length and complexity
   - Enhance grammatical structure
   - Apply sentence structure rules from the style guide

2. **Vocabulary Optimization**:
   - Replace informal or imprecise words with academic vocabulary
   - Ensure consistent terminology usage
   - Improve word choice for clarity and precision
   - Apply vocabulary rules from the style guide

3. **Transition and Coherence Improvement**:
   - Enhance paragraph transitions
   - Improve logical flow between sentences
   - Add or improve transitional phrases
   - Strengthen overall coherence

**Important Guidelines:**
- Make all three types of improvements in one comprehensive pass
- Maintain the original meaning and academic tone
- Apply relevant rules from the provided style guide
- Provide clear rationale for each modification
- Ensure modifications work together harmoniously

Please output comprehensive modification suggestions in JSON format:

```json
{{
  "sentence_structure": {{
    "modifications": [
      {{
        "modification_id": "sent_001",
        "original_text": "Original sentence",
        "modified_text": "Improved sentence",
        "position": "Paragraph X, Sentence Y",
        "reason": "Sentence structure improvement rationale",
        "rule_applied": "Rule ID",
        "rule_evidence": "Rule evidence"
      }}
    ],
    "summary": {{
      "total_modifications": 0,
      "rules_applied": ["Rule ID1", "Rule ID2"],
      "improvement_description": "Overall sentence structure improvements"
    }}
  }},
  "vocabulary": {{
    "modifications": [
      {{
        "modification_id": "vocab_001",
        "original_text": "Sentence with original vocabulary",
        "modified_text": "Sentence with improved vocabulary",
        "position": "Paragraph X, Sentence Y",
        "word_changed": "original word → improved word",
        "reason": "Vocabulary improvement rationale",
        "rule_applied": "Rule ID",
        "rule_evidence": "Rule evidence"
      }}
    ],
    "summary": {{
      "total_modifications": 0,
      "words_replaced": ["word1", "word2"],
      "rules_applied": ["Rule ID1", "Rule ID2"]
    }}
  }},
  "transitions": {{
    "modifications": [
      {{
        "modification_id": "trans_001",
        "original_text": "Sentence with poor transition",
        "modified_text": "Sentence with improved transition",
        "position": "Paragraph X, Sentence Y",
        "transition_added": "transitional phrase",
        "reason": "Transition improvement rationale",
        "rule_applied": "Rule ID",
        "rule_evidence": "Rule evidence"
      }}
    ],
    "summary": {{
      "total_modifications": 0,
      "transitions_added": ["transition1", "transition2"],
      "rules_applied": ["Rule ID1", "Rule ID2"]
    }}
  }},
  "overall_summary": {{
    "total_modifications": 0,
    "categories_improved": ["sentence_structure", "vocabulary", "transitions"],
    "rules_applied": ["Rule ID1", "Rule ID2", "Rule ID3"],
    "overall_improvement": "Comprehensive description of all improvements made"
  }}
}}
```

Style Rules:
{style_rules}

User's Paper:
{paper_text}
"""

    @staticmethod
    def get_quality_assessment_prompt() -> str:
        """获取质量评估的prompt"""
        return """
Please evaluate the academic writing quality of the following paper across three dimensions:

Evaluation Dimensions:
1. **Academic Standard** (0-100 points):
   - Adherence to academic writing standards
   - Citation format, terminology usage, formality

2. **Readability** (0-100 points):
   - Appropriate sentence complexity
   - Clear logic and fluent expression
   - Appropriate vocabulary usage

3. **Overall Quality** (0-100 points):
   - Overall paper quality
   - Content organization rationality

Please output the evaluation results in JSON format:

```json
{{
  "assessment": {{
    "academic_standard": {{
      "score": 0,
      "description": "Evaluation description",
      "strengths": ["strength1", "strength2"],
      "weaknesses": ["weakness1", "weakness2"]
    }},
    "readability": {{
      "score": 0,
      "description": "Evaluation description",
      "sentence_complexity": "simple/moderate/complex",
      "logical_flow": "clear/moderate/confusing"
    }},
    "overall_quality": {{
      "score": 0,
      "description": "Overall evaluation",
      "recommendations": ["recommendation1", "recommendation2"]
    }}
  }},
  "detailed_analysis": {{
    "sentence_analysis": "Sentence analysis",
    "vocabulary_analysis": "Vocabulary analysis",
    "structure_analysis": "Structure analysis"
  }}
}}
```

Paper Text:
{paper_text}
"""

    @staticmethod
    def get_simple_polish_prompt() -> str:
        """获取简洁润色提示词（只返回润色后的文本）"""
        return """
You are an expert academic writing editor. Please polish the following paper according to the provided style guide rules.

**Style Rules to Apply:**
{style_rules}

**Requirements:**
- Apply the style guide rules to improve the paper
- Focus on sentence structure, vocabulary, and transitions
- Maintain the original meaning and academic tone
- Ensure proper academic writing standards

**Important:** Return ONLY the polished text. Do not include any explanations, modifications list, or JSON format. Just return the complete polished version of the paper.

Paper to polish:
{paper_text}
"""

    @staticmethod
    def get_official_guide_parsing_prompt() -> str:
        """获取官方指南解析的prompt"""
        return """
Please extract specific writing rules and guidelines from the following official journal style guide:

Extraction Requirements:
1. **Identify Specific Rules**: Extract clear writing standards, formatting requirements, and language usage rules
2. **Categorize Rules**: Classify rules into the following categories:
   - Format Guidelines
   - Sentence Structure
   - Vocabulary Choice
   - Citation Format
   - Paragraph Organization
   - Academic Expression
   - Other

3. **Extract Examples**: Provide specific correct and incorrect examples for each rule
4. **Determine Priority**: Judge rule importance based on wording (must/should/may)
5. **Record Sources**: Note the section or page number in the document

Please output the parsing results in JSON format:

```json
{{
  "rules": [
    {{
      "rule_id": "format-title-case",
      "category": "Format Guidelines",
      "description": "Use title case for headings",
      "priority": "highest",
      "requirements": ["Capitalize first letter", "Capitalize important words"],
      "prohibitions": ["All caps", "All lowercase"],
      "examples": [
        {{
          "correct": "The Impact of Climate Change on Agriculture",
          "incorrect": "the impact of climate change on agriculture",
          "explanation": "Important words in titles should be capitalized"
        }}
      ],
      "context": "Paper title format requirements",
      "section": "Title Format",
      "page_reference": "Page 3",
      "confidence": 0.9
    }}
  ],
  "summary": {{
    "total_rules": 0,
    "categories": {{
      "Format Guidelines": 0,
      "Sentence Structure": 0,
      "Vocabulary Choice": 0
    }},
    "priority_distribution": {{
      "highest": 0,
      "high": 0,
      "medium": 0
    }}
  }}
}}
```

Official Style Guide Content:
{style_guide_text}
"""

    @staticmethod
    def get_style_features_analysis_prompt() -> str:
        """风格特征深度分析Prompt"""
        return """
Analyze the writing style features of the following academic paper across 8 dimensions:

1. **Narrative Strategies**:
   - Opening strategy (story/statistics/paradox/literature gap)
   - Story arc (problem → discovery narrative rhythm)
   - Evidence presentation style (quantitative vs qualitative balance)

2. **Argumentation Patterns**:
   - Theory building approach (inductive vs deductive)
   - Counterargument handling (anticipation of objections)
   - Logic connectives usage (therefore, however, moreover)

3. **Rhetorical Devices**:
   - Emphasis techniques (repetition, rhetorical questions)
   - Hedging vs boosting (may/suggest vs clearly/substantial)
   - Metaphors and analogies usage

4. **Rhythm & Flow**:
   - Sentence variety (length variation, structure diversity)
   - Paragraph transitions (bridging techniques)
   - Reading pace (information density variation)

5. **Voice & Tone**:
   - Author presence ("we" usage scenarios)
   - Confidence level (assertive vs exploratory)
   - Engagement style (dialogue with readers)

6. **Terminology Management**:
   - Field-specific language density
   - Accessibility balance (technical vs accessible)
   - Conceptual clarity (definition methods)

7. **Section-Specific Patterns**:
   - Introduction style (problem statement positioning)
   - Theory section style (hypothesis presentation)
   - Methods transparency (detail level)
   - Discussion depth (contribution layers)

8. **Citation Integration Artistry**:
   - Citation density patterns across sections
   - Citation functions (supportive vs contrastive)
   - Integration smoothness (flow disruption)

Output in JSON format:
```json
{{
  "narrative_strategies": {{
    "opening_strategy": "story/statistics/paradox/gap",
    "story_arc": "description of narrative flow",
    "evidence_presentation": "quantitative/qualitative/mixed"
  }},
  "argumentation_patterns": {{
    "theory_building": "inductive/deductive",
    "counterargument_handling": "description",
    "logic_connectives": {{"causal": 5, "contrast": 3, "addition": 8}}
  }},
  "rhetorical_devices": {{
    "emphasis_techniques": "description",
    "hedging_ratio": 0.0,
    "boosting_ratio": 0.0
  }},
  "rhythm_flow": {{
    "sentence_variety": "high/moderate/low",
    "paragraph_transitions": "description",
    "reading_pace": "fast/moderate/slow"
  }},
  "voice_tone": {{
    "author_presence": "strong/moderate/weak",
    "confidence_level": "assertive/exploratory",
    "engagement_style": "description"
  }},
  "terminology_management": {{
    "field_language_density": 0.0,
    "accessibility_balance": "description",
    "conceptual_clarity": "description"
  }},
  "section_patterns": {{
    "introduction": "description",
    "theory": "description",
    "methods": "description",
    "discussion": "description"
  }},
  "citation_artistry": {{
    "citation_density": 0.0,
    "citation_functions": "description",
    "integration_smoothness": "description"
  }}
}}
```

Paper Text:
{paper_text}
"""

    @staticmethod
    def get_style_features_batch_summary_prompt() -> str:
        """风格特征批次汇总Prompt"""
        return """
Based on papers' style feature analysis, summarize the common patterns across 8 dimensions.

Requirements:
1. **Dominant Patterns** (50%+ papers): Most common approaches
2. **Alternative Patterns** (25%-50%): Less common but valid approaches
3. **Variations**: Different implementations of the same pattern
4. **Examples**: Specific examples from the papers

Output summary in JSON format:
```json
{{
  "narrative_strategies": {{
    "dominant_patterns": ["pattern1", "pattern2"],
    "alternative_patterns": ["pattern3"],
    "frequency": {{"pattern1": 0.75, "pattern2": 0.65}},
    "examples": [
      {{"pattern": "pattern1", "example": "specific example from paper"}}
    ]
  }},
  "argumentation_patterns": {{...}},
  "rhetorical_devices": {{...}},
  "rhythm_flow": {{...}},
  "voice_tone": {{...}},
  "terminology_management": {{...}},
  "section_patterns": {{...}},
  "citation_artistry": {{...}}
}}
```

Individual Analysis Results:
{individual_analyses}
"""

    @classmethod
    def format_prompt(cls, template: str, **kwargs) -> str:
        """
        格式化prompt模板

        Args:
            template: prompt模板
            **kwargs: 格式化参数

        Returns:
            格式化后的prompt
        """
        try:
            return template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing required parameter for prompt: {e}")


def main():
    """测试prompt模板"""
    prompts = PromptTemplates()

    # 测试单篇分析prompt
    test_text = "This is a test paper content..."
    individual_prompt = prompts.format_prompt(
        prompts.get_individual_analysis_prompt(), paper_text=test_text
    )

    print("Individual Analysis Prompt:")
    print(individual_prompt[:200] + "...")


if __name__ == "__main__":
    main()
