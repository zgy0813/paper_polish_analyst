#!/usr/bin/env python3
"""
结构化AI输出使用示例
演示如何使用Pydantic模型进行结构化AI输出
"""

import sys
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.ai_client import call_ai_structured_simple

# 定义Pydantic模型
class PaperSummary(BaseModel):
    """论文摘要模型"""
    title: str = Field(description="论文标题")
    main_contribution: str = Field(description="主要贡献")
    methodology: str = Field(description="研究方法")
    key_findings: List[str] = Field(description="关键发现")
    limitations: List[str] = Field(description="研究局限性")
    future_directions: List[str] = Field(description="未来研究方向")
    quality_score: float = Field(ge=0, le=10, description="质量评分")

def main():
    """主函数"""
    print("🚀 结构化AI输出示例")
    print("=" * 50)
    
    # 示例1：论文摘要分析
    print("\n📄 示例1：论文摘要分析")
    try:
        result = call_ai_structured_simple(
            prompt="""
            请分析以下论文摘要，并以JSON格式返回分析结果：
            
            论文摘要：
            "This paper presents a novel deep learning approach for natural language processing. 
            We propose a transformer-based architecture that achieves state-of-the-art performance 
            on multiple benchmark datasets. Our method combines attention mechanisms with 
            reinforcement learning to improve text understanding. Experimental results show 
            15% improvement over existing methods. However, the approach requires significant 
            computational resources and may not generalize well to low-resource languages."
            
            请严格按照以下JSON格式返回（注意：JSON的key必须是英文，value可以是中文）：
            {
                "title": "论文标题",
                "main_contribution": "主要贡献",
                "methodology": "研究方法",
                "key_findings": ["关键发现列表"],
                "limitations": ["研究局限性列表"],
                "future_directions": ["未来研究方向列表"],
                "quality_score": 8.5
            }
            """,
            response_model=PaperSummary,
            system_message="你是一个学术论文分析专家，请严格按照JSON格式返回分析结果，JSON的key必须是英文，value可以是中文。",
            task_name="论文摘要分析"
        )
        

        print(result)
        print("✅ 分析成功！")
        print(f"   标题: {result.title}")
        print(f"   主要贡献: {result.main_contribution}")
        print(f"   研究方法: {result.methodology}")
        print(f"   关键发现: {result.key_findings}")
        print(f"   局限性: {result.limitations}")
        print(f"   未来方向: {result.future_directions}")
        print(f"   质量评分: {result.quality_score}")
        
    except Exception as e:
        print(f"❌ 分析失败: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🎉 示例完成！")

if __name__ == "__main__":
    main()
