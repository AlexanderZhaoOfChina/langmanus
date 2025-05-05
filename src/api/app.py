"""
FastAPI application for LangManus.
LangManus的FastAPI应用程序，提供Web API服务。
"""

import json
import logging
from typing import Dict, List, Any, Optional, Union

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse
import asyncio
from typing import AsyncGenerator, Dict, List, Any

from src.graph import build_graph
from src.config import TEAM_MEMBERS
from src.service.workflow_service import run_agent_workflow

# 配置日志系统
logger = logging.getLogger(__name__)

# 创建FastAPI应用实例
# 设置应用的元数据，包括标题、描述和版本信息
app = FastAPI(
    title="LangManus API",
    description="API for LangManus LangGraph-based agent workflow",
    version="0.1.0",
)

# 添加CORS中间件
# 允许跨域资源共享，使前端应用能够从不同域名访问API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源的请求
    allow_credentials=True,  # 允许发送凭证（如cookies）
    allow_methods=["*"],  # 允许所有HTTP方法
    allow_headers=["*"],  # 允许所有HTTP头部
)

# 创建工作流图
# 构建LangGraph工作流图，定义智能体之间的协作关系
graph = build_graph()


# 定义内容项模型
# 用于表示消息中的不同类型内容（文本、图像等）
class ContentItem(BaseModel):
    type: str = Field(..., description="The type of content (text, image, etc.)")  # 内容类型（文本、图像等）
    text: Optional[str] = Field(None, description="The text content if type is 'text'")  # 文本内容（当类型为text时）
    image_url: Optional[str] = Field(
        None, description="The image URL if type is 'image'"  # 图像URL（当类型为image时）
    )


# 定义聊天消息模型
# 表示对话中的单条消息，包含角色和内容
class ChatMessage(BaseModel):
    role: str = Field(
        ..., description="The role of the message sender (user or assistant)"  # 消息发送者的角色（用户或助手）
    )
    content: Union[str, List[ContentItem]] = Field(
        ...,
        description="The content of the message, either a string or a list of content items",  # 消息内容，可以是字符串或内容项列表
    )


# 定义聊天请求模型
# 表示聊天API的完整请求结构
class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., description="The conversation history")  # 对话历史记录
    debug: Optional[bool] = Field(False, description="Whether to enable debug logging")  # 是否启用调试日志
    deep_thinking_mode: Optional[bool] = Field(
        False, description="Whether to enable deep thinking mode"  # 是否启用深度思考模式
    )
    search_before_planning: Optional[bool] = Field(
        False, description="Whether to search before planning"  # 是否在规划前执行搜索
    )


@app.post("/api/chat/stream")
async def chat_endpoint(request: ChatRequest, req: Request):
    """
    Chat endpoint for LangGraph invoke.

    Args:
        request: The chat request
        req: The FastAPI request object for connection state checking

    Returns:
        The streamed response
    """
    """
    聊天端点，用于调用LangGraph工作流并获取流式响应。
    
    参数:
        request: 聊天请求对象，包含消息历史和配置选项
        req: FastAPI请求对象，用于检查连接状态
        
    返回:
        服务器发送事件(SSE)流式响应
    """
    try:
        # 将Pydantic模型转换为字典并规范化内容格式
        messages = []
        for msg in request.messages:
            message_dict = {"role": msg.role}

            # 处理字符串内容和内容项列表两种形式
            if isinstance(msg.content, str):
                # 如果内容是简单字符串，直接使用
                message_dict["content"] = msg.content
            else:
                # 如果内容是列表，转换为工作流期望的格式
                content_items = []
                for item in msg.content:
                    if item.type == "text" and item.text:
                        # 添加文本内容项
                        content_items.append({"type": "text", "text": item.text})
                    elif item.type == "image" and item.image_url:
                        # 添加图像内容项
                        content_items.append(
                            {"type": "image", "image_url": item.image_url}
                        )

                message_dict["content"] = content_items

            messages.append(message_dict)

        # 定义事件生成器函数
        # 用于生成SSE事件流
        async def event_generator():
            try:
                # 调用工作流服务，获取异步事件流
                async for event in run_agent_workflow(
                    messages,  # 消息历史
                    request.debug,  # 是否启用调试
                    request.deep_thinking_mode,  # 是否启用深度思考模式
                    request.search_before_planning,  # 是否在规划前搜索
                ):
                    # 检查客户端是否仍然连接
                    if await req.is_disconnected():
                        logger.info("Client disconnected, stopping workflow")  # 客户端断开连接，停止工作流
                        break
                    # 生成SSE事件
                    yield {
                        "event": event["event"],  # 事件类型
                        "data": json.dumps(event["data"], ensure_ascii=False),  # 事件数据（JSON格式）
                    }
            except asyncio.CancelledError:
                # 处理异步取消异常
                logger.info("Stream processing cancelled")  # 流处理被取消
                raise

        # 返回SSE响应
        # 使用事件生成器提供的事件流
        return EventSourceResponse(
            event_generator(),  # 事件生成器
            media_type="text/event-stream",  # 媒体类型为SSE
            sep="\n",  # 事件分隔符
        )
    except Exception as e:
        # 处理任何异常
        logger.error(f"Error in chat endpoint: {e}")  # 记录错误
        # 返回500错误响应
        raise HTTPException(status_code=500, detail=str(e))
