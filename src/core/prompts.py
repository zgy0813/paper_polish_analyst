"""
AI Prompt模板模块

包含所有与OpenAI API交互的prompt模板。
"""


class PromptTemplates:
    """Prompt模板类"""

    @staticmethod
    def get_individual_analysis_prompt() -> str:
        """获取单篇论文分析的prompt"""
        return """
Please analyze the writing style of the following academic paper across the following dimensions:

1. **Sentence Structure Features**:
   - Average sentence length (word count)
   - Compound sentence ratio (sentences containing and, but, or, etc.)
   - Complex sentence patterns (sentences containing because, although, which, etc.)
   - Sentence length variation

2. **Vocabulary Characteristics**:
   - Academic vocabulary density (ratio of words ending in -tion, -sion, -ment)
   - Professional terminology frequency
   - Verb tense preference (past vs present tense)
   - Top 10 most frequent words

3. **Paragraph Organization**:
   - Average paragraph length (word count)
   - Topic sentence position (usually at paragraph beginning)
   - Argumentative logic structure

4. **Academic Expression Habits**:
   - Passive voice usage rate
   - First person usage
   - Qualifier usage (very, quite, rather, etc.)


6. **Citation and Argumentation Style**:
   - Citation format preference
   - Argumentation logic patterns

Please output the analysis results in JSON format with specific statistical data:

```json
{{
  "sentence_structure": {{
    "avg_sentence_length": 0,
    "compound_sentence_ratio": 0.5,
    "complex_sentence_ratio": 0.3,
    "sentence_length_variance": 0
  }},
  "vocabulary": {{
    "academic_word_ratio": 0.5,
    "professional_terminology_frequency": 0,
    "verb_tense_preference": "past/present/mixed",
    "top_words": ["word1", "word2", ...]
  }},
  "paragraph_organization": {{
    "avg_paragraph_length": 0,
    "topic_sentence_position": "beginning/middle/mixed",
    "argument_structure": "description"
  }},
  "academic_expression": {{
    "passive_voice_ratio": 0.0,
    "first_person_usage": 0.0,
    "qualifier_usage": 0.0
  }},
  "citation_argument": {{
    "citation_format": "APA/MLA/Other",
    "argument_pattern": "description of argument pattern"
  }}
}}
```

Paper Text:
{paper_text}
"""

    @staticmethod
    def get_batch_summary_prompt() -> str:
        """获取基于并集思维的批次汇总prompt"""
        return """
Below are the individual analysis results of {paper_count} papers. Please collect ALL valuable writing patterns and style features from these papers using a "union" approach:

Analysis Requirements:
1. **Collect All Patterns**: Identify ALL writing patterns found, regardless of frequency
2. **Categorize by Frequency**: Classify patterns into frequent (60%+), common (30%-60%), and alternative (10%-30%)
3. **Document Variations**: Record different style approaches and variations
4. **Generate Comprehensive Rules**: Create rules for all discovered patterns, not just common ones
5. **Track Pattern Discovery**: Document which patterns are new vs. recurring

Please output batch summary results in JSON format:

```json
{{
  "batch_id": "batch_{batch_number}",
  "paper_count": 0,
  "pattern_collection": {{
    "frequent_patterns": {{
      "sentence_structure": {{
        "avg_sentence_length_range": [min_value, max_value],
        "avg_sentence_length_mean": average_value,
        "compound_sentence_consistency": 0.0,
        "complex_sentence_consistency": 0.0
      }},
      "vocabulary": {{
        "academic_word_consistency": 0.0,
        "common_academic_words": ["word1", "word2", ...],
        "verb_tense_consistency": 0.0
      }},
      "paragraph_organization": {{
        "avg_paragraph_length_range": [min_value, max_value],
        "topic_sentence_consistency": 0.0
      }},
      "academic_expression": {{
        "passive_voice_range": [min_value, max_value],
        "passive_voice_mean": average_value,
        "first_person_consistency": 0.0
      }}
    }},
    "common_patterns": {{
      "sentence_structure": {{}},
      "vocabulary": {{}},
      "paragraph_organization": {{}},
      "academic_expression": {{}}
    }},
    "alternative_patterns": {{
      "sentence_structure": {{}},
      "vocabulary": {{}},
      "paragraph_organization": {{}},
      "academic_expression": {{}}
    }}
  }},
  "comprehensive_rules": [
    {{
      "rule_id": "rule_id",
      "rule_type": "frequent|common|alternative",
      "category": "Sentence Structure|Vocabulary|Paragraph Organization|Academic Expression",
      "description": "rule description",
      "frequency": 0.0,
      "consistency_rate": 0.0,
      "evidence": "supporting evidence",
      "variations": ["variation1", "variation2"]
    }}
  ],
  "style_variations": {{
    "conservative_style": {{
      "characteristics": ["stable", "formal"],
      "pattern_sources": ["frequent_patterns"]
    }},
    "balanced_style": {{
      "characteristics": ["flexible", "adaptable"],
      "pattern_sources": ["frequent_patterns", "common_patterns"]
    }},
    "innovative_style": {{
      "characteristics": ["diverse", "creative"],
      "pattern_sources": ["frequent_patterns", "common_patterns", "alternative_patterns"]
    }}
  }},
  "pattern_discovery": {{
    "new_patterns": ["pattern1", "pattern2"],
    "recurring_patterns": ["pattern3", "pattern4"],
    "unique_variations": ["variation1", "variation2"]
  }},
  "legacy_format": {{
    "common_patterns": {{
      "sentence_structure": {{}},
      "vocabulary": {{}},
      "paragraph_organization": {{}},
      "academic_expression": {{}}
    }},
    "preliminary_rules": [
      {{
        "rule_id": "rule_id",
        "rule_type": "preliminary",
        "description": "rule description",
        "consistency_rate": 0.0,
        "evidence": "supporting evidence"
      }}
    ],
    "variation_analysis": {{
      "high_variation_features": ["feature1", "feature2"],
      "low_variation_features": ["feature1", "feature2"]
    }}
  }}
}}
```

Paper Analysis Results:
{individual_analyses}
"""

    @staticmethod
    def get_global_integration_prompt() -> str:
        """获取全局整合的prompt (保持向后兼容)"""
        return """
Based on the summary analysis results from all batches, please generate the final style guide, distinguishing between core rules and optional rules:

Integration Requirements:
1. **Core Rules**: Rules followed by 80% or more papers (rule_type: "core")
2. **Optional Rules**: Rules followed by 50%-80% papers (rule_type: "optional")
3. **Statistical Evidence**: Each rule must have specific statistical data support
4. **Example Collection**: Collect specific examples from the analysis
5. **Rule Priority**: Sort by adherence rate and importance

Please output the final style guide in JSON format:

```json
{{
  "style_guide_version": "1.0",
  "total_papers_analyzed": 0,
  "analysis_date": "date",
  "rules": [
    {{
      "rule_id": "vocabulary-examine-vs-investigate",
      "rule_type": "core",
      "category": "Vocabulary Choice",
      "description": "Prefer 'examine' over 'investigate'",
      "frequency": 0.78,
      "consistency_rate": 0.87,
      "examples": [
        {{
          "before": "This study investigates the impact...",
          "after": "This study examines the impact...",
          "source": "paper_23.pdf",
          "context": "when describing research objectives"
        }}
      ],
      "statistics": {{
        "examine_count": 156,
        "investigate_count": 44,
        "papers_using_examine": 78,
        "papers_using_investigate": 22
      }},
      "evidence": "Out of 100 papers, 78 prefer 'examine' while only 22 use 'investigate'"
    }}
  ],
  "summary_statistics": {{
    "core_rules_count": 0,
    "optional_rules_count": 0,
    "most_consistent_features": ["feature1", "feature2"],
    "most_variable_features": ["feature1", "feature2"]
  }}
}}
```

Batch Summary Results:
{batch_summaries}
"""

    @staticmethod
    def get_global_integration_union_prompt() -> str:
        """获取基于并集思维的全局整合prompt"""
        return """
Based on the summary analysis results from all batches, please generate a comprehensive style guide using a "union" approach that collects ALL valuable style patterns rather than filtering them out.

Integration Requirements:
1. **Collect All Patterns**: Include all style patterns found, regardless of frequency
2. **Categorize by Frequency**: Classify rules into three categories based on usage rate
3. **Track Rule Evolution**: Document how rules were discovered across different batches
4. **Identify Style Variations**: Recognize different writing style approaches
5. **Provide Choice Options**: Enable users to select from multiple style approaches

Rule Categories:
- **Frequent Rules (60%+ papers)**: High-frequency patterns, stable and reliable
- **Common Rules (30%-60% papers)**: Moderate-frequency patterns, optional applications
- **Alternative Rules (10%-30% papers)**: Lower-frequency patterns, innovative choices

Please output the comprehensive style guide in JSON format:

```json
{{
  "style_guide_version": "2.0",
  "approach": "rule_supplementation",
  "total_papers_analyzed": 0,
  "analysis_date": "date",
  "rule_categories": {{
    "frequent_rules": {{
      "threshold": "60%+",
      "count": 0,
      "description": "High-frequency patterns used by most papers",
      "rules": [
        {{
          "rule_id": "freq_001",
          "rule_type": "frequent",
          "category": "Sentence Structure",
          "description": "Use compound sentences with ratio > 0.5",
          "frequency": 0.85,
          "consistency_rate": 0.92,
          "examples": [...],
          "statistics": {{...}},
          "evidence": "85% of papers use compound sentences frequently"
        }}
      ]
    }},
    "common_rules": {{
      "threshold": "30%-60%",
      "count": 0,
      "description": "Moderate-frequency patterns for balanced writing",
      "rules": [
        {{
          "rule_id": "common_001",
          "rule_type": "common",
          "category": "Vocabulary",
          "description": "Use 'analyze' instead of 'examine' in certain contexts",
          "frequency": 0.45,
          "consistency_rate": 0.78,
          "examples": [...],
          "statistics": {{...}},
          "evidence": "45% of papers prefer 'analyze' in methodological sections"
        }}
      ]
    }},
    "alternative_rules": {{
      "threshold": "10%-30%",
      "count": 0,
      "description": "Lower-frequency patterns for innovative writing",
      "rules": [
        {{
          "rule_id": "alt_001",
          "rule_type": "alternative",
          "category": "Expression",
          "description": "Use first-person plural 'we' in collaborative research",
          "frequency": 0.25,
          "consistency_rate": 0.65,
          "examples": [...],
          "statistics": {{...}},
          "evidence": "25% of papers use 'we' when describing collaborative work"
        }}
      ]
    }}
  }},
  "rule_evolution": {{
    "batch_01": {{
      "description": "Established core baseline rules",
      "rules_count": 0,
      "new_rules_count": 0
    }},
    "batch_02": {{
      "description": "Supplemented with 5 new rules",
      "rules_count": 0,
      "new_rules_count": 0
    }}
  }},
  "style_variations": {{
    "conservative": {{
      "description": "Traditional academic style",
      "rule_sources": ["frequent_rules"],
      "characteristics": ["stable", "formal", "consistent"]
    }},
    "balanced": {{
      "description": "Moderate innovation style",
      "rule_sources": ["frequent_rules", "common_rules"],
      "characteristics": ["flexible", "adaptable", "professional"]
    }},
    "innovative": {{
      "description": "Creative academic style",
      "rule_sources": ["frequent_rules", "common_rules", "alternative_rules"],
      "characteristics": ["diverse", "creative", "expressive"]
    }}
  }},
  "summary_statistics": {{
    "total_rules_discovered": 0,
    "frequent_rules_count": 0,
    "common_rules_count": 0,
    "alternative_rules_count": 0,
    "rule_diversity_score": 0.0,
    "most_consistent_features": ["feature1", "feature2"],
    "most_variable_features": ["feature1", "feature2"]
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
