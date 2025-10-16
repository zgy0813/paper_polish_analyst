"""
NLP工具函数模块

提供文本分析、统计指标计算、相似度计算等NLP功能。
"""

import re
from typing import List, Dict, Tuple
from collections import Counter
import spacy
from spacy.lang.en.stop_words import STOP_WORDS as SPACY_STOP_WORDS
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


class NLPUtils:
    """NLP工具类"""

    def __init__(self):
        """初始化NLP工具"""
        # Load spaCy with en_core_web_md model
        try:
            self.nlp = spacy.load("en_core_web_md")
            self.stop_words = SPACY_STOP_WORDS
            self.backend = "spacy"
            print("Using spaCy backend with en_core_web_md model")
        except OSError as e:
            raise RuntimeError(
                f"spaCy model 'en_core_web_md' not found. Please install it with: python -m spacy download en_core_web_md"
            ) from e

        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words="english")

    def _tokenize_text(self, text: str) -> List[str]:
        """Tokenize text using spaCy"""
        doc = self.nlp(text)
        return [
            token.text
            for token in doc
            if token.is_alpha and token.text.lower() not in self.stop_words
        ]

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences using spaCy"""
        doc = self.nlp(text)
        return [sent.text.strip() for sent in doc.sents]

    def analyze_sentence_structure(self, text: str) -> Dict:
        """
        分析句式结构

        Args:
            text: 输入文本

        Returns:
            句式结构分析结果
        """
        sentences = self._split_sentences(text)

        if not sentences:
            return {}

        # 计算句子长度统计
        sentence_lengths = []
        for sent in sentences:
            # Use spaCy for more accurate tokenization
            doc = self.nlp(sent)
            sentence_lengths.append(len([token for token in doc if token.is_alpha]))

        # 识别复合句（包含连接词的句子）
        compound_sentences = 0
        for sent in sentences:
            if any(
                connector in sent.lower()
                for connector in ["and", "but", "or", "so", "yet", "for", "nor"]
            ):
                compound_sentences += 1

        # 识别从句（包含关系代词或从属连词）
        complex_sentences = 0
        subordinating_conjunctions = [
            "because",
            "although",
            "while",
            "since",
            "if",
            "when",
            "where",
            "which",
            "that",
            "who",
        ]
        for sent in sentences:
            if any(conj in sent.lower() for conj in subordinating_conjunctions):
                complex_sentences += 1

        return {
            "total_sentences": len(sentences),
            "avg_sentence_length": (
                sum(sentence_lengths) / len(sentence_lengths) if sentence_lengths else 0
            ),
            "sentence_length_variance": (
                np.var(sentence_lengths) if sentence_lengths else 0
            ),
            "compound_sentence_ratio": (
                compound_sentences / len(sentences) if sentences else 0
            ),
            "complex_sentence_ratio": (
                complex_sentences / len(sentences) if sentences else 0
            ),
            "max_sentence_length": max(sentence_lengths) if sentence_lengths else 0,
            "min_sentence_length": min(sentence_lengths) if sentence_lengths else 0,
        }

    def analyze_vocabulary(self, text: str) -> Dict:
        """
        分析词汇特点

        Args:
            text: 输入文本

        Returns:
            词汇分析结果
        """
        words = self._tokenize_text(text)

        if not words:
            return {}

        word_counts = Counter(words)

        # 学术词汇检测（简单的启发式规则）
        academic_words = self._identify_academic_words(words)

        # 动词时态分析
        tense_analysis = self._analyze_verb_tenses(words)

        return {
            "total_words": len(words),
            "unique_words": len(word_counts),
            "vocabulary_richness": len(word_counts) / len(words) if words else 0,
            "academic_word_ratio": len(academic_words) / len(words) if words else 0,
            "most_common_words": dict(word_counts.most_common(10)),
            "verb_tense_analysis": tense_analysis,
            "avg_word_length": (
                sum(len(word) for word in words) / len(words) if words else 0
            ),
        }

    def analyze_paragraph_structure(self, text: str) -> Dict:
        """
        分析段落结构

        Args:
            text: 输入文本

        Returns:
            段落结构分析结果
        """
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        if not paragraphs:
            return {}

        # 计算段落长度
        paragraph_lengths = []
        for para in paragraphs:
            # Use spaCy for more accurate tokenization
            doc = self.nlp(para)
            paragraph_lengths.append(len([token for token in doc if token.is_alpha]))

        # 分析主题句位置（段落第一句的特征）
        topic_sentence_analysis = self._analyze_topic_sentences(paragraphs)

        return {
            "total_paragraphs": len(paragraphs),
            "avg_paragraph_length": (
                sum(paragraph_lengths) / len(paragraph_lengths)
                if paragraph_lengths
                else 0
            ),
            "paragraph_length_variance": (
                np.var(paragraph_lengths) if paragraph_lengths else 0
            ),
            "max_paragraph_length": max(paragraph_lengths) if paragraph_lengths else 0,
            "min_paragraph_length": min(paragraph_lengths) if paragraph_lengths else 0,
            "topic_sentence_analysis": topic_sentence_analysis,
        }

    def analyze_academic_expression(self, text: str) -> Dict:
        """
        分析学术表达习惯

        Args:
            text: 输入文本

        Returns:
            学术表达分析结果
        """
        sentences = self._split_sentences(text)
        words = self._tokenize_text(text)

        # 被动语态检测
        passive_voice_ratio = self._calculate_passive_voice_ratio(sentences)

        # 第一人称使用分析
        first_person_analysis = self._analyze_first_person_usage(words)

        # 限定词使用分析
        qualifier_analysis = self._analyze_qualifiers(words)

        return {
            "passive_voice_ratio": passive_voice_ratio,
            "first_person_usage": first_person_analysis,
            "qualifier_usage": qualifier_analysis,
        }

    def calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        计算两个文本的相似度

        Args:
            text1: 第一个文本
            text2: 第二个文本

        Returns:
            相似度分数 (0-1)
        """
        if not text1 or not text2:
            return 0.0

        try:
            # 使用TF-IDF向量化
            tfidf_matrix = self.vectorizer.fit_transform([text1, text2])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return float(similarity)
        except Exception:
            return 0.0

    def calculate_readability_score(self, text: str) -> float:
        """
        计算可读性评分

        Args:
            text: 输入文本

        Returns:
            可读性评分 (0-100)
        """
        sentences = self._split_sentences(text)
        words = self._tokenize_text(text)

        if not sentences or not words:
            return 0.0

        # 基本指标
        avg_sentence_length = len(words) / len(sentences)

        # 词汇多样性
        unique_words = len(set(word.lower() for word in words))
        vocabulary_richness = unique_words / len(words) if words else 0

        # 连接词密度
        connecting_words = [
            "and",
            "but",
            "or",
            "so",
            "yet",
            "for",
            "nor",
            "however",
            "therefore",
            "moreover",
        ]
        connecting_word_count = sum(words.count(word) for word in connecting_words)
        connection_density = connecting_word_count / len(words) if words else 0

        # 综合评分（简单加权平均）
        readability = (
            (1 / (1 + avg_sentence_length / 20)) * 40  # 句长因子
            + vocabulary_richness * 30  # 词汇丰富度
            + min(connection_density * 100, 30)  # 连接词密度
        )

        return min(max(readability, 0), 100)

    def _identify_academic_words(self, words: List[str]) -> List[str]:
        """识别学术词汇"""
        academic_patterns = [
            r".*tion$",
            r".*sion$",
            r".*ment$",  # 名词后缀
            r"^analy.*",
            r"^investig.*",
            r"^examin.*",  # 研究动词
            r"^signific.*",
            r"^substantial.*",
            r"^considerable.*",  # 程度词
        ]

        academic_words = []
        for word in words:
            for pattern in academic_patterns:
                if re.match(pattern, word):
                    academic_words.append(word)
                    break

        return academic_words

    def _analyze_verb_tenses(self, words: List[str]) -> Dict:
        """分析动词时态"""
        # 简化的时态检测
        past_tense_words = [
            "was",
            "were",
            "had",
            "did",
            "went",
            "said",
            "found",
            "showed",
        ]
        present_tense_words = [
            "is",
            "are",
            "has",
            "have",
            "do",
            "go",
            "say",
            "find",
            "show",
        ]

        past_count = sum(words.count(word) for word in past_tense_words)
        present_count = sum(words.count(word) for word in present_tense_words)

        total_verbs = past_count + present_count

        return {
            "past_tense_ratio": past_count / total_verbs if total_verbs > 0 else 0,
            "present_tense_ratio": (
                present_count / total_verbs if total_verbs > 0 else 0
            ),
        }

    def _analyze_topic_sentences(self, paragraphs: List[str]) -> Dict:
        """分析主题句特征"""
        topic_sentences = []

        for para in paragraphs:
            sentences = self._split_sentences(para)
            if sentences:
                topic_sentences.append(sentences[0])

        if not topic_sentences:
            return {}

        # 分析主题句长度
        topic_lengths = []
        for ts in topic_sentences:
            doc = self.nlp(ts)
            topic_lengths.append(len([token for token in doc if token.is_alpha]))

        return {
            "avg_topic_sentence_length": (
                sum(topic_lengths) / len(topic_lengths) if topic_lengths else 0
            ),
            "topic_sentence_variance": np.var(topic_lengths) if topic_lengths else 0,
        }

    def _calculate_passive_voice_ratio(self, sentences: List[str]) -> float:
        """计算被动语态比例"""
        # Use spaCy for more accurate passive voice detection
        total_verbs = 0
        passive_verbs = 0

        for sentence in sentences:
            doc = self.nlp(sentence)
            for token in doc:
                if token.pos_ == "AUX" and token.dep_ == "auxpass":
                    passive_verbs += 1
                elif token.pos_ == "VERB":
                    total_verbs += 1

        return passive_verbs / total_verbs if total_verbs > 0 else 0

    def _analyze_first_person_usage(self, words: List[str]) -> Dict:
        """分析第一人称使用"""
        first_person_words = ["i", "we", "my", "our", "me", "us"]

        first_person_count = sum(words.count(word) for word in first_person_words)
        total_words = len(words)

        return {
            "first_person_count": first_person_count,
            "first_person_ratio": (
                first_person_count / total_words if total_words > 0 else 0
            ),
        }

    def _analyze_qualifiers(self, words: List[str]) -> Dict:
        """分析限定词使用"""
        qualifiers = [
            "very",
            "quite",
            "rather",
            "somewhat",
            "fairly",
            "relatively",
            "considerably",
        ]

        qualifier_count = sum(words.count(word) for word in qualifiers)
        total_words = len(words)

        return {
            "qualifier_count": qualifier_count,
            "qualifier_ratio": qualifier_count / total_words if total_words > 0 else 0,
        }

    def analyze_advanced_features(self, text: str) -> Dict:
        """
        使用spaCy的高级功能进行深度分析

        Args:
            text: 输入文本

        Returns:
            高级分析结果
        """
        doc = self.nlp(text)

        # 命名实体识别
        entities = {}
        for ent in doc.ents:
            if ent.label_ not in entities:
                entities[ent.label_] = []
            entities[ent.label_].append(ent.text)

        # 词性标注统计
        pos_counts = {}
        for token in doc:
            if token.pos_ not in pos_counts:
                pos_counts[token.pos_] = 0
            pos_counts[token.pos_] += 1

        # 依存关系分析
        dependency_patterns = {}
        for token in doc:
            if token.dep_ not in dependency_patterns:
                dependency_patterns[token.dep_] = 0
            dependency_patterns[token.dep_] += 1

        # 词向量相似度分析（如果有向量）
        word_similarities = []
        academic_words = [
            "research",
            "study",
            "analysis",
            "investigation",
            "methodology",
        ]
        for word in academic_words:
            if word in [token.text.lower() for token in doc]:
                for token in doc:
                    if token.has_vector and token.text.lower() != word:
                        similarity = token.similarity(doc.vocab[word])
                        word_similarities.append(
                            {
                                "word": token.text,
                                "similarity": similarity,
                                "target": word,
                            }
                        )

        # 语法复杂度分析
        complex_structures = 0
        for sent in doc.sents:
            # 检测从句（有从属连词标记的句子）
            if any(token.dep_ == "mark" for token in sent):
                complex_structures += 1

        return {
            "entities": entities,
            "pos_distribution": pos_counts,
            "dependency_patterns": dependency_patterns,
            "word_similarities": word_similarities[:10],  # 只返回前10个
            "complex_structure_ratio": (
                complex_structures / len(list(doc.sents)) if doc.sents else 0
            ),
            "has_word_vectors": doc.vocab.vectors.size > 0,
        }

    def calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """
        使用spaCy的词向量计算语义相似度

        Args:
            text1: 第一个文本
            text2: 第二个文本

        Returns:
            语义相似度分数 (0-1)
        """
        try:
            doc1 = self.nlp(text1)
            doc2 = self.nlp(text2)

            # 使用spaCy的内置相似度计算
            similarity = doc1.similarity(doc2)
            return float(similarity)
        except Exception:
            # 如果失败，回退到TF-IDF
            return self.calculate_text_similarity(text1, text2)

    def extract_academic_keywords(self, text: str, top_n: int = 10) -> List[Dict]:
        """
        提取学术关键词，结合词性和重要性

        Args:
            text: 输入文本
            top_n: 返回关键词数量

        Returns:
            关键词列表
        """
        doc = self.nlp(text)

        # 计算词汇重要性（结合词频、词性和长度）
        word_scores = {}
        for token in doc:
            if (
                token.is_alpha
                and token.pos_ in ["NOUN", "ADJ", "VERB"]
                and len(token.text) > 3
                and token.text.lower() not in self.stop_words
            ):

                word = token.text.lower()

                # 基础分数：词频
                base_score = word_scores.get(word, 0) + 1

                # 词性权重
                pos_weight = {"NOUN": 1.5, "ADJ": 1.2, "VERB": 1.3}.get(token.pos_, 1.0)

                # 长度权重（偏好中等长度的词）
                length_weight = (
                    min(len(word) / 8, 1.0)
                    if len(word) <= 8
                    else max(0.5, 1 - (len(word) - 8) / 10)
                )

                # 学术词汇权重
                academic_weight = (
                    1.5
                    if any(
                        pattern in word
                        for pattern in [
                            "tion",
                            "sion",
                            "ment",
                            "analy",
                            "investig",
                            "examin",
                        ]
                    )
                    else 1.0
                )

                word_scores[word] = (
                    base_score * pos_weight * length_weight * academic_weight
                )

        # 排序并返回top_n
        sorted_words = sorted(word_scores.items(), key=lambda x: x[1], reverse=True)
        return [
            {"word": word, "frequency": int(score), "importance": score}
            for word, score in sorted_words[:top_n]
        ]


def main():
    """测试NLP工具功能"""
    nlp = NLPUtils()

    # 测试文本
    test_text = """
    This study investigates the impact of climate change on agricultural productivity. 
    The research methodology involves analyzing data from multiple sources. Furthermore, 
    the findings demonstrate significant correlations between temperature increases and 
    crop yield reductions. Therefore, we recommend implementing adaptive strategies.
    """

    print("句式结构分析:")
    print(nlp.analyze_sentence_structure(test_text))

    print("\n词汇分析:")
    print(nlp.analyze_vocabulary(test_text))

    print("\n可读性评分:")
    print(f"{nlp.calculate_readability_score(test_text):.2f}")

    print(f"\n后端: {nlp.backend}")

    print("\n=== 高级功能测试 ===")

    print("\n高级特征分析:")
    advanced = nlp.analyze_advanced_features(test_text)
    print(f"命名实体: {list(advanced.get('entities', {}).keys())}")
    print(f"词性分布: {advanced.get('pos_distribution', {})}")
    print(f"是否有词向量: {advanced.get('has_word_vectors', False)}")

    print("\n学术关键词提取:")
    keywords = nlp.extract_academic_keywords(test_text, top_n=5)
    for kw in keywords:
        print(f"  {kw['word']}: 重要性={kw['importance']:.2f}")

    print("\n语义相似度测试:")
    text1 = "This research examines organizational behavior."
    text2 = "The study investigates corporate culture."
    semantic_sim = nlp.calculate_semantic_similarity(text1, text2)
    tfidf_sim = nlp.calculate_text_similarity(text1, text2)
    print(f"语义相似度: {semantic_sim:.3f}")
    print(f"TF-IDF相似度: {tfidf_sim:.3f}")


if __name__ == "__main__":
    main()
