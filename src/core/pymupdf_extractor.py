"""
PyMuPDF PDF文本提取器

基于PyMuPDF的简化PDF文本提取器，提供更好的双栏布局处理。
"""

import fitz
import re
from pathlib import Path
from typing import Dict, List, Any

from ..utils.logger_config import get_logger

logger = get_logger(__name__)


class PyMuPDFExtractor:
    """PyMuPDF PDF文本提取器"""

    def __init__(self, input_dir: str, output_dir: str):
        """
        初始化提取器

        Args:
            input_dir: PDF文件输入目录
            output_dir: 提取文本输出目录
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def extract_all_pdfs(self) -> Dict[str, Any]:
        """
        提取所有PDF文件的文本

        Returns:
            提取结果统计
        """
        pdf_files = list(self.input_dir.glob("*.pdf"))

        if not pdf_files:
            logger.warning(f"在 {self.input_dir} 中没有找到PDF文件")
            return {
                "success": False,
                "message": "没有找到PDF文件",
                "total_files": 0,
                "successful_extractions": 0,
                "failed_extractions": 0,
            }

        logger.info(f"找到 {len(pdf_files)} 个PDF文件")

        results = {
            "success": True,
            "total_files": len(pdf_files),
            "successful_extractions": 0,
            "failed_extractions": 0,
            "total_characters": 0,
            "extraction_details": [],
        }

        for pdf_file in pdf_files:
            try:
                logger.info(f"正在提取: {pdf_file.name}")
                result = self.extract_single_pdf(pdf_file)

                if result["success"]:
                    results["successful_extractions"] += 1
                    results["total_characters"] += result.get("character_count", 0)
                    logger.info(
                        f"成功提取: {pdf_file.name} ({result.get('character_count', 0)} 字符)"
                    )
                else:
                    results["failed_extractions"] += 1
                    logger.error(
                        f"提取失败: {pdf_file.name} - {result.get('error', '未知错误')}"
                    )

                results["extraction_details"].append(
                    {
                        "filename": pdf_file.name,
                        "success": result["success"],
                        "character_count": result.get("character_count", 0),
                        "error": result.get("error", None),
                    }
                )

            except Exception as e:
                results["failed_extractions"] += 1
                logger.error(f"提取 {pdf_file.name} 时出现异常: {str(e)}")
                results["extraction_details"].append(
                    {
                        "filename": pdf_file.name,
                        "success": False,
                        "character_count": 0,
                        "error": str(e),
                    }
                )

        logger.info(
            f"提取完成: 成功 {results['successful_extractions']}, 失败 {results['failed_extractions']}"
        )
        return results

    def extract_single_pdf(self, pdf_path: Path) -> Dict[str, Any]:
        """
        提取单个PDF文件的文本

        Args:
            pdf_path: PDF文件路径

        Returns:
            提取结果
        """
        try:
            # 打开PDF文件
            doc = fitz.open(str(pdf_path))

            all_text = []
            layout_info = {"total_pages": len(doc), "pages": {}, "is_two_column": False}

            for page_num in range(len(doc)):
                page = doc[page_num]

                # 获取页面文本字典
                text_dict = page.get_text("dict")

                # 提取文本块
                text_blocks = []
                for block in text_dict["blocks"]:
                    if "lines" in block:
                        for line in block["lines"]:
                            for span in line["spans"]:
                                if span["text"].strip():
                                    text_blocks.append(
                                        {
                                            "text": span["text"],
                                            "bbox": span["bbox"],
                                            "font_size": span["size"],
                                            "is_bold": span["flags"] & 2**4 > 0,
                                        }
                                    )

                # 分析页面布局
                page_layout = self._analyze_page_layout(text_blocks)
                layout_info["pages"][page_num] = page_layout

                # 重组文本
                page_text = self._reorganize_page_text(text_blocks, page_layout)
                all_text.append(page_text)

            # 检查整体是否为双栏布局
            two_column_pages = sum(
                1
                for page in layout_info["pages"].values()
                if page.get("is_two_column", False)
            )
            layout_info["is_two_column"] = two_column_pages > len(doc) * 0.5

            # 合并所有页面文本
            full_text = "\n\n".join(all_text)

            # 清理文本
            cleaned_text = self._clean_text(full_text)

            # 保存结果
            output_filename = pdf_path.stem + ".txt"
            output_path = self.output_dir / output_filename

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(cleaned_text)

            # 在关闭文档前保存页面数
            page_count = len(doc)
            doc.close()

            return {
                "success": True,
                "character_count": len(cleaned_text),
                "page_count": page_count,
                "layout_info": layout_info,
            }

        except Exception as e:
            logger.error(f"提取PDF失败: {str(e)}")
            return {"success": False, "error": str(e)}

    def _analyze_page_layout(self, text_blocks: List[Dict]) -> Dict:
        """
        分析页面布局

        Args:
            text_blocks: 文本块列表

        Returns:
            布局分析结果
        """
        if not text_blocks:
            return {"is_two_column": False, "columns": 0}

        # 计算页面边界
        x_coords = [b["bbox"][0] for b in text_blocks] + [
            b["bbox"][2] for b in text_blocks
        ]
        page_left = min(x_coords)
        page_right = max(x_coords)
        page_width = page_right - page_left
        page_center = page_left + page_width / 2

        # 检测列
        left_blocks = [b for b in text_blocks if b["bbox"][0] < page_center]
        right_blocks = [b for b in text_blocks if b["bbox"][0] >= page_center]

        # 判断是否为双栏
        is_two_column = False
        if left_blocks and right_blocks:
            left_right = max(b["bbox"][2] for b in left_blocks)
            right_left = min(b["bbox"][0] for b in right_blocks)
            gap = right_left - left_right
            avg_width = (left_right - page_left + page_right - right_left) / 2
            is_two_column = gap > avg_width * 0.2

        return {
            "is_two_column": is_two_column,
            "columns": 2 if is_two_column else 1,
            "left_blocks": len(left_blocks),
            "right_blocks": len(right_blocks),
            "total_blocks": len(text_blocks),
        }

    def _reorganize_page_text(self, text_blocks: List[Dict], layout: Dict) -> str:
        """
        重组页面文本

        Args:
            text_blocks: 文本块列表
            layout: 布局信息

        Returns:
            重组后的文本
        """
        if not text_blocks:
            return ""

        if layout.get("is_two_column", False):
            # 双栏布局：按列重组
            page_center = sum(b["bbox"][0] for b in text_blocks) / len(
                text_blocks
            ) + sum(b["bbox"][2] for b in text_blocks) / len(text_blocks)
            page_center /= 2

            left_blocks = [b for b in text_blocks if b["bbox"][0] < page_center]
            right_blocks = [b for b in text_blocks if b["bbox"][0] >= page_center]

            # 按y坐标排序
            left_blocks.sort(key=lambda b: b["bbox"][1])
            right_blocks.sort(key=lambda b: b["bbox"][1])

            # 合并两栏
            left_text = " ".join(b["text"] for b in left_blocks)
            right_text = " ".join(b["text"] for b in right_blocks)

            # 简单的段落合并
            left_paras = [p.strip() for p in left_text.split(".") if p.strip()]
            right_paras = [p.strip() for p in right_text.split(".") if p.strip()]

            # 交替合并段落
            merged_paras = []
            max_paras = max(len(left_paras), len(right_paras))
            for i in range(max_paras):
                if i < len(left_paras):
                    merged_paras.append(left_paras[i])
                if i < len(right_paras):
                    merged_paras.append(right_paras[i])

            return ". ".join(merged_paras)
        else:
            # 单栏布局：按y坐标排序
            text_blocks.sort(key=lambda b: b["bbox"][1])
            return " ".join(b["text"] for b in text_blocks)

    def _clean_text(self, text: str) -> str:
        """
        清理文本

        Args:
            text: 原始文本

        Returns:
            清理后的文本
        """
        # 移除页眉页脚
        lines = text.split("\n")
        cleaned_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 跳过页码
            if re.match(r"^\d+$", line):
                continue

            # 跳过期刊信息
            if re.match(r"^Journal of.*$", line):
                continue

            # 跳过版权信息
            if re.match(r"^Copyright.*$", line):
                continue

            # 跳过DOI
            if re.match(r"^https?://.*$", line):
                continue

            cleaned_lines.append(line)

        # 修复连字符
        text = "\n".join(cleaned_lines)
        text = re.sub(r"-\s*\n\s*", "", text)

        # 修复粘词
        text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
        text = re.sub(r"(\d)([A-Za-z])", r"\1 \2", text)
        text = re.sub(r"([A-Za-z])(\d)", r"\1 \2", text)

        # 标准化空白字符
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r" +\n", "\n", text)
        text = re.sub(r"\n +", "\n", text)

        return text

    def get_extracted_texts(self) -> List[tuple]:
        """
        获取所有已提取的文本文件

        Returns:
            文本文件列表，每个元素为(文件名, 文本内容)的元组
        """
        txt_files = list(self.output_dir.glob("*.txt"))
        texts = []

        for file_path in txt_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    # 使用文件名（不含扩展名）作为ID
                    file_id = file_path.stem
                    texts.append((file_id, content))
            except Exception as e:
                logger.warning(f"读取文件失败 {file_path}: {str(e)}")

        return texts

    def get_extraction_summary(self) -> Dict[str, Any]:
        """
        获取提取结果摘要

        Returns:
            提取摘要
        """
        txt_files = list(self.output_dir.glob("*.txt"))

        total_characters = 0
        for file_path in txt_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    total_characters += len(content)
            except Exception as e:
                logger.warning(f"读取文件失败 {file_path}: {str(e)}")

        return {
            "total_files": len(txt_files),
            "successful_extractions": len(txt_files),
            "total_characters": total_characters,
            "output_directory": str(self.output_dir),
        }
