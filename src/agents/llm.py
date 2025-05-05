from langchain_openai import ChatOpenAI
from langchain_deepseek import ChatDeepSeek
from typing import Optional

from src.config import (
    REASONING_MODEL,
    REASONING_BASE_URL,
    REASONING_API_KEY,
    BASIC_MODEL,
    BASIC_BASE_URL,
    BASIC_API_KEY,
    VL_MODEL,
    VL_BASE_URL,
    VL_API_KEY,
)
from src.config.agents import LLMType


def create_openai_llm(
    model: str,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    temperature: float = 0.0,
    **kwargs,
) -> ChatOpenAI:
    """
    Create a ChatOpenAI instance with the specified configuration
    """
    """
    创建一个基于OpenAI兼容API的聊天模型实例
    
    参数:
        model: 模型名称或标识符
        base_url: 自定义API基础URL，用于支持非OpenAI官方API的服务（如阿里云千问）
        api_key: API密钥
        temperature: 温度参数，控制随机性（0.0表示最确定性的输出）
        **kwargs: 其他传递给ChatOpenAI构造函数的参数
        
    返回:
        配置好的ChatOpenAI实例
    """
    # 仅在base_url不为None或空字符串时包含它
    llm_kwargs = {"model": model, "temperature": temperature, **kwargs}

    if base_url:  # 这将处理None或空字符串的情况
        llm_kwargs["base_url"] = base_url

    if api_key:  # 这将处理None或空字符串的情况
        llm_kwargs["api_key"] = api_key

    return ChatOpenAI(**llm_kwargs)


def create_deepseek_llm(
    model: str,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    temperature: float = 0.0,
    **kwargs,
) -> ChatDeepSeek:
    """
    Create a ChatDeepSeek instance with the specified configuration
    """
    """
    创建一个基于DeepSeek API的聊天模型实例
    
    参数:
        model: DeepSeek模型名称或标识符
        base_url: 自定义API基础URL
        api_key: DeepSeek API密钥
        temperature: 温度参数，控制随机性（0.0表示最确定性的输出）
        **kwargs: 其他传递给ChatDeepSeek构造函数的参数
        
    返回:
        配置好的ChatDeepSeek实例
    """
    # 仅在base_url不为None或空字符串时包含它
    llm_kwargs = {"model": model, "temperature": temperature, **kwargs}

    if base_url:  # 这将处理None或空字符串的情况
        llm_kwargs["api_base"] = base_url  # 注意：DeepSeek使用api_base而不是base_url

    if api_key:  # 这将处理None或空字符串的情况
        llm_kwargs["api_key"] = api_key

    return ChatDeepSeek(**llm_kwargs)


# LLM实例的缓存
# 用于存储已创建的LLM实例，避免重复创建相同配置的模型实例
_llm_cache: dict[LLMType, ChatOpenAI | ChatDeepSeek] = {}


def get_llm_by_type(llm_type: LLMType) -> ChatOpenAI | ChatDeepSeek:
    """
    Get LLM instance by type. Returns cached instance if available.
    """
    """
    根据类型获取LLM实例，如果缓存中有可用实例则返回缓存的实例
    
    参数:
        llm_type: LLM类型，可以是"reasoning"（推理）、"basic"（基础）或"vision"（视觉）
        
    返回:
        对应类型的LLM实例（ChatOpenAI或ChatDeepSeek）
        
    异常:
        ValueError: 如果提供了未知的LLM类型
    """
    # 检查缓存中是否已有该类型的LLM实例
    if llm_type in _llm_cache:
        return _llm_cache[llm_type]

    # 根据类型创建不同的LLM实例
    if llm_type == "reasoning":
        # 推理LLM - 使用DeepSeek模型，适用于复杂推理任务
        llm = create_deepseek_llm(
            model=REASONING_MODEL,
            base_url=REASONING_BASE_URL,
            api_key=REASONING_API_KEY,
        )
    elif llm_type == "basic":
        # 基础LLM - 使用较轻量级模型，适用于简单任务
        llm = create_openai_llm(
            model=BASIC_MODEL,
            base_url=BASIC_BASE_URL,
            api_key=BASIC_API_KEY,
        )
    elif llm_type == "vision":
        # 视觉LLM - 支持处理图像的模型，适用于多模态任务
        llm = create_openai_llm(
            model=VL_MODEL,
            base_url=VL_BASE_URL,
            api_key=VL_API_KEY,
        )
    else:
        # 未知类型，抛出错误
        raise ValueError(f"Unknown LLM type: {llm_type}")

    # 将创建的实例存入缓存
    _llm_cache[llm_type] = llm
    return llm


# 初始化不同用途的LLM - 这些实例会被缓存
# 预先初始化，以便在整个应用程序中使用
reasoning_llm = get_llm_by_type("reasoning")  # 用于复杂推理的LLM
basic_llm = get_llm_by_type("basic")          # 用于基本任务的LLM
vl_llm = get_llm_by_type("vision")            # 用于视觉任务的LLM


if __name__ == "__main__":
    # 当直接运行此文件时，执行测试代码
    # 测试推理LLM的流式输出
    stream = reasoning_llm.stream("what is mcp?")
    full_response = ""
    for chunk in stream:
        full_response += chunk.content
    print(full_response)

    # 测试基础LLM和视觉LLM是否能正常工作
    basic_llm.invoke("Hello")
    vl_llm.invoke("Hello")
