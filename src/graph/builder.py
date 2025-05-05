from langgraph.graph import StateGraph, START

from .types import State
from .nodes import (
    supervisor_node,
    research_node,
    code_node,
    coordinator_node,
    browser_node,
    reporter_node,
    planner_node,
)


def build_graph():
    """Build and return the agent workflow graph."""
    """构建并返回智能体工作流图。"""
    builder = StateGraph(State)  # 创建一个StateGraph对象，使用State类作为状态类型
    
    # 添加工作流的起始边，从START指向coordinator节点
    builder.add_edge(START, "coordinator")
    
    # 添加所有节点到工作流图中
    builder.add_node("coordinator", coordinator_node)  # 添加协调者节点，负责与用户沟通
    builder.add_node("planner", planner_node)          # 添加规划者节点，生成完整的执行计划
    builder.add_node("supervisor", supervisor_node)    # 添加主管节点，决定下一步操作
    builder.add_node("researcher", research_node)      # 添加研究员节点，执行信息收集任务
    builder.add_node("coder", code_node)               # 添加程序员节点，执行代码和技术任务
    builder.add_node("browser", browser_node)          # 添加浏览器节点，执行网页浏览任务
    builder.add_node("reporter", reporter_node)        # 添加报告者节点，编写最终报告
    
    return builder.compile()  # 编译工作流图并返回，使其可以被执行
