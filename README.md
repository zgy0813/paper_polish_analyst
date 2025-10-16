# 📝 论文风格分析与润色系统

一个基于AI的智能学术论文润色工具，专门针对AMJ（Academy of Management Journal）期刊的写作风格进行优化。系统通过分析历史期刊论文提取写作风格特征，结合官方风格指南，提供多轮交互式润色和质量评分功能。

**🌟 推荐使用OpenAI GPT模型**，提供最佳的学术写作理解和润色质量，同时支持DeepSeek API作为成本优化选择。

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![AI Model](https://img.shields.io/badge/AI-OpenAI%20GPT--4o-green.svg)](https://openai.com)

## ✨ 核心特性

### 🔍 智能分析
- **增量式分析**: 分批处理论文，智能判断何时停止分析，节省API成本
- **分层风格提取**: 单篇→批次→全局三层分析，区分核心规则和可选规则
- **官方指南整合**: 融合AMJ官方风格指南与历史期刊经验数据，生成混合风格指南
- **双源规则整合**: 官方规则优先，经验规则补充，智能冲突检测与解决
- **示例库构建**: 每条规则配备真实示例和统计数据
- **GPT优化**: 利用最新的OpenAI模型提供更准确的学术写作分析
- **spaCy NLP引擎**: 使用en_core_web_md模型提供高性能的文本分析和语义理解

### ✨ 多轮润色
- **三轮渐进优化**: 句式结构 → 词汇选择 → 段落衔接
- **交互式确认**: 用户可逐条确认修改建议，控制润色过程
- **上下文感知**: 基于整篇论文的语义理解进行润色
- **批量处理**: 支持单篇或批量论文润色

### 📊 质量评估
- **多维度评分**: 风格匹配度、学术规范性、可读性
- **可视化报告**: 润色前后对比图表和详细分析
- **改进建议**: 针对性的优化建议和最佳实践
- **量化指标**: 客观的评分体系和改进幅度统计

### 🖥️ 双界面支持
- **命令行界面**: 适合批处理和自动化脚本
- **Web界面**: 直观的交互式用户界面
- **实时监控**: 分析进度和系统状态实时显示

## 📖 获取帮助

在开始使用系统之前，建议先阅读以下详细文档：

- 🤖 **[AI模型配置指南](docs/AI模型配置指南.md)** - 详细的AI模型配置和优化指南
- 📊 **[AI模型参数配置分析文档](docs/AI模型参数配置分析文档.md)** - 深入分析AI模型参数配置原理
- 🔍 **[单文件分析使用指南](docs/单个文件分析使用指南.md)** - 单个文件分析的详细使用说明
- 📋 **[多文件合并分析逻辑详解文档](docs/多文件合并分析逻辑详解文档.md)** - 多文件合并分析的完整逻辑说明
- 🏛️ **[官方style文档整合历史期刊论文规则逻辑详解文档](docs/官方style文档整合历史期刊论文规则逻辑详解文档.md)** - 官方风格指南整合的详细逻辑
- 🧠 **[NLP分析原理详解文档](docs/NLP分析原理详解文档.md)** - NLP分析的技术原理和实现细节
- 📋 **[JSON解析改进设计文档](docs/JSON解析改进设计文档.md)** - JSON解析功能的改进设计说明

> 💡 **提示**: 这些文档包含了系统的核心技术原理和详细使用说明，建议在遇到问题时优先查阅相关文档。

## 🚀 快速开始

### 1. 环境要求
- Python 3.9+
- OpenAI API Key（推荐）或 DeepSeek API Key

### 2. 创建隔离环境（推荐）
```bash
# 克隆项目
git clone <repository-url>
cd paper_polish_analyst

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 升级pip
pip install --upgrade pip

# 安装依赖
pip install -r requirements.txt

# 下载spaCy英文模型
python -m spacy download en_core_web_md
```

### 3. 安装依赖（不使用虚拟环境）
```bash
# 克隆项目
git clone <repository-url>
cd paper_polish_analyst

# 安装依赖
pip install -r requirements.txt

# 下载spaCy英文模型
python -m spacy download en_core_web_md
```

### 4. 配置API密钥
```bash
# 设置环境变量（推荐使用OpenAI）
export OPENAI_API_KEY="your_openai_key_here"
# 或使用DeepSeek（备选方案）
export DEEPSEEK_API_KEY="your_deepseek_key_here"

# 或创建.env文件
echo "OPENAI_API_KEY=your_openai_key_here" > .env
# 或使用DeepSeek
echo "DEEPSEEK_API_KEY=your_deepseek_key_here" > .env
```

### 5. 验证安装
```bash
# 检查系统状态
python main.py status
```

如果配置正确，您会看到：
```
✅ 使用 OpenAI API
   模型: GPT
   Base URL: https://api.openai.com/v1
```

### 6. 快速验证功能
```bash
# 验证质量评分功能（无需API Key）
python main.py score --text "这是一个测试论文。"

# 查看风格指南
python main.py guide

# 启动Web界面
streamlit run app.py
```

### 7. 准备数据
将期刊论文PDF文件放入 `data/journals/` 目录。

### 8. 虚拟环境使用说明

#### 激活虚拟环境
```bash
# 每次使用前都需要激活虚拟环境
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

#### 退出虚拟环境
```bash
# 使用完毕后退出虚拟环境
deactivate
```

#### 虚拟环境优势
- **依赖隔离**: 避免与其他项目依赖冲突
- **版本控制**: 锁定特定版本的依赖包
- **环境清洁**: 保持系统Python环境的干净
- **部署一致**: 确保开发和生产环境一致

## 📖 使用指南

### 完整工作流程

#### 第一步：PDF文本提取
```bash
# 提取所有PDF文件
python main.py extract

# 检查提取结果
python main.py status
```

**功能特性**：
- 基于PyMuPDF的高精度PDF解析
- 自动处理双栏布局的学术论文
- 智能段落识别和文本清理
- 支持批量处理，提取成功率100%

#### 第二步：风格分析
```bash
# 增量式分析（推荐）
python main.py analyze --batch-size 10 --max-papers 50

# 恢复中断的分析
python main.py analyze --resume

# 分析单个文件
python main.py analyze-individual --progress
```

**分析过程**：
- 智能跳过已分析的论文，避免重复处理
- 分批生成汇总报告，支持增量学习
- 基于规则多样性自动停止，收集更多风格模式
- 生成详细的单篇和批次分析报告
- 采用并集思维：通过规则多样性收集和优先级排序，确保规则库的完整性和丰富性

#### 第三步：生成风格指南
```bash
# 从批次汇总文件生成最终风格指南
python main.py generate-guide

# 指定输入目录和输出文件
python main.py generate-guide --input-dir data/batch_summaries --output data/style_guide.json

# 查看生成命令帮助
python main.py generate-guide --help
```

**生成功能**：
- 自动扫描批次汇总文件目录
- 智能加载所有批次的分析结果
- 基于并集思维进行全局风格整合
- 生成包含规则分类的完整风格指南
- 显示详细的规则统计和分类信息
- 验证生成文件的完整性

#### 第四步：整合官方指南
```bash
# 整合官方风格指南与经验数据
python main.py integrate_guide --validate

# 检查缓存状态
python main.py cache_status

# 强制重新解析
python main.py integrate_guide --force-refresh

# 使用自定义官方指南文件
python main.py integrate_guide --official-guide data/official_guides/AMJ_style_guide.pdf
```

**整合功能**：
- 自动解析AMJ官方风格指南PDF
- 融合历史期刊分析结果，生成混合风格指南
- 智能冲突检测与解决（官方规则优先）
- 规则验证和一致性检查
- 生成混合风格指南（JSON + Markdown）
- 支持规则优先级排序和执行级别分级

#### 第五步：论文润色
```bash
# 交互式润色（推荐）
python main.py polish --text "论文内容" --interactive

# 从文件润色
python main.py polish --file paper.txt --interactive

# 批量润色
python main.py polish --text "论文内容" --output polished.txt

# 基于风格选择的润色（新功能）
python main.py polish --text "论文内容" --style conservative
python main.py polish --text "论文内容" --style balanced
python main.py polish --text "论文内容" --style innovative
python main.py polish --text "论文内容" --style auto  # 自动推荐风格
```

**润色流程**：
- **第一轮**: 句式结构调整和语法优化
- **第二轮**: 词汇选择和表达优化
- **第三轮**: 段落衔接和逻辑流畅性
- 支持逐条确认修改，用户完全控制润色过程

**风格选择**（新功能）：
- **保守风格 (conservative)**: 遵循高频规则，稳定可靠，适合正式学术论文
- **平衡风格 (balanced)**: 结合高频和常见规则，适度创新，适合一般学术写作
- **创新风格 (innovative)**: 包含所有规则类型，多样化选择，适合创意写作
- **自动推荐 (auto)**: 基于论文特征智能推荐最适合的风格

#### 第六步：质量评估
```bash
# 评估论文质量
python main.py score --text "论文内容"

# 评估文件
python main.py score --file paper.txt
```

**评估维度**：
- **风格匹配度**: 与AMJ期刊风格的符合程度
- **学术规范性**: 引用格式、术语使用、学术写作规范
- **可读性**: 语言流畅性、逻辑清晰度、表达准确性

### Web界面使用

```bash
# 启动Web界面
streamlit run app.py
```

访问 http://localhost:8501 享受直观的交互体验：

- 📝 **论文润色**: 支持文本输入和文件上传，实时润色反馈
- 📊 **质量评估**: 可视化评分图表和详细分析报告
- 📖 **风格指南**: 规则浏览、分类查看和下载功能
- ⚙️ **系统状态**: 配置检查、状态监控和日志查看

**Web界面特色**：
- 交互式润色界面，支持逐条确认修改
- 可视化评分图表，直观显示改进效果
- 实时配置检查和状态监控
- 支持文件上传和结果下载

## 🏛️ 混合风格指南核心价值

### 双源规则整合
系统创新性地将**官方style文档规则**与**历史期刊论文实证分析规则**进行智能整合：

**🎯 官方规则（权威性）**
- 来源：AMJ官方发布的style guide PDF文档
- 特点：必须遵循的期刊要求，权威性强
- 优先级：最高，确保期刊合规性

**📊 经验规则（实证性）**
- 来源：多篇已发表的高质量AMJ论文分析
- 特点：实际写作模式，可操作性强
- 优先级：基于遵循率分级（核心/可选/建议）

**🤝 智能整合机制**
- **冲突检测**：自动识别官方规则与经验规则的冲突
- **优先级排序**：官方规则 > 核心经验规则 > 可选经验规则 > 建议规则
- **执行级别**：mandatory（必须）→ strongly_recommended（强烈推荐）→ recommended（推荐）→ suggested（建议）

### 四层规则体系
```
Level 1: 官方规则 (Official Rules)
├── 必须严格遵循的期刊要求
├── 来源：AMJ官方style guide
└── 执行级别：mandatory

Level 2: 核心经验规则 (Core Rules)  
├── 80%+论文遵循的写作模式
├── 来源：历史期刊实证分析
└── 执行级别：strongly_recommended

Level 3: 可选经验规则 (Optional Rules)
├── 50%-80%论文遵循的模式
├── 来源：历史期刊实证分析  
└── 执行级别：recommended

Level 4: 建议规则 (Suggested Rules)
├── 遵循率较低的创新模式
├── 来源：历史期刊实证分析
└── 执行级别：suggested
```

## 📊 数据流程详解

### PDF提取流程
```
PDF文件 → PyMuPDF解析 → 布局分析 → 文本重组 → 清理优化 → 保存TXT
```

**关键特性**：
- 双栏布局自动识别和重组
- 段落边界智能检测
- 连词问题自动修复
- 特殊字符和格式清理

### 分析流程
```
提取文本 → NLP分析 → GPT分析 → 单篇报告 → 批次汇总 → 风格指南
```

**分析层次**：
- **NLP层**：基础语言特征统计
- **GPT层**：深度语义和风格分析
- **汇总层**：模式识别和规则提取

### 润色流程
```
原始文本 → 风格匹配 → 三轮润色 → 质量评估 → 最终输出
```

**润色策略**：
- 基于风格指南的规则匹配
- 渐进式优化策略
- 上下文感知的修改建议

## 🏗️ 系统架构

### 核心模块

#### 📊 分析模块 (`src/analysis/`)
- **增量式分析器** (`incremental_analyzer.py`): 智能分批处理，避免重复分析
- **分层分析器** (`layered_analyzer.py`): NLP + AI双重分析，三层特征提取
- **质量评分器** (`quality_scorer.py`): 多维度质量评估和评分系统
- **风格指南生成器** (`style_guide_generator.py`): 规则库构建和指南生成
- **规则验证器** (`rule_validator.py`): 规则一致性和有效性验证

#### 🔧 核心模块 (`src/core/`)
- **PDF提取器** (`pymupdf_extractor.py`): 基于PyMuPDF的高精度文本提取
- **官方指南解析器** (`official_guide_parser.py`): AMJ官方指南PDF解析
- **AI提示模板** (`prompts.py`): 结构化的AI交互提示词库

#### ✨ 润色模块 (`src/polishing/`)
- **多轮润色器** (`multi_round_polisher.py`): 三轮渐进式润色优化

#### 🛠️ 工具模块 (`src/utils/`)
- **NLP工具** (`nlp_utils.py`): 文本分析、相似度计算、可读性评分
- **日志配置** (`logger_config.py`): 统一的日志记录和配置管理

### 技术栈

- **AI模型**: OpenAI GPT（推荐）/ DeepSeek API
- **PDF处理**: PyMuPDF (fitz)
- **NLP分析**: spaCy (en_core_web_md), scikit-learn
- **Web界面**: Streamlit, Plotly
- **命令行**: Click
- **数据处理**: pandas, numpy

### 工作流程

```
PDF论文 → 文本提取 → 增量分析 → 分层特征提取 → 风格指南 → 官方指南整合 → 论文润色 → 质量评分
```

## 📊 输出示例

### 润色结果展示

```markdown
# 论文润色报告

## 质量评分对比
| 维度 | 润色前 | 润色后 | 改进 |
|------|--------|--------|------|
| 风格匹配度 | 62分 | 89分 | +27分 |
| 学术规范性 | 75分 | 92分 | +17分 |
| 可读性 | 68分 | 85分 | +17分 |
| **总分** | **68分** | **89分** | **+21分** |

## 润色后的论文
[完整的润色后文本]

## 修改详情 (共23处)
### 第一轮: 句式结构调整 (8处修改)
#### 修改1: 第1段第2句
**原文**: This study investigates the impact of organizational culture...
**修改后**: This study examines the impact of organizational culture...
**修改理由**: 使用"examines"替代"investigates",更符合AMJ期刊的词汇偏好
**风格依据**: 规则 `vocab-examine` (核心规则,遵循率87%)

### 第二轮: 词汇优化 (10处修改)
#### 修改1: 第2段第1句
**原文**: The research shows that organizational change...
**修改后**: The findings demonstrate that organizational change...
**修改理由**: 使用"demonstrate"替代"show",更符合学术写作规范
**风格依据**: 规则 `vocab-demonstrate` (核心规则,遵循率92%)

### 第三轮: 段落衔接 (5处修改)
#### 修改1: 第2段开头
**原文**: Previous studies have shown that...
**修改后**: Building on this foundation, previous studies have shown that...
**修改理由**: 添加过渡短语,增强段落间的逻辑连接
**风格依据**: 规则 `trans-coherence` (核心规则,遵循率85%)
```

### 混合风格指南结构

```json
{
  "style_guide_version": "2.0",
  "generation_date": "2025-01-15",
  "guide_type": "hybrid",
  "total_papers_analyzed": 82,
  "official_rules_count": 23,
  "empirical_rules_count": 133,
  "rule_summary": {
    "total_rules": 156,
    "official_rules": 23,
    "empirical_rules": 133,
    "core_rules": 89,
    "optional_rules": 67
  },
  "rules": [
    {
      "rule_id": "official-format-title-case",
      "rule_type": "official",
      "category": "Format Guidelines",
      "description": "Use title case for paper headings",
      "priority": "highest",
      "source": "official_guide",
      "enforcement_level": "mandatory",
      "requirements": [
        "Capitalize first letter of each word",
        "Capitalize important words (nouns, verbs, adjectives, adverbs)"
      ],
      "examples": [
        {
          "correct": "The Impact of Climate Change on Agricultural Productivity",
          "incorrect": "the impact of climate change on agricultural productivity",
          "explanation": "Important words in titles should be capitalized"
        }
      ]
    },
    {
      "rule_id": "empirical-vocab-examine-vs-investigate",
      "rule_type": "core",
      "category": "词汇选择",
      "description": "优先使用examine而非investigate描述研究目的",
      "frequency": 0.78,
      "source": "empirical_analysis",
      "enforcement_level": "strongly_recommended",
      "examples": [
        {
          "before": "This study investigates the impact of...",
          "after": "This study examines the impact of...",
          "source": "paper_23.pdf",
          "context": "描述研究目的时"
        }
      ],
      "statistics": {
        "examine_count": 156,
        "investigate_count": 44,
        "papers_using_examine": 78
      }
    }
  ],
  "usage_guidelines": {
    "official_rules": "Official Rules: Journal requirements that must be strictly followed",
    "core_rules": "Core Rules: Followed by 80%+ papers, strongly recommended",
    "optional_rules": "Optional Rules: Followed by 50%-80% papers, choose as appropriate",
    "conflict_resolution": "When rules conflict, official rules take priority over empirical rules"
  }
}
```

## ⚙️ 配置说明

### 环境变量配置

```bash
# AI API配置（必需）
export OPENAI_API_KEY="your_openai_key"         # 推荐使用OpenAI
export DEEPSEEK_API_KEY="your_deepseek_key"     # 或使用DeepSeek

# 可选配置
export AI_PROVIDER="openai"                     # AI提供商选择（openai/deepseek）
export BATCH_SIZE=10                            # 批次大小
export MAX_PAPERS=100                           # 最大论文数
export SIMILARITY_THRESHOLD=0.9                 # 相似度阈值
export AI_TEMPERATURE=0.3                       # AI生成温度
```

### 配置文件 (`config.py`)

主要配置项包括：

```python
# 分析配置
BATCH_SIZE = 10                    # 每批分析的论文数量
MAX_PAPERS = 100                   # 最大分析论文数量
SIMILARITY_THRESHOLD = 0.9         # 相似度阈值（停止分析条件）

# 规则分类阈值
CORE_RULE_THRESHOLD = 0.8          # 核心规则阈值（80%+论文遵循）
OPTIONAL_RULE_THRESHOLD = 0.5      # 可选规则阈值（50%-80%论文遵循）

# AI模型配置
AI_MODEL = "GPT"                # 使用的AI模型（推荐GPT）
AI_MAX_TOKENS = 4000               # 最大token数
AI_TEMPERATURE = 0.3               # 生成温度

# 质量评分权重
SCORE_WEIGHTS = {
    'style_match': 0.4,            # 风格匹配度权重
    'academic_norm': 0.4,          # 学术规范性权重
    'readability': 0.2             # 可读性权重
}
```

## 📁 项目结构

```
ai/
├── 📄 README.md                      # 项目说明文档
├── 📄 LICENSE                        # MIT开源许可证
├── ⚙️ config.py                      # 系统配置文件
├── 🚀 main.py                        # 命令行入口
├── 🌐 app.py                         # Web界面入口
├── 📦 requirements.txt               # 依赖包列表
│
├── 📁 data/                          # 数据目录
│   ├── 📁 journals/                  # 期刊PDF文件
│   ├── 📁 extracted/                 # 提取的文本文件
│   ├── 📁 individual_reports/        # 单篇分析报告
│   ├── 📁 batch_summaries/           # 批次汇总报告
│   ├── 📁 official_guides/           # 官方风格指南
│   │   └── 📄 AMJ_style_guide.pdf    # AMJ官方风格指南
│   ├── 📄 style_guide.json           # 风格规则库
│   ├── 📄 style_guide.md             # 人类可读版本
│   ├── 📄 hybrid_style_guide.json    # 混合风格指南
│   └── 📄 analysis_log.json          # 分析过程日志
│
├── 📁 src/                           # 源代码
│   ├── 📁 analysis/                  # 分析模块
│   │   ├── incremental_analyzer.py   # 增量式分析器
│   │   ├── layered_analyzer.py       # 分层风格分析器
│   │   ├── quality_scorer.py         # 质量评分器
│   │   ├── style_guide_generator.py  # 风格指南生成器
│   │   └── rule_validator.py         # 规则验证器
│   │
│   ├── 📁 core/                      # 核心模块
│   │   ├── pymupdf_extractor.py      # PDF文本提取器
│   │   ├── official_guide_parser.py  # 官方指南解析器
│   │   └── prompts.py                # AI提示模板
│   │
│   ├── 📁 polishing/                 # 润色模块
│   │   └── multi_round_polisher.py   # 多轮润色器
│   │
│   └── 📁 utils/                     # 工具模块
│       ├── nlp_utils.py              # NLP工具函数
│       └── logger_config.py          # 日志配置
│
├── 📁 docs/                          # 文档目录
│   ├── 🤖 AI模型配置指南.md
│   ├── 📊 AI模型参数配置分析文档.md
│   ├── 🔍 单个文件分析使用指南.md
│   ├── 📋 多文件合并分析逻辑详解文档.md
│   ├── 🏛️ 官方style文档整合历史期刊论文规则逻辑详解文档.md
│   ├── 🧠 NLP分析原理详解文档.md
│   └── 📋 JSON解析改进设计文档.md
│
├── 📁 examples/                      # 示例代码
│   └── individual_analysis_example.py
│
│
└── 📁 logs/                          # 日志目录
    ├── app_20250114.log
    └── json_parse_errors.json
```

## 🔧 高级功能

### 缓存管理
```bash
# 检查官方规则缓存状态
python main.py cache_status

# 清理缓存
python main.py clear_cache
```

### 风格指南生成
```bash
# 从批次汇总重新生成风格指南
python main.py generate-guide

# 使用自定义参数生成
python main.py generate-guide --input-dir data/batch_summaries --output data/custom_style_guide.json
```

**功能特点**：
- 自动检测所有批次汇总文件
- 显示每个批次的论文数量和规则数量
- 基于并集思维进行全局风格整合
- 生成包含规则分类的完整指南
- 提供详细的规则统计和验证信息

### 增量分析
系统支持增量分析，避免重复处理：
- 自动检测已分析的论文
- 跳过已存在的individual_reports
- 重新生成batch_summaries
- 支持断点续传

### 规则验证
```bash
# 验证规则一致性
python main.py integrate_guide --validate
```

验证内容包括：
- 官方规则与经验规则的一致性
- 规则冲突检测
- 规则有效性验证

### 缓存管理
```bash
# 检查官方规则缓存状态
python main.py cache_status

# 清理缓存
python main.py clear_cache
```

### 增量分析
系统支持增量分析，避免重复处理：
- 自动检测已分析的论文
- 跳过已存在的individual_reports
- 重新生成batch_summaries
- 支持断点续传

## ⚠️ 注意事项

### API成本控制
- 首次分析100篇论文需要较多API调用
- 建议使用较小的批次大小（3-10篇）
- 监控API使用量，避免超出配额
- OpenAI GPT提供最佳质量，DeepSeek API可作为成本优化选择

### PDF质量要求
- 确保PDF文件包含可提取的文本
- 避免扫描版PDF或图片格式
- 复杂的表格和公式可能影响提取效果
- 建议使用原生的PDF文件

### 润色结果使用
- 润色结果仅供参考，建议人工审核
- 重要的学术内容请仔细检查
- 可以根据需要调整风格指南规则
- 保持整篇论文风格的一致性

### 性能优化建议
- 大文件分析可能需要较长时间
- 建议在性能较好的机器上运行
- 可以中断后使用`--resume`恢复
- 定期清理临时文件和日志

### 虚拟环境注意事项
- **每次使用前激活**: 记得激活虚拟环境后再运行命令
- **环境隔离**: 虚拟环境中的包不会影响系统Python环境
- **依赖管理**: 使用`pip freeze > requirements.txt`更新依赖列表
- **跨平台兼容**: 虚拟环境在不同操作系统间需要重新创建

## 🐛 故障排除

### 常见问题解决

**1. API调用失败**
```bash
# 检查API Key配置
python main.py status

# 验证OpenAI API密钥有效性
python -c "import openai; openai.api_key='your_key'; print('OpenAI配置正确')"

# 或验证DeepSeek API密钥
python -c "import requests; print('DeepSeek配置正确')"
```

**2. PDF提取失败**
```bash
# 检查PDF文件质量
python main.py extract

# 查看提取日志
tail -f logs/app_$(date +%Y%m%d).log
```

**3. 内存不足**
```python
# 在config.py中减小批次大小
BATCH_SIZE = 5
MAX_PAPERS = 50
```

**4. 风格指南不存在**
```bash
# 先运行分析
python main.py analyze

# 或使用单个文件分析
python main.py analyze-individual

# 从批次汇总生成风格指南
python main.py generate-guide
```

**5. 批次汇总文件缺失**
```bash
# 检查批次汇总文件是否存在
ls data/batch_summaries/

# 如果不存在，先运行分析生成批次汇总
python main.py analyze

# 然后生成风格指南
python main.py generate-guide
```

**6. 虚拟环境问题**
```bash
# 虚拟环境未激活
# 激活虚拟环境
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate     # Windows

# 依赖包未安装
# 确保在虚拟环境中安装依赖
pip install -r requirements.txt

# 虚拟环境损坏
# 删除并重新创建
rm -rf venv               # macOS/Linux
# 或
rmdir /s venv             # Windows
python -m venv venv
source venv/bin/activate  # 重新激活
pip install -r requirements.txt
```

### 日志查看
```bash
# 查看详细日志
tail -f logs/app_$(date +%Y%m%d).log

# 查看JSON解析错误
cat logs/json_parse_errors.json
```

### 系统状态检查
```bash
# 全面系统状态检查
python main.py status

# 查看风格指南摘要
python main.py guide
```

## 📈 性能优化

### 分析效率
- **批量处理**：合理设置batch_size
- **增量分析**：避免重复处理
- **缓存机制**：减少重复计算
- **提前停止**：风格稳定时自动停止

### 资源管理
- **内存使用**：分批处理大文件
- **API调用**：控制请求频率
- **存储空间**：定期清理临时文件

## 🎯 最佳实践

### 分析策略
1. **小批量开始**：先用3-5篇论文测试
2. **逐步扩大**：确认效果后增加批次
3. **定期验证**：检查规则质量
4. **持续优化**：根据结果调整参数

### 润色建议
1. **多轮润色**：充分利用三轮润色功能
2. **质量评估**：润色后进行质量检查
3. **人工校对**：AI润色后仍需人工检查
4. **风格一致**：保持整篇论文风格统一

## 🚀 开发计划

### 已完成功能 ✅
- [x] 基础架构和配置系统
- [x] PDF文本提取模块（PyMuPDF）
- [x] 增量式分析引擎
- [x] 分层风格分析系统（单篇→批次→全局）
- [x] 官方指南解析和整合
- [x] 混合风格指南生成器（官方规则+经验规则）
- [x] 智能冲突检测与解决机制
- [x] 多轮润色模块
- [x] 质量评分系统
- [x] 命令行界面（完整）
- [x] Web界面（Streamlit）
- [x] 完整的文档体系和使用指南
- [x] spaCy NLP引擎集成
- [x] 规则验证和一致性检查

### 未来计划 🔮
- [ ] 支持更多文档格式（Word, LaTeX）
- [ ] 添加领域特定的风格模板
- [ ] 实现批量论文处理流水线
- [ ] 添加协作和版本控制功能
- [ ] 支持多语言论文处理
- [ ] 集成更多AI模型选择
- [ ] 添加论文结构分析功能
- [ ] 实现实时协作润色

## 🤝 贡献指南

欢迎为项目做出贡献！请遵循以下步骤：

1. **Fork项目** 并克隆到本地
2. **创建功能分支** `git checkout -b feature/amazing-feature`
3. **提交更改** `git commit -m 'Add amazing feature'`
4. **推送分支** `git push origin feature/amazing-feature`
5. **创建Pull Request**

### 开发环境设置
```bash
# 创建并激活虚拟环境
python -m venv venv
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate     # Windows

# 安装开发依赖
pip install -r requirements.txt
pip install black flake8

# 检查系统状态
python main.py status

# 代码格式化
black src/
flake8 src/
```

## 📄 许可证

本项目采用MIT许可证，详见 [LICENSE](LICENSE) 文件。

### MIT许可证说明

MIT许可证是一个宽松的开源许可证，允许：

✅ **自由使用**: 任何人都可以免费使用本软件  
✅ **自由修改**: 可以修改源代码以满足您的需求  
✅ **自由分发**: 可以重新分发软件，包括商业用途  
✅ **自由销售**: 可以将软件包含在商业产品中销售  
✅ **专利使用**: 可以使用软件中涉及的专利技术  

**唯一要求**: 在分发时保留原始的版权声明和许可证文本。

这种许可证确保了软件的最大自由度，同时保护了原作者的权益。

## 📞 支持与联系


### 问题反馈
- 🐛 提交 [GitHub Issue](https://github.com/your-repo/issues)
- 💬 参与 [Discussions](https://github.com/your-repo/discussions)
- 📧 发送邮件至项目维护者

### 社区
- ⭐ 给项目点星支持
- 🍴 Fork项目进行二次开发
- 🔄 关注项目更新和发布

---

**🎉 享受智能论文润色的便利！让AI助力您的学术写作，提升论文质量和发表成功率。**

<div align="center">

**⭐ 如果这个项目对您有帮助，请给我们一个Star！**

</div>