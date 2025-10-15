"""
论文风格分析与润色系统 - Web界面

基于Streamlit的交互式Web界面，提供论文润色和质量评分功能。
"""

import streamlit as st
import json
import os
import sys
from pathlib import Path
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 添加src目录到路径
sys.path.append(str(Path(__file__).parent / 'src'))

from config import Config
from src.polishing.multi_round_polisher import MultiRoundPolisher
from src.analysis.quality_scorer import QualityScorer
from src.analysis.style_guide_generator import StyleGuideGenerator

# 页面配置
st.set_page_config(
    page_title="论文风格分析与润色系统",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2e8b57;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .score-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
    }
    .modification-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e1e5e9;
        margin: 0.5rem 0;
    }
    .success-card {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
    }
    .warning-card {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """主函数"""
    # 标题
    st.markdown('<div class="main-header">📝 论文风格分析与润色系统</div>', unsafe_allow_html=True)
    
    # 侧边栏
    setup_sidebar()
    
    # 主内容区域
    tab1, tab2, tab3, tab4 = st.tabs(["📝 论文润色", "📊 质量评估", "📖 风格指南", "⚙️ 系统状态"])
    
    with tab1:
        paper_polishing_interface()
    
    with tab2:
        quality_assessment_interface()
    
    with tab3:
        style_guide_interface()
    
    with tab4:
        system_status_interface()

def setup_sidebar():
    """设置侧边栏"""
    st.sidebar.title("🔧 系统配置")
    
    # 检查配置
    try:
        Config.validate()
        st.sidebar.success("✅ 配置验证通过")
    except Exception as e:
        st.sidebar.error(f"❌ 配置错误: {str(e)}")
        return
    
    # 检查风格指南
    if Path(Config.STYLE_GUIDE_JSON).exists():
        st.sidebar.success("✅ 风格指南已加载")
        with open(Config.STYLE_GUIDE_JSON, 'r', encoding='utf-8') as f:
            guide = json.load(f)
        st.sidebar.info(f"📊 规则数量: {len(guide.get('rules', []))}")
    else:
        st.sidebar.warning("⚠️ 风格指南不存在")
        st.sidebar.info("请先运行: `python main.py analyze`")
    
    # 系统信息
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📋 系统信息")
    st.sidebar.text(f"Python版本: {sys.version.split()[0]}")
    st.sidebar.text(f"Streamlit版本: {st.__version__}")

def paper_polishing_interface():
    """论文润色界面"""
    st.markdown('<div class="section-header">📝 论文润色</div>', unsafe_allow_html=True)
    
    # 输入方式选择
    input_method = st.radio("选择输入方式:", ["直接输入", "上传文件"])
    
    paper_text = ""
    
    if input_method == "直接输入":
        paper_text = st.text_area(
            "请输入论文内容:",
            height=300,
            placeholder="在此粘贴您的论文内容..."
        )
    else:
        uploaded_file = st.file_uploader(
            "选择文件",
            type=['txt', 'md'],
            help="支持 .txt 和 .md 格式"
        )
        
        if uploaded_file is not None:
            paper_text = uploaded_file.read().decode('utf-8')
            st.success(f"✅ 文件已上传: {uploaded_file.name}")
    
    if paper_text:
        # 润色选项
        col1, col2 = st.columns(2)
        
        with col1:
            interactive_mode = st.checkbox("交互模式", value=True, help="逐轮确认修改建议")
        
        with col2:
            show_scores = st.checkbox("显示评分对比", value=True, help="显示润色前后的质量评分")
        
        # 润色按钮
        if st.button("🚀 开始润色", type="primary"):
            with st.spinner("正在润色论文..."):
                try:
                    # 创建润色器
                    polisher = MultiRoundPolisher()
                    
                    # 执行润色
                    result = polisher.polish_paper(paper_text, interactive=interactive_mode)
                    
                    if result.get('success', False):
                        # 显示润色结果
                        display_polishing_results(result, show_scores)
                    else:
                        st.error(f"❌ 润色失败: {result.get('error', '未知错误')}")
                        
                except Exception as e:
                    st.error(f"❌ 润色过程中出现错误: {str(e)}")

def display_polishing_results(result, show_scores):
    """显示润色结果"""
    st.markdown('<div class="section-header">✨ 润色结果</div>', unsafe_allow_html=True)
    
    # 评分对比
    if show_scores and 'score_comparison' in result:
        display_score_comparison(result['score_comparison'])
    
    # 修改统计
    summary = result.get('polishing_summary', {})
    if summary:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("润色轮数", summary.get('total_rounds', 0))
        
        with col2:
            st.metric("应用修改", f"{summary.get('total_modifications_applied', 0)} 处")
        
        with col3:
            mode = "交互模式" if summary.get('interactive_mode') else "批量模式"
            st.metric("润色模式", mode)
    
    # 润色后的文本
    st.markdown('<div class="section-header">📄 润色后的论文</div>', unsafe_allow_html=True)
    
    polished_text = result.get('polished_text', '')
    st.text_area(
        "润色后的内容:",
        value=polished_text,
        height=400,
        key="polished_text"
    )
    
    # 下载按钮
    if polished_text:
        st.download_button(
            label="💾 下载润色结果",
            data=polished_text,
            file_name=f"polished_paper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )
    
    # 修改详情
    modification_history = result.get('modification_history', [])
    if modification_history:
        st.markdown('<div class="section-header">📝 修改详情</div>', unsafe_allow_html=True)
        
        for round_info in modification_history:
            with st.expander(f"第{round_info['round']}轮: {round_info['round_name']} ({round_info['modifications_applied']}处修改)"):
                st.text(f"修改数量: {round_info['modifications_applied']}")
                
                if 'user_choices' in round_info:
                    choices = round_info['user_choices']
                    st.text(f"接受的修改: {len(choices.get('accepted', []))}")
                    st.text(f"拒绝的修改: {len(choices.get('rejected', []))}")

def display_score_comparison(comparison):
    """显示评分对比"""
    st.markdown('<div class="section-header">📊 质量评分对比</div>', unsafe_allow_html=True)
    
    # 总体改进
    overall_improvement = comparison.get('overall_improvement', 0)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        before_score = comparison.get('before_scores', {}).get('overall_score', 0)
        st.metric("润色前总分", f"{before_score:.1f}")
    
    with col2:
        after_score = comparison.get('after_scores', {}).get('overall_score', 0)
        st.metric("润色后总分", f"{after_score:.1f}")
    
    with col3:
        st.metric("总体改进", f"+{overall_improvement:.1f}", delta=f"+{overall_improvement:.1f}")
    
    with col4:
        improvement_pct = comparison.get('overall_improvement_percentage', 0)
        st.metric("改进百分比", f"{improvement_pct:.1f}%")
    
    # 各维度改进
    st.markdown("### 各维度改进")
    
    dimensions = [
        ('style_improvement', '风格匹配度', '风格匹配'),
        ('academic_improvement', '学术规范性', '学术规范'),
        ('readability_improvement', '可读性', '可读性')
    ]
    
    improvements = []
    labels = []
    
    for key, name, short_name in dimensions:
        improvement = comparison.get(key, 0)
        improvements.append(improvement)
        labels.append(short_name)
    
    # 创建改进图表
    fig = go.Figure(data=[
        go.Bar(
            x=labels,
            y=improvements,
            marker_color=['#1f77b4' if x >= 0 else '#d62728' for x in improvements],
            text=[f"+{x:.1f}" if x >= 0 else f"{x:.1f}" for x in improvements],
            textposition='auto'
        )
    ])
    
    fig.update_layout(
        title="各维度改进情况",
        xaxis_title="评分维度",
        yaxis_title="改进分数",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

def quality_assessment_interface():
    """质量评估界面"""
    st.markdown('<div class="section-header">📊 质量评估</div>', unsafe_allow_html=True)
    
    # 输入文本
    assessment_text = st.text_area(
        "请输入要评估的论文内容:",
        height=300,
        placeholder="在此粘贴您的论文内容..."
    )
    
    if assessment_text and st.button("📊 开始评估", type="primary"):
        with st.spinner("正在评估论文质量..."):
            try:
                # 创建评分器
                scorer = QualityScorer()
                
                # 执行评分
                scores = scorer.score_paper(assessment_text)
                
                if 'error' not in scores:
                    display_quality_scores(scores)
                else:
                    st.error(f"❌ 评估失败: {scores['error']}")
                    
            except Exception as e:
                st.error(f"❌ 评估过程中出现错误: {str(e)}")

def display_quality_scores(scores):
    """显示质量评分"""
    st.markdown('<div class="section-header">📈 质量评分结果</div>', unsafe_allow_html=True)
    
    # 总体评分
    overall_score = scores.get('overall_score', 0)
    
    # 创建评分仪表盘
    fig = make_subplots(
        rows=2, cols=2,
        specs=[[{'type': 'indicator'}, {'type': 'indicator'}],
               [{'type': 'indicator'}, {'type': 'indicator'}]],
        subplot_titles=('总分', '风格匹配', '学术规范', '可读性')
    )
    
    # 总分
    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=overall_score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "总分"},
        gauge={'axis': {'range': [None, 100]},
               'bar': {'color': "darkblue"},
               'steps': [{'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 80], 'color': "yellow"},
                        {'range': [80, 100], 'color': "green"}],
               'threshold': {'line': {'color': "red", 'width': 4},
                           'thickness': 0.75, 'value': 90}}),
        row=1, col=1)
    
    # 各维度评分
    dimensions = [
        ('style_match', '风格匹配'),
        ('academic_standard', '学术规范'),
        ('readability', '可读性')
    ]
    
    positions = [(1, 2), (2, 1), (2, 2)]
    
    for i, (key, name) in enumerate(dimensions):
        dimension_score = scores.get(key, {}).get('score', 0)
        
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=dimension_score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': name},
            gauge={'axis': {'range': [None, 100]},
                   'bar': {'color': "darkblue"},
                   'steps': [{'range': [0, 50], 'color': "lightgray"},
                            {'range': [50, 80], 'color': "yellow"},
                            {'range': [80, 100], 'color': "green"}]}),
            row=positions[i][0], col=positions[i][1])
    
    fig.update_layout(height=600, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    
    # 详细分析
    detailed = scores.get('detailed_analysis', {})
    if detailed:
        st.markdown("### 📝 详细分析")
        
        # 基础统计
        basic_stats = detailed.get('basic_stats', {})
        if basic_stats:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("字数", basic_stats.get('word_count', 0))
            
            with col2:
                st.metric("句数", basic_stats.get('sentence_count', 0))
            
            with col3:
                st.metric("平均句长", f"{basic_stats.get('avg_words_per_sentence', 0):.1f} 词")
        
        # 风格分析
        style_analysis = detailed.get('style_analysis', {})
        if style_analysis:
            st.markdown("#### 🎯 风格分析")
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("匹配规则数", style_analysis.get('matched_rules', 0))
                st.metric("核心规则匹配", style_analysis.get('core_rules_matched', 0))
            
            with col2:
                st.write("**主要优点:**")
                for strength in style_analysis.get('top_strengths', []):
                    st.write(f"• {strength}")
        
        # 可读性分析
        readability_analysis = detailed.get('readability_analysis', {})
        if readability_analysis:
            st.markdown("#### 📖 可读性分析")
            
            read_scores = [
                readability_analysis.get('sentence_complexity', 0),
                readability_analysis.get('vocabulary_diversity', 0),
                readability_analysis.get('transition_usage', 0)
            ]
            read_labels = ['句式复杂度', '词汇多样性', '过渡词使用']
            
            fig = px.bar(
                x=read_labels,
                y=read_scores,
                title="可读性各维度评分",
                labels={'x': '维度', 'y': '分数'}
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # 改进建议
    recommendations = scores.get('recommendations', [])
    if recommendations:
        st.markdown("### 💡 改进建议")
        for i, rec in enumerate(recommendations, 1):
            st.write(f"{i}. {rec}")

def style_guide_interface():
    """风格指南界面"""
    st.markdown('<div class="section-header">📖 风格指南</div>', unsafe_allow_html=True)
    
    # 检查风格指南是否存在
    if not Path(Config.STYLE_GUIDE_JSON).exists():
        st.warning("⚠️ 风格指南不存在，请先运行分析命令")
        st.code("python main.py analyze")
        return
    
    try:
        # 加载风格指南
        with open(Config.STYLE_GUIDE_JSON, 'r', encoding='utf-8') as f:
            guide = json.load(f)
        
        # 指南摘要
        st.markdown("### 📊 指南摘要")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("总规则数", len(guide.get('rules', [])))
        
        with col2:
            core_rules = len([r for r in guide.get('rules', []) if r.get('rule_type') == 'core'])
            st.metric("核心规则", core_rules)
        
        with col3:
            optional_rules = len([r for r in guide.get('rules', []) if r.get('rule_type') == 'optional'])
            st.metric("可选规则", optional_rules)
        
        with col4:
            st.metric("分析论文数", guide.get('total_papers_analyzed', 0))
        
        # 规则类别分布
        categories = guide.get('categories', {})
        if categories:
            st.markdown("### 📂 规则类别分布")
            
            category_names = list(categories.keys())
            category_counts = [len(rules) for rules in categories.values()]
            
            fig = px.pie(
                values=category_counts,
                names=category_names,
                title="规则类别分布"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # 核心规则
        core_rules = [r for r in guide.get('rules', []) if r.get('rule_type') == 'core']
        if core_rules:
            st.markdown("### 🎯 核心规则")
            
            for i, rule in enumerate(core_rules[:10], 1):  # 显示前10条
                with st.expander(f"{i}. {rule.get('description', '')}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**类型**: {rule.get('rule_type', '')}")
                        st.write(f"**类别**: {rule.get('category', '')}")
                        st.write(f"**遵循率**: {rule.get('frequency', 0):.1%}")
                    
                    with col2:
                        st.write(f"**规则ID**: `{rule.get('rule_id', '')}`")
                        
                        # 显示示例
                        examples = rule.get('examples', [])
                        if examples:
                            st.write("**示例**:")
                            for example in examples[:2]:  # 显示前2个示例
                                if 'before' in example and 'after' in example:
                                    st.write(f"• 原文: {example['before']}")
                                    st.write(f"• 修改: {example['after']}")
        
        # 下载风格指南
        st.markdown("### 💾 下载风格指南")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("下载JSON版本"):
                with open(Config.STYLE_GUIDE_JSON, 'r', encoding='utf-8') as f:
                    json_data = f.read()
                st.download_button(
                    label="下载JSON",
                    data=json_data,
                    file_name="style_guide.json",
                    mime="application/json"
                )
        
        with col2:
            if st.button("下载Markdown版本") and Path(Config.STYLE_GUIDE_MD).exists():
                with open(Config.STYLE_GUIDE_MD, 'r', encoding='utf-8') as f:
                    md_data = f.read()
                st.download_button(
                    label="下载Markdown",
                    data=md_data,
                    file_name="style_guide.md",
                    mime="text/markdown"
                )
        
    except Exception as e:
        st.error(f"❌ 加载风格指南失败: {str(e)}")

def system_status_interface():
    """系统状态界面"""
    st.markdown('<div class="section-header">⚙️ 系统状态</div>', unsafe_allow_html=True)
    
    # 配置状态
    st.markdown("### 🔧 配置状态")
    
    try:
        Config.validate()
        st.success("✅ 配置验证通过")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**批次大小**: {Config.BATCH_SIZE}")
            st.write(f"**最大论文数**: {Config.MAX_PAPERS}")
            st.write(f"**相似度阈值**: {Config.SIMILARITY_THRESHOLD}")
        
        with col2:
            st.write(f"**核心规则阈值**: {Config.CORE_RULE_THRESHOLD}")
            st.write(f"**可选规则阈值**: {Config.OPTIONAL_RULE_THRESHOLD}")
            st.write(f"**OpenAI模型**: {Config.OPENAI_MODEL}")
        
    except Exception as e:
        st.error(f"❌ 配置错误: {str(e)}")
    
    # 数据目录状态
    st.markdown("### 📁 数据目录状态")
    
    data_dirs = [
        ("期刊PDF", Config.JOURNALS_DIR),
        ("提取文本", Config.EXTRACTED_DIR),
        ("单篇报告", Config.INDIVIDUAL_REPORTS_DIR),
        ("批次汇总", Config.BATCH_SUMMARIES_DIR)
    ]
    
    for name, dir_path in data_dirs:
        if Path(dir_path).exists():
            file_count = len(list(Path(dir_path).glob('*')))
            st.success(f"✅ {name}: {file_count} 个文件")
        else:
            st.warning(f"⚠️ {name}: 目录不存在")
    
    # 文件状态
    st.markdown("### 📄 重要文件状态")
    
    important_files = [
        ("风格指南JSON", Config.STYLE_GUIDE_JSON),
        ("风格指南MD", Config.STYLE_GUIDE_MD),
        ("分析日志", Config.ANALYSIS_LOG)
    ]
    
    for name, file_path in important_files:
        if Path(file_path).exists():
            file_size = Path(file_path).stat().st_size
            st.success(f"✅ {name}: {file_size:,} 字节")
        else:
            st.warning(f"⚠️ {name}: 文件不存在")
    
    # 系统信息
    st.markdown("### 💻 系统信息")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Python版本**: {sys.version.split()[0]}")
        st.write(f"**操作系统**: {os.name}")
    
    with col2:
        st.write(f"**Streamlit版本**: {st.__version__}")
        st.write(f"**工作目录**: {os.getcwd()}")

if __name__ == "__main__":
    main()
