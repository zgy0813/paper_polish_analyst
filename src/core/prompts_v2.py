"""
AI Prompt模板模块 - 版本2.0

保留旧版prompt模板以供参考
"""

class PromptTemplatesV2:
    """Prompt模板类 - 版本2.0 (旧版)"""

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
2. **Categorize by Frequency**: Classify patterns into frequent (50%+), common (25%-50%), and alternative (10%-25%)
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
        """获取基于并集思维的全局整合prompt - 版本2.0"""
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

