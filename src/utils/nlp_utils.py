"""
NLP工具函数模块

提供文本分析、统计指标计算、相似度计算等NLP功能。
"""

import re
import math
from typing import List, Dict, Tuple, Counter
from collections import Counter
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# 下载必要的NLTK数据
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    try:
        nltk.download('punkt')
        nltk.download('stopwords')
    except:
        # 如果下载失败，使用备用方案
        pass

class NLPUtils:
    """NLP工具类"""
    
    def __init__(self):
        """初始化NLP工具"""
        self.stop_words = set(stopwords.words('english'))
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
    
    def analyze_sentence_structure(self, text: str) -> Dict:
        """
        分析句式结构
        
        Args:
            text: 输入文本
            
        Returns:
            句式结构分析结果
        """
        try:
            sentences = sent_tokenize(text)
        except:
            # 如果NLTK不可用，使用简单的句子分割
            sentences = [s.strip() for s in text.split('.') if s.strip()]
        
        if not sentences:
            return {}
        
        # 计算句子长度统计
        sentence_lengths = [len(word_tokenize(sent)) for sent in sentences]
        
        # 识别复合句（包含连接词的句子）
        compound_sentences = 0
        for sent in sentences:
            if any(connector in sent.lower() for connector in ['and', 'but', 'or', 'so', 'yet', 'for', 'nor']):
                compound_sentences += 1
        
        # 识别从句（包含关系代词或从属连词）
        complex_sentences = 0
        subordinating_conjunctions = ['because', 'although', 'while', 'since', 'if', 'when', 'where', 'which', 'that', 'who']
        for sent in sentences:
            if any(conj in sent.lower() for conj in subordinating_conjunctions):
                complex_sentences += 1
        
        return {
            'total_sentences': len(sentences),
            'avg_sentence_length': sum(sentence_lengths) / len(sentence_lengths),
            'sentence_length_variance': np.var(sentence_lengths),
            'compound_sentence_ratio': compound_sentences / len(sentences),
            'complex_sentence_ratio': complex_sentences / len(sentences),
            'max_sentence_length': max(sentence_lengths),
            'min_sentence_length': min(sentence_lengths)
        }
    
    def analyze_vocabulary(self, text: str) -> Dict:
        """
        分析词汇特点
        
        Args:
            text: 输入文本
            
        Returns:
            词汇分析结果
        """
        try:
            # 分词并清理
            words = word_tokenize(text.lower())
            words = [word for word in words if word.isalpha() and word not in self.stop_words]
        except:
            # 如果NLTK不可用，使用简单的词汇分割
            words = [word.lower() for word in text.split() if word.isalpha()]
            words = [word for word in words if word not in self.stop_words]
        
        if not words:
            return {}
        
        word_counts = Counter(words)
        
        # 学术词汇检测（简单的启发式规则）
        academic_words = self._identify_academic_words(words)
        
        # 动词时态分析
        tense_analysis = self._analyze_verb_tenses(words)
        
        return {
            'total_words': len(words),
            'unique_words': len(word_counts),
            'vocabulary_richness': len(word_counts) / len(words),
            'academic_word_ratio': len(academic_words) / len(words),
            'most_common_words': dict(word_counts.most_common(10)),
            'verb_tense_analysis': tense_analysis,
            'avg_word_length': sum(len(word) for word in words) / len(words)
        }
    
    def analyze_paragraph_structure(self, text: str) -> Dict:
        """
        分析段落结构
        
        Args:
            text: 输入文本
            
        Returns:
            段落结构分析结果
        """
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        if not paragraphs:
            return {}
        
        try:
            paragraph_lengths = [len(word_tokenize(p)) for p in paragraphs]
        except:
            paragraph_lengths = [len(p.split()) for p in paragraphs]
        
        # 分析主题句位置（段落第一句的特征）
        topic_sentence_analysis = self._analyze_topic_sentences(paragraphs)
        
        return {
            'total_paragraphs': len(paragraphs),
            'avg_paragraph_length': sum(paragraph_lengths) / len(paragraph_lengths),
            'paragraph_length_variance': np.var(paragraph_lengths),
            'max_paragraph_length': max(paragraph_lengths),
            'min_paragraph_length': min(paragraph_lengths),
            'topic_sentence_analysis': topic_sentence_analysis
        }
    
    def analyze_academic_expression(self, text: str) -> Dict:
        """
        分析学术表达习惯
        
        Args:
            text: 输入文本
            
        Returns:
            学术表达分析结果
        """
        try:
            sentences = sent_tokenize(text)
            words = word_tokenize(text.lower())
        except:
            sentences = [s.strip() for s in text.split('.') if s.strip()]
            words = [word.lower() for word in text.split() if word.isalpha()]
        
        # 被动语态检测
        passive_voice_ratio = self._calculate_passive_voice_ratio(sentences)
        
        # 第一人称使用分析
        first_person_analysis = self._analyze_first_person_usage(words)
        
        # 限定词使用分析
        qualifier_analysis = self._analyze_qualifiers(words)
        
        return {
            'passive_voice_ratio': passive_voice_ratio,
            'first_person_usage': first_person_analysis,
            'qualifier_usage': qualifier_analysis
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
        try:
            sentences = sent_tokenize(text)
            words = word_tokenize(text)
        except:
            sentences = [s.strip() for s in text.split('.') if s.strip()]
            words = [word for word in text.split() if word.isalpha()]
        
        if not sentences or not words:
            return 0.0
        
        # 基本指标
        avg_sentence_length = len(words) / len(sentences)
        avg_word_length = sum(len(word) for word in words if word.isalpha()) / len([w for w in words if w.isalpha()])
        
        # 词汇多样性
        unique_words = len(set(word.lower() for word in words if word.isalpha()))
        vocabulary_richness = unique_words / len(words) if words else 0
        
        # 连接词密度
        connecting_words = ['and', 'but', 'or', 'so', 'yet', 'for', 'nor', 'however', 'therefore', 'moreover']
        connecting_word_count = sum(words.count(word) for word in connecting_words)
        connection_density = connecting_word_count / len(words) if words else 0
        
        # 综合评分（简单加权平均）
        readability = (
            (1 / (1 + avg_sentence_length / 20)) * 40 +  # 句长因子
            vocabulary_richness * 30 +                    # 词汇丰富度
            min(connection_density * 100, 30)            # 连接词密度
        )
        
        return min(max(readability, 0), 100)
    
    def _identify_academic_words(self, words: List[str]) -> List[str]:
        """识别学术词汇"""
        academic_patterns = [
            r'.*tion$', r'.*sion$', r'.*ment$',  # 名词后缀
            r'^analy.*', r'^investig.*', r'^examin.*',  # 研究动词
            r'^signific.*', r'^substantial.*', r'^considerable.*'  # 程度词
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
        past_tense_words = ['was', 'were', 'had', 'did', 'went', 'said', 'found', 'showed']
        present_tense_words = ['is', 'are', 'has', 'have', 'do', 'go', 'say', 'find', 'show']
        
        past_count = sum(words.count(word) for word in past_tense_words)
        present_count = sum(words.count(word) for word in present_tense_words)
        
        total_verbs = past_count + present_count
        
        return {
            'past_tense_ratio': past_count / total_verbs if total_verbs > 0 else 0,
            'present_tense_ratio': present_count / total_verbs if total_verbs > 0 else 0
        }
    
    def _analyze_topic_sentences(self, paragraphs: List[str]) -> Dict:
        """分析主题句特征"""
        topic_sentences = []
        
        for para in paragraphs:
            try:
                sentences = sent_tokenize(para)
            except:
                sentences = [s.strip() for s in para.split('.') if s.strip()]
            
            if sentences:
                topic_sentences.append(sentences[0])
        
        if not topic_sentences:
            return {}
        
        # 分析主题句长度
        try:
            topic_lengths = [len(word_tokenize(ts)) for ts in topic_sentences]
        except:
            topic_lengths = [len(ts.split()) for ts in topic_sentences]
        
        return {
            'avg_topic_sentence_length': sum(topic_lengths) / len(topic_lengths),
            'topic_sentence_variance': np.var(topic_lengths)
        }
    
    def _calculate_passive_voice_ratio(self, sentences: List[str]) -> float:
        """计算被动语态比例"""
        passive_indicators = ['was', 'were', 'been', 'being', 'is', 'are']
        total_verbs = 0
        passive_verbs = 0
        
        for sentence in sentences:
            try:
                words = word_tokenize(sentence.lower())
            except:
                words = [word.lower() for word in sentence.split() if word.isalpha()]
            
            for i, word in enumerate(words):
                if word in passive_indicators:
                    total_verbs += 1
                    # 简单的被动语态检测：be动词 + 过去分词
                    if i + 1 < len(words):
                        next_word = words[i + 1]
                        if any(next_word.endswith(suffix) for suffix in ['ed', 'en', 't']):
                            passive_verbs += 1
        
        return passive_verbs / total_verbs if total_verbs > 0 else 0
    
    def _analyze_first_person_usage(self, words: List[str]) -> Dict:
        """分析第一人称使用"""
        first_person_words = ['i', 'we', 'my', 'our', 'me', 'us']
        
        first_person_count = sum(words.count(word) for word in first_person_words)
        total_words = len(words)
        
        return {
            'first_person_count': first_person_count,
            'first_person_ratio': first_person_count / total_words if total_words > 0 else 0
        }
    
    def _analyze_qualifiers(self, words: List[str]) -> Dict:
        """分析限定词使用"""
        qualifiers = ['very', 'quite', 'rather', 'somewhat', 'fairly', 'relatively', 'considerably']
        
        qualifier_count = sum(words.count(word) for word in qualifiers)
        total_words = len(words)
        
        return {
            'qualifier_count': qualifier_count,
            'qualifier_ratio': qualifier_count / total_words if total_words > 0 else 0
        }

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

if __name__ == "__main__":
    main()
