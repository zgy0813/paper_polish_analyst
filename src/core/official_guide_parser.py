"""
官方风格指南解析器

从期刊官方style guide PDF中提取规则，并使用AI解析成标准JSON格式。
"""

import json
from typing import Dict, List
from pathlib import Path

from .pymupdf_extractor import PyMuPDFExtractor
from .prompts import PromptTemplates
from .ai_client import get_ai_client, AICallError
from config import Config

# 设置日志
from ..utils.logger_config import get_logger

logger = get_logger(__name__)


class OfficialGuideParser:
    """官方风格指南解析器"""

    def __init__(self):
        """初始化解析器"""
        self.pdf_extractor = PyMuPDFExtractor("", "")  # 不需要特定目录
        self.prompts = PromptTemplates()

        # 缓存文件路径
        self.cache_file = Path("data/official_guides/official_rules_cache.json")

        # 初始化AI客户端
        try:
            self.ai_client = get_ai_client()
            self.ai_config = Config.get_ai_config()
        except Exception as e:
            logger.error(f"初始化AI客户端失败: {str(e)}")
            self.ai_client = None
            self.ai_config = None

    def parse_official_guide(self, pdf_path: str, force_refresh: bool = False) -> Dict:
        """
        解析官方风格指南PDF（支持缓存）

        Args:
            pdf_path: 官方style guide PDF文件路径
            force_refresh: 是否强制刷新缓存

        Returns:
            解析结果字典
        """
        logger.info(f"开始解析官方风格指南: {pdf_path}")

        try:
            # 1. 检查缓存文件是否存在
            if not force_refresh and self.cache_file.exists():
                logger.info("发现官方规则缓存文件，直接加载...")
                cached_result = self._load_from_cache()
                if cached_result:
                    logger.info(
                        f"从缓存加载官方规则，共 {cached_result.get('total_rules', 0)} 条规则"
                    )
                    return cached_result
                else:
                    logger.warning("缓存文件损坏，将重新解析...")

            # 2. 提取PDF文本
            pdf_file = Path(pdf_path)
            if not pdf_file.exists():
                return {"error": f"PDF文件不存在: {pdf_path}"}

            # 使用现有的extract_single_pdf方法
            result = self.pdf_extractor.extract_single_pdf(pdf_file)

            if not result.get("success"):
                return {"error": "PDF文本提取失败"}

            # 读取提取的文本文件
            output_filename = pdf_file.stem + ".txt"
            output_path = self.pdf_extractor.output_dir / output_filename

            if not output_path.exists():
                return {"error": "提取的文本文件不存在"}

            with open(output_path, "r", encoding="utf-8") as f:
                text = f.read()

            # 构建元数据
            metadata = {
                "extraction_success": result.get("success", False),
                "total_characters": result.get("character_count", 0),
                "page_count": result.get("page_count", 0),
                "layout_info": result.get("layout_info", {}),
            }

            logger.info(f"成功提取文本，共 {metadata.get('total_characters', 0)} 字符")

            # 3. 使用AI解析规则
            if not self.client:
                return {"error": "AI客户端未初始化，无法解析规则"}

            rules = self._extract_rules_with_ai(text)

            if not rules:
                return {"error": "未能从官方指南中提取到规则"}

            # 4. 结构化规则
            structured_rules = self._structure_rules(rules)

            # 5. 生成解析报告
            result = {
                "success": True,
                "source_file": pdf_path,
                "extraction_metadata": metadata,
                "total_rules": len(structured_rules),
                "rules": structured_rules,
                "categories": self._categorize_rules(structured_rules),
                "parsing_date": self._get_current_timestamp(),
            }

            # 6. 保存到缓存
            self._save_to_cache(result)

            logger.info(f"成功解析官方指南，提取 {len(structured_rules)} 条规则")
            return result

        except Exception as e:
            logger.error(f"解析官方指南失败: {str(e)}")
            return {"error": str(e)}

    def _extract_rules_with_ai(self, text: str) -> List[Dict]:
        """
        使用AI从官方指南中提取规则

        Args:
            text: 官方指南文本内容

        Returns:
            提取的规则列表
        """
        try:
            # 使用完整文本进行解析

            # 获取解析prompt
            prompt = self.prompts.format_prompt(
                self.prompts.get_official_guide_parsing_prompt(), style_guide_text=text
            )

            # 记录AI请求参数
            request_params = {
                "model": self.ai_config["model"],
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": self.ai_config["max_tokens"],
                "temperature": self.ai_config["temperature"],
            }
            logger.info(f"官方指南解析AI请求参数: {request_params}")
            logger.info(f"官方指南解析Prompt长度: {len(prompt)} 字符")

            # 调用AI API
            try:
                response_content = self.ai_client.call_ai(
                    prompt=prompt,
                    system_message="你是一个专业的学术写作风格分析专家。",
                    task_name="官方指南解析",
                    max_tokens=self.ai_config["max_tokens"],
                    temperature=self.ai_config["temperature"]
                )
            except AICallError as e:
                logger.error(f"AI调用失败: {str(e)}")
                return []

            # 解析AI响应
            result = self._parse_ai_response(response_content)

            if "rules" in result:
                return result["rules"]
            else:
                logger.error(f"AI响应格式错误: {result}")
                return []

        except Exception as e:
            logger.error(f"AI提取规则失败: {str(e)}")
            return []

    def _parse_ai_response(self, response_text: str) -> Dict:
        """
        解析AI响应

        Args:
            response_text: AI响应文本

        Returns:
            解析后的结果
        """
        try:
            # 尝试提取JSON部分
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            else:
                # 如果没有代码块标记，尝试找到JSON开始和结束
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                json_text = response_text[json_start:json_end]

            return json.loads(json_text)

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"解析AI响应失败: {str(e)}")
            logger.error(f"响应文本: {response_text[:500]}...")
            return {"error": str(e)}

    def _structure_rules(self, rules: List[Dict]) -> List[Dict]:
        """
        结构化规则

        Args:
            rules: 原始规则列表

        Returns:
            结构化后的规则列表
        """
        structured_rules = []

        for i, rule in enumerate(rules, 1):
            try:
                # 确保必要字段存在
                structured_rule = {
                    "rule_id": rule.get("rule_id", f"official-rule-{i:03d}"),
                    "rule_type": "official",
                    "priority": self._determine_priority(rule.get("description", "")),
                    "category": rule.get("category", "其他"),
                    "description": rule.get("description", ""),
                    "source": "official_guide",
                    "examples": rule.get("examples", []),
                    "requirements": rule.get("requirements", []),
                    "prohibitions": rule.get("prohibitions", []),
                    "context": rule.get("context", ""),
                    "section": rule.get("section", ""),
                    "page_reference": rule.get("page_reference", ""),
                    "confidence": rule.get("confidence", 0.8),
                }

                structured_rules.append(structured_rule)

            except Exception as e:
                logger.warning(f"结构化规则失败 {i}: {str(e)}")
                continue

        return structured_rules

    def _determine_priority(self, rule_text: str) -> str:
        """
        判断规则优先级

        Args:
            rule_text: 规则描述文本

        Returns:
            优先级字符串
        """
        rule_lower = rule_text.lower()

        # 高优先级关键词
        high_priority_keywords = [
            "must",
            "required",
            "mandatory",
            "shall",
            "always",
            "never",
        ]
        # 中优先级关键词
        medium_priority_keywords = [
            "should",
            "recommended",
            "preferred",
            "typically",
            "usually",
        ]
        # 低优先级关键词
        low_priority_keywords = ["may", "can", "optional", "sometimes", "occasionally"]

        if any(keyword in rule_lower for keyword in high_priority_keywords):
            return "highest"
        elif any(keyword in rule_lower for keyword in medium_priority_keywords):
            return "high"
        elif any(keyword in rule_lower for keyword in low_priority_keywords):
            return "medium"
        else:
            return "high"  # 默认为高优先级

    def _categorize_rules(self, rules: List[Dict]) -> Dict[str, List[Dict]]:
        """
        对规则进行分类

        Args:
            rules: 规则列表

        Returns:
            按类别分组的规则字典
        """
        categories = {}

        for rule in rules:
            category = rule.get("category", "其他")
            if category not in categories:
                categories[category] = []
            categories[category].append(rule)

        return categories

    def _get_current_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime

        return datetime.now().isoformat()

    def save_official_rules(self, rules_data: Dict, output_path: str = None):
        """
        保存官方规则到文件

        Args:
            rules_data: 规则数据
            output_path: 输出文件路径
        """
        if not output_path:
            output_path = "data/official_guides/official_rules.json"

        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(rules_data, f, ensure_ascii=False, indent=2)

            logger.info(f"官方规则已保存到: {output_path}")

        except Exception as e:
            logger.error(f"保存官方规则失败: {str(e)}")

    def _load_from_cache(self) -> Dict:
        """
        从缓存加载官方规则

        Returns:
            缓存的解析结果或None
        """
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                cache_data = json.load(f)

            # 检查缓存数据是否有效
            if cache_data.get("success") and cache_data.get("rules"):
                logger.info("缓存文件有效，加载成功")
                return cache_data
            else:
                logger.warning("缓存文件数据无效")
                return None

        except Exception as e:
            logger.warning(f"加载缓存失败: {str(e)}")
            return None

    def _save_to_cache(self, result: Dict):
        """
        保存解析结果到缓存

        Args:
            result: 解析结果
        """
        try:
            # 确保目录存在
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)

            # 添加缓存时间戳
            result["cached_at"] = self._get_current_timestamp()

            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            logger.info(f"官方规则已缓存到: {self.cache_file}")

        except Exception as e:
            logger.error(f"保存缓存失败: {str(e)}")

    def clear_cache(self):
        """清除缓存"""
        try:
            if self.cache_file.exists():
                self.cache_file.unlink()
                logger.info("缓存已清除")
        except Exception as e:
            logger.error(f"清除缓存失败: {str(e)}")

    def has_cache(self) -> bool:
        """检查是否存在有效的缓存文件"""
        return self.cache_file.exists()


def main():
    """测试官方指南解析功能"""
    parser = OfficialGuideParser()

    # 测试解析
    result = parser.parse_official_guide("AMJ_style_guide.pdf")

    if result.get("success"):
        print("解析成功!")
        print(f"提取规则数: {result.get('total_rules', 0)}")
        print(f"规则类别: {list(result.get('categories', {}).keys())}")

        # 保存结果
        parser.save_official_rules(result)
    else:
        print(f"解析失败: {result.get('error')}")


if __name__ == "__main__":
    main()
