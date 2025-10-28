"""
AI客户端管理模块
统一管理AI API调用、日志记录和错误处理
"""
import json
import time
from typing import Dict, List, Any, Optional, Union, Type, TypeVar
from openai import OpenAI
from openai.types.chat import ChatCompletion
from pydantic import BaseModel

from config import Config
from ..utils.logger_config import get_logger

T = TypeVar('T', bound=BaseModel)

logger = get_logger(__name__)


class AIClient:
    """统一的AI客户端管理类"""
    
    def __init__(self):
        """初始化AI客户端"""
        self.ai_config = Config.get_ai_config()
        self.client = OpenAI(
            api_key=self.ai_config['api_key'],
            base_url=self.ai_config['base_url']
        )
        self._call_count = 0
        self._total_tokens = 0
    
    def call_ai(
        self,
        prompt: str,
        system_message: str = "你是一个专业的学术写作专家。",
        task_name: str = "AI分析",
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        统一的AI调用方法
        
        Args:
            prompt: 用户提示词
            system_message: 系统消息
            task_name: 任务名称（用于日志标识）
            max_tokens: 最大token数，None时使用配置默认值
            temperature: 温度参数，None时使用配置默认值
            additional_params: 额外的API参数
            
        Returns:
            AI响应的文本内容
            
        Raises:
            AICallError: AI调用失败时抛出
        """
        try:
            # 准备API参数（只包含OpenAI API支持的参数）
            api_params = {
                "model": self.ai_config["model"],
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens or self.ai_config["max_tokens"],
                "temperature": temperature or self.ai_config["temperature"]
            }
            
            # 添加OpenAI API支持的额外参数
            if additional_params:
                # 只添加OpenAI API支持的参数
                openai_supported_params = {
                    'top_p', 'frequency_penalty', 'presence_penalty', 'stop', 
                    'stream', 'logit_bias', 'user', 'response_format'
                }
                for key, value in additional_params.items():
                    if key in openai_supported_params:
                        api_params[key] = value
            
            # 记录调用前日志（包含所有参数用于调试）
            log_params = api_params.copy()
            if additional_params:
                log_params['custom_params'] = additional_params
            self._log_ai_input(task_name, prompt, log_params)
            
            # 调用AI API
            start_time = time.time()
            response = self.client.chat.completions.create(**api_params)
            end_time = time.time()
            
            # 解析响应
            response_text = response.choices[0].message.content
            
            # 更新统计信息
            self._call_count += 1
            if hasattr(response, 'usage') and response.usage:
                self._total_tokens += response.usage.total_tokens
            
            # 记录调用后日志
            self._log_ai_output(task_name, response_text, response, end_time - start_time)
            
            return response_text
            
        except Exception as e:
            logger.error(f"AI调用失败 - {task_name}: {str(e)}")
            raise AICallError(f"AI调用失败 - {task_name}: {str(e)}")
    
    def call_ai_json(
        self,
        prompt: str,
        system_message: str = "你是一个专业的学术写作专家。请以JSON格式返回结果。",
        task_name: str = "AI分析",
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        调用AI并解析JSON响应
        
        Args:
            prompt: 用户提示词
            system_message: 系统消息
            task_name: 任务名称（用于日志标识）
            max_tokens: 最大token数
            temperature: 温度参数
            additional_params: 额外的API参数
            
        Returns:
            解析后的JSON数据
            
        Raises:
            AICallError: AI调用失败时抛出
            JSONDecodeError: JSON解析失败时抛出
        """
        try:
            response_text = self.call_ai(
                prompt=prompt,
                system_message=system_message,
                task_name=task_name,
                max_tokens=max_tokens,
                temperature=temperature,
                additional_params=additional_params
            )
            
            # 清理响应文本，移除markdown代码块标记
            cleaned_text = response_text.strip()
            if cleaned_text.startswith('```json'):
                cleaned_text = cleaned_text[7:]  # 移除 ```json
            if cleaned_text.startswith('```'):
                cleaned_text = cleaned_text[3:]  # 移除 ```
            if cleaned_text.endswith('```'):
                cleaned_text = cleaned_text[:-3]  # 移除结尾的 ```
            cleaned_text = cleaned_text.strip()
            
            # 解析JSON响应
            result = json.loads(cleaned_text)
            logger.info(f"JSON解析成功 - {task_name}: 解析了 {len(str(result))} 字符的JSON数据")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败 - {task_name}: {str(e)}")
            logger.error(f"原始响应内容: {response_text[:500]}...")
            raise
        except Exception as e:
            logger.error(f"AI JSON调用失败 - {task_name}: {str(e)}")
            raise AICallError(f"AI JSON调用失败 - {task_name}: {str(e)}")
    
    def call_ai_with_retry(
        self,
        prompt: str,
        system_message: str = "你是一个专业的学术写作专家。",
        task_name: str = "AI分析",
        max_retries: int = 3,
        retry_delay: float = 1.0,
        **kwargs
    ) -> str:
        """
        带重试机制的AI调用
        
        Args:
            prompt: 用户提示词
            system_message: 系统消息
            task_name: 任务名称
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
            **kwargs: 其他参数传递给call_ai
            
        Returns:
            AI响应的文本内容
        """
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return self.call_ai(
                    prompt=prompt,
                    system_message=system_message,
                    task_name=f"{task_name} (尝试 {attempt + 1}/{max_retries + 1})",
                    **kwargs
                )
            except Exception as e:
                last_exception = e
                if attempt < max_retries:
                    logger.warning(f"AI调用失败，{retry_delay}秒后重试 - {task_name}: {str(e)}")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # 指数退避
                else:
                    logger.error(f"AI调用最终失败 - {task_name}: {str(e)}")
        
        raise AICallError(f"AI调用重试失败 - {task_name}: {str(last_exception)}")
    
    def call_ai_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_message: str = "你是一个专业的学术写作专家。请严格按照JSON格式返回结果，JSON的key必须是英文，value可以是中文。",
        task_name: str = "AI结构化分析",
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> T:
        """
        调用AI并返回结构化输出
        
        Args:
            prompt: 用户提示词
            response_model: Pydantic模型类，定义期望的输出结构
            system_message: 系统消息
            task_name: 任务名称（用于日志标识）
            max_tokens: 最大token数，None时使用配置默认值
            temperature: 温度参数，None时使用配置默认值
            additional_params: 额外的API参数
            
        Returns:
            解析后的Pydantic模型实例
            
        Raises:
            AICallError: AI调用失败时抛出
            ValidationError: 模型验证失败时抛出
        """
        try:
            # 准备API参数（只包含OpenAI API支持的参数）
            api_params = {
                "model": self.ai_config["model"],
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens or self.ai_config["max_tokens"],
                "temperature": temperature or self.ai_config["temperature"]
            }
            
            # 添加OpenAI API支持的额外参数
            if additional_params:
                # 只添加OpenAI API支持的参数
                openai_supported_params = {
                    'top_p', 'frequency_penalty', 'presence_penalty', 'stop', 
                    'stream', 'logit_bias', 'user', 'response_format'
                }
                for key, value in additional_params.items():
                    if key in openai_supported_params:
                        api_params[key] = value

            # 记录调用前日志（包含所有参数用于调试）
            log_params = api_params.copy()
            if additional_params:
                log_params['custom_params'] = additional_params
            self._log_ai_input(task_name, prompt, log_params)
            logger.info(f"期望输出模型: {response_model.__name__}")
            
            # 调用AI API
            start_time = time.time()
            response = self.client.chat.completions.create(**api_params)
            end_time = time.time()
            
            # 解析响应
            response_text = response.choices[0].message.content
            
            # 更新统计信息
            self._call_count += 1
            if hasattr(response, 'usage') and response.usage:
                self._total_tokens += response.usage.total_tokens
            
            # 记录调用后日志
            self._log_ai_output(task_name, response_text, response, end_time - start_time)
            
            # 解析为结构化输出
            try:
                # 清理响应文本，移除markdown代码块标记
                cleaned_text = response_text.strip()
                if cleaned_text.startswith('```json'):
                    cleaned_text = cleaned_text[7:]  # 移除 ```json
                if cleaned_text.startswith('```'):
                    cleaned_text = cleaned_text[3:]  # 移除 ```
                if cleaned_text.endswith('```'):
                    cleaned_text = cleaned_text[:-3]  # 移除结尾的 ```
                cleaned_text = cleaned_text.strip()
                
                # 解析JSON
                json_data = json.loads(cleaned_text)
    
                # 尝试直接创建模型实例
                try:
                    structured_result = response_model(**json_data)
                except Exception as e:
                    # 如果直接创建失败，尝试字段映射
                    logger.warning(f"直接模型创建失败，尝试字段映射: {str(e)}")
                    mapped_data = self._map_json_fields(json_data, response_model)
                    structured_result = response_model(**mapped_data)
                
                logger.info(f"结构化解析成功 - {task_name}: 成功解析为 {response_model.__name__} 模型")
                return structured_result
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析失败 - {task_name}: {str(e)}")
                logger.error(f"原始响应内容: {response_text[:500]}...")
                raise AICallError(f"JSON解析失败 - {task_name}: {str(e)}")
            except Exception as e:
                logger.error(f"模型验证失败 - {task_name}: {str(e)}")
                logger.error(f"原始响应内容: {response_text[:500]}...")
                raise AICallError(f"模型验证失败 - {task_name}: {str(e)}")
            
        except AICallError:
            raise
        except Exception as e:
            logger.error(f"AI结构化调用失败 - {task_name}: {str(e)}")
            raise AICallError(f"AI结构化调用失败 - {task_name}: {str(e)}")
    
    def call_ai_structured_with_retry(
        self,
        prompt: str,
        response_model: Type[T],
        system_message: str = "你是一个专业的学术写作专家。",
        task_name: str = "AI结构化分析",
        max_retries: int = 3,
        retry_delay: float = 1.0,
        **kwargs
    ) -> T:
        """
        带重试机制的结构化AI调用
        
        Args:
            prompt: 用户提示词
            response_model: Pydantic模型类
            system_message: 系统消息
            task_name: 任务名称
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
            **kwargs: 其他参数传递给call_ai_structured
            
        Returns:
            解析后的Pydantic模型实例
        """
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return self.call_ai_structured(
                    prompt=prompt,
                    response_model=response_model,
                    system_message=system_message,
                    task_name=f"{task_name} (尝试 {attempt + 1}/{max_retries + 1})",
                    **kwargs
                )
            except Exception as e:
                last_exception = e
                if attempt < max_retries:
                    logger.warning(f"AI结构化调用失败，{retry_delay}秒后重试 - {task_name}: {str(e)}")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # 指数退避
                else:
                    logger.error(f"AI结构化调用最终失败 - {task_name}: {str(e)}")
        
        raise AICallError(f"AI结构化调用重试失败 - {task_name}: {str(last_exception)}")
    
    def _map_json_fields(self, json_data: Dict[str, Any], response_model: Type[T]) -> Dict[str, Any]:
        """
        映射JSON字段到Pydantic模型字段
        
        Args:
            json_data: 原始JSON数据
            response_model: Pydantic模型类
            
        Returns:
            映射后的数据字典
        """
        # 获取模型字段信息
        model_fields = response_model.model_fields
        
        # 常见的中英文字段映射（优先匹配英文key）
        field_mappings = {
            # 通用字段
            'name': ['name', 'title', '名称', '标题', '事件', '会议名称'],
            'date': ['date', 'time', '日期', '时间'],
            'participants': ['participants', 'participant', '人员', '参与者', '参与人员'],
            'location': ['location', 'place', '地点', '位置'],
            'description': ['description', 'details', '描述', '说明'],
            
            # 学术相关字段
            'title': ['title', '标题', '论文标题', '研究标题'],
            'abstract': ['abstract', 'summary', '摘要', '概要'],
            'keywords': ['keywords', 'keyword', '关键词', '关键字'],
            'methodology': ['methodology', 'method', '方法', '研究方法', '方法学'],
            'findings': ['findings', 'results', 'key_findings', '发现', '结果', '主要发现'],
            'limitations': ['limitations', 'limitation', '限制', '局限性', '不足'],
            'future_work': ['future_work', 'future_directions', 'future_research', '未来工作', '未来研究', '后续工作'],
            'quality_score': ['quality_score', 'score', 'rating', '质量评分', '评分'],
            
            # 写作风格字段
            'clarity_score': ['clarity_score', 'clarity', '清晰度评分', '清晰度'],
            'conciseness_score': ['conciseness_score', 'conciseness', '简洁性评分', '简洁性'],
            'academic_tone_score': ['academic_tone_score', 'academic_tone', '学术语调评分', '学术语调'],
            'grammar_issues': ['grammar_issues', 'grammar_errors', '语法问题', '语法错误'],
            'style_suggestions': ['style_suggestions', 'suggestions', '风格建议', '改进建议'],
            'overall_quality': ['overall_quality', 'quality', '整体质量', '总体质量'],
            
            # 论文分析字段
            'main_contribution': ['main_contribution', 'contribution', '主要贡献', '贡献'],
            'key_findings': ['key_findings', 'findings', '关键发现', '主要发现'],
            'future_directions': ['future_directions', 'future_work', '未来方向', '未来工作']
        }
        
        mapped_data = {}
        
        for field_name, field_info in model_fields.items():
            # 首先尝试直接匹配
            if field_name in json_data:
                mapped_data[field_name] = json_data[field_name]
                continue
            
            # 尝试通过映射表匹配
            if field_name in field_mappings:
                for possible_key in field_mappings[field_name]:
                    if possible_key in json_data:
                        mapped_data[field_name] = json_data[possible_key]
                        break
            
            # 如果仍然没有找到，尝试模糊匹配（忽略大小写和特殊字符）
            if field_name not in mapped_data:
                for key, value in json_data.items():
                    if self._fuzzy_match_field(field_name, key):
                        mapped_data[field_name] = value
                        break
        
        logger.info(f"字段映射完成: {len(mapped_data)}/{len(model_fields)} 个字段成功映射")
        return mapped_data
    
    def _fuzzy_match_field(self, field_name: str, json_key: str) -> bool:
        """
        模糊匹配字段名
        
        Args:
            field_name: Pydantic字段名
            json_key: JSON键名
            
        Returns:
            是否匹配
        """
        # 转换为小写并移除特殊字符
        field_clean = ''.join(c.lower() for c in field_name if c.isalnum())
        json_clean = ''.join(c.lower() for c in json_key if c.isalnum())
        
        # 检查是否包含或相似
        return (field_clean in json_clean or 
                json_clean in field_clean or 
                field_clean == json_clean)
    
    def _log_ai_input(self, task_name: str, prompt: str, params: Dict[str, Any]) -> None:
        """记录AI输入日志"""
        logger.info(f"=== AI输入日志 - {task_name} ===")
        logger.info(f"模型: {params['model']}")
        logger.info(f"最大令牌数: {params['max_tokens']}")
        logger.info(f"温度参数: {params['temperature']}")
        logger.info(f"输入文本长度: {len(prompt)} 字符")
        
        # 记录系统消息
        if 'messages' in params and len(params['messages']) > 0:
            system_msg = params['messages'][0].get('content', '')
            logger.info(f"系统消息: {system_msg[:100]}{'...' if len(system_msg) > 100 else ''}")
        
        # 记录完整prompt（截断显示）
        logger.info("--- 完整Prompt ---")
        if len(prompt) > 1000:
            logger.info(f"{prompt[:500]}...\n...\n{prompt[-500:]}")
        else:
            logger.info(prompt)
        logger.info("--- Prompt结束 ---")
    
    def _log_ai_output(
        self, 
        task_name: str, 
        response_text: str, 
        response: ChatCompletion, 
        duration: float
    ) -> None:
        """记录AI输出日志"""
        logger.info(f"=== AI输出日志 - {task_name} ===")
        logger.info(f"响应长度: {len(response_text)} 字符")
        logger.info(f"调用耗时: {duration:.2f} 秒")
        
        # 记录使用统计
        if hasattr(response, 'usage') and response.usage:
            usage = response.usage
            logger.info(f"使用令牌数: {usage.total_tokens}")
            logger.info(f"  - 输入令牌: {usage.prompt_tokens}")
            logger.info(f"  - 输出令牌: {usage.completion_tokens}")
        else:
            logger.info("使用令牌数: 未知")
        
        # 记录完成原因
        if response.choices and len(response.choices) > 0:
            finish_reason = response.choices[0].finish_reason
            logger.info(f"完成原因: {finish_reason}")
        
        # 记录响应内容（截断显示）
        logger.info("--- 完整响应 ---")
        if len(response_text) > 1000:
            logger.info(f"{response_text[:500]}...\n...\n{response_text[-500:]}")
        else:
            logger.info(response_text)
        logger.info("--- 响应结束 ---")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取AI调用统计信息"""
        return {
            "total_calls": self._call_count,
            "total_tokens": self._total_tokens,
            "average_tokens_per_call": self._total_tokens / self._call_count if self._call_count > 0 else 0
        }
    
    def reset_stats(self) -> None:
        """重置统计信息"""
        self._call_count = 0
        self._total_tokens = 0
        logger.info("AI调用统计信息已重置")


class AICallError(Exception):
    """AI调用异常"""
    pass


# 全局AI客户端实例
_ai_client = None

def get_ai_client() -> AIClient:
    """获取全局AI客户端实例（单例模式）"""
    global _ai_client
    if _ai_client is None:
        _ai_client = AIClient()
    return _ai_client


def call_ai_simple(
    prompt: str,
    system_message: str = "你是一个专业的学术写作专家。",
    task_name: str = "AI分析",
    **kwargs
) -> str:
    """
    简化的AI调用函数（便捷接口）
    
    Args:
        prompt: 用户提示词
        system_message: 系统消息
        task_name: 任务名称
        **kwargs: 其他参数
        
    Returns:
        AI响应的文本内容
    """
    client = get_ai_client()
    return client.call_ai(
        prompt=prompt,
        system_message=system_message,
        task_name=task_name,
        **kwargs
    )


def call_ai_json_simple(
    prompt: str,
    system_message: str = "你是一个专业的学术写作专家。请以JSON格式返回结果。",
    task_name: str = "AI分析",
    **kwargs
) -> Dict[str, Any]:
    """
    简化的AI JSON调用函数（便捷接口）
    
    Args:
        prompt: 用户提示词
        system_message: 系统消息
        task_name: 任务名称
        **kwargs: 其他参数
        
    Returns:
        解析后的JSON数据
    """
    client = get_ai_client()
    return client.call_ai_json(
        prompt=prompt,
        system_message=system_message,
        task_name=task_name,
        **kwargs
    )


def call_ai_structured_simple(
    prompt: str,
    response_model: Type[T],
    system_message: str = "你是一个专业的学术写作专家。请严格按照JSON格式返回结果，JSON的key必须是英文，value可以是中文。",
    task_name: str = "AI结构化分析",
    **kwargs
) -> T:
    """
    简化的AI结构化调用函数（便捷接口）
    
    Args:
        prompt: 用户提示词
        response_model: Pydantic模型类
        system_message: 系统消息
        task_name: 任务名称
        **kwargs: 其他参数
        
    Returns:
        解析后的Pydantic模型实例
    """
    client = get_ai_client()
    return client.call_ai_structured(
        prompt=prompt,
        response_model=response_model,
        system_message=system_message,
        task_name=task_name,
        **kwargs
    )
