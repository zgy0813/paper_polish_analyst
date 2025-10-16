"""
配置文件 - 论文风格分析与润色系统
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """系统配置类"""
    
    # AI API配置 (支持OpenAI和DeepSeek)
    AI_PROVIDER = os.getenv('AI_PROVIDER', 'openai')  # 'openai' 或 'deepseek'
    
    # OpenAI配置
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4')
    OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
    
    # DeepSeek配置
    DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
    DEEPSEEK_MODEL = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')
    DEEPSEEK_BASE_URL = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1')
    
    # 通用配置
    AI_MAX_TOKENS = int(os.getenv('AI_MAX_TOKENS', '4000'))
    AI_TEMPERATURE = float(os.getenv('AI_TEMPERATURE', '0.3'))  # 0.3适合大多数分析任务，平衡创造性和一致性
    
    # 分析配置
    BATCH_SIZE = int(os.getenv('BATCH_SIZE', '10'))  # 每批分析的论文数量
    MAX_PAPERS = int(os.getenv('MAX_PAPERS', '100'))  # 最大论文数量
    
    # 规则分类阈值 (基于并集思维)
    FREQUENT_RULE_THRESHOLD = float(os.getenv('FREQUENT_RULE_THRESHOLD', '0.6'))  # 高频规则 (60%+)
    COMMON_RULE_THRESHOLD = float(os.getenv('COMMON_RULE_THRESHOLD', '0.3'))      # 常见规则 (30%-60%)
    ALTERNATIVE_RULE_THRESHOLD = float(os.getenv('ALTERNATIVE_RULE_THRESHOLD', '0.1'))  # 替代规则 (10%-30%)
    
    # 停止条件配置 (基于规则多样性)
    MIN_BATCHES_FOR_DIVERSITY = int(os.getenv('MIN_BATCHES_FOR_DIVERSITY', '8'))    # 最少批次数 (从5改为8)
    MAX_BATCHES_FOR_DIVERSITY = int(os.getenv('MAX_BATCHES_FOR_DIVERSITY', '15'))   # 最多批次数 (从10改为15)
    RULE_DIVERSITY_THRESHOLD = float(os.getenv('RULE_DIVERSITY_THRESHOLD', '0.9'))  # 规则多样性阈值 (从0.7改为0.9)
    
    # 文件路径配置
    DATA_DIR = os.getenv('DATA_DIR', 'data')
    JOURNALS_DIR = os.path.join(DATA_DIR, 'journals')
    EXTRACTED_DIR = os.path.join(DATA_DIR, 'extracted')
    INDIVIDUAL_REPORTS_DIR = os.path.join(DATA_DIR, 'individual_reports')
    BATCH_SUMMARIES_DIR = os.path.join(DATA_DIR, 'batch_summaries')
    OFFICIAL_GUIDES_DIR = os.path.join(DATA_DIR, 'official_guides')
    
    # 输出文件
    STYLE_GUIDE_JSON = os.path.join(DATA_DIR, 'style_guide.json')
    STYLE_GUIDE_MD = os.path.join(DATA_DIR, 'style_guide.md')
    ANALYSIS_LOG = os.path.join(DATA_DIR, 'analysis_log.json')
    
    # 质量评分权重
    SCORE_WEIGHTS = {
        'style_match': 0.4,      # 风格匹配度权重
        'academic_norm': 0.4,    # 学术规范性权重
        'readability': 0.2       # 可读性权重
    }
    
    # 规则分类阈值
    CORE_RULE_THRESHOLD = 0.8    # 核心规则阈值(80%+论文遵循)
    OPTIONAL_RULE_THRESHOLD = 0.5  # 可选规则阈值(50%-80%论文遵循)
    
    @classmethod
    def get_ai_config(cls):
        """获取当前AI配置"""
        if cls.AI_PROVIDER.lower() == 'deepseek':
            return {
                'provider': 'deepseek',
                'api_key': cls.DEEPSEEK_API_KEY,
                'model': cls.DEEPSEEK_MODEL,
                'base_url': cls.DEEPSEEK_BASE_URL,
                'max_tokens': cls.AI_MAX_TOKENS,
                'temperature': cls.AI_TEMPERATURE
            }
        else:
            return {
                'provider': 'openai',
                'api_key': cls.OPENAI_API_KEY,
                'model': cls.OPENAI_MODEL,
                'base_url': cls.OPENAI_BASE_URL,
                'max_tokens': cls.AI_MAX_TOKENS,
                'temperature': cls.AI_TEMPERATURE
            }
    
    @classmethod
    def validate(cls):
        """验证配置"""
        ai_config = cls.get_ai_config()
        
        # 检查API Key
        if not ai_config['api_key']:
            print(f"⚠️ {ai_config['provider'].upper()}_API_KEY 环境变量未设置，部分功能可能不可用")
        else:
            print(f"✅ 使用 {ai_config['provider'].upper()} API")
            print(f"   模型: {ai_config['model']}")
            print(f"   Base URL: {ai_config['base_url']}")
        
        # 确保目录存在
        os.makedirs(cls.DATA_DIR, exist_ok=True)
        os.makedirs(cls.JOURNALS_DIR, exist_ok=True)
        os.makedirs(cls.EXTRACTED_DIR, exist_ok=True)
        os.makedirs(cls.INDIVIDUAL_REPORTS_DIR, exist_ok=True)
        os.makedirs(cls.BATCH_SUMMARIES_DIR, exist_ok=True)
        os.makedirs(cls.OFFICIAL_GUIDES_DIR, exist_ok=True)
        
        return True
