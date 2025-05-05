from typing import Literal
from typing_extensions import TypedDict
from langgraph.graph import MessagesState

from src.config import TEAM_MEMBERS

# 定义路由选项
# OPTIONS包含所有团队成员名称加上"FINISH"，用于表示工作流程的各种路由目的地
OPTIONS = TEAM_MEMBERS + ["FINISH"]


class Router(TypedDict):
    """Worker to route to next. If no workers needed, route to FINISH."""
    """决定下一步由哪个工作者处理的路由器。如果不需要工作者，则路由到FINISH。"""

    next: Literal[*OPTIONS]  # 下一个要执行的智能体名称或FINISH标记


class State(MessagesState):
    """State for the agent system, extends MessagesState with next field."""
    """智能体系统的状态，扩展了MessagesState并添加了额外字段。"""

    # Constants（常量）
    TEAM_MEMBERS: list[str]  # 团队成员列表，存储所有可用的智能体名称

    # Runtime Variables（运行时变量）
    next: str  # 下一步执行的智能体名称
    full_plan: str  # 完整的执行计划，通常由planner节点生成的JSON格式计划
    deep_thinking_mode: bool  # 是否启用深度思考模式，启用时会使用reasoning LLM而不是basic LLM
    search_before_planning: bool  # 是否在规划前执行搜索，为规划提供更多上下文信息
