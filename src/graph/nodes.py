import logging
import json
from copy import deepcopy
from typing import Literal
from langchain_core.messages import HumanMessage
from langgraph.types import Command
from langgraph.graph import END

from src.agents import research_agent, coder_agent, browser_agent
from src.agents.llm import get_llm_by_type
from src.config import TEAM_MEMBERS
from src.config.agents import AGENT_LLM_MAP
from src.prompts.template import apply_prompt_template
from src.tools.search import tavily_tool
from .types import State, Router

logger = logging.getLogger(__name__)

# 定义智能体响应的格式化模板
# 包含智能体名称和响应内容，以及提示执行下一步操作的信息
RESPONSE_FORMAT = "Response from {}:\n\n<response>\n{}\n</response>\n\n*Please execute the next step.*"


def research_node(state: State) -> Command[Literal["supervisor"]]:
    """Node for the researcher agent that performs research tasks."""
    """研究员智能体节点，执行信息收集和研究任务。"""
    logger.info("Research agent starting task")  # 记录研究智能体开始任务
    result = research_agent.invoke(state)  # 调用研究智能体处理当前状态
    logger.info("Research agent completed task")  # 记录研究智能体完成任务
    logger.debug(f"Research agent response: {result['messages'][-1].content}")  # 记录研究智能体的详细响应
    return Command(
        update={
            "messages": [
                HumanMessage(
                    content=RESPONSE_FORMAT.format(
                        "researcher", result["messages"][-1].content
                    ),
                    name="researcher",  # 设置消息的发送者为"researcher"
                )
            ]
        },
        goto="supervisor",  # 指示下一步转到supervisor节点
    )


def code_node(state: State) -> Command[Literal["supervisor"]]:
    """Node for the coder agent that executes Python code."""
    """程序员智能体节点，执行Python代码和处理技术任务。"""
    logger.info("Code agent starting task")  # 记录代码智能体开始任务
    result = coder_agent.invoke(state)  # 调用代码智能体处理当前状态
    logger.info("Code agent completed task")  # 记录代码智能体完成任务
    logger.debug(f"Code agent response: {result['messages'][-1].content}")  # 记录代码智能体的详细响应
    return Command(
        update={
            "messages": [
                HumanMessage(
                    content=RESPONSE_FORMAT.format(
                        "coder", result["messages"][-1].content
                    ),
                    name="coder",  # 设置消息的发送者为"coder"
                )
            ]
        },
        goto="supervisor",  # 指示下一步转到supervisor节点
    )


def browser_node(state: State) -> Command[Literal["supervisor"]]:
    """Node for the browser agent that performs web browsing tasks."""
    """浏览器智能体节点，执行网页浏览和信息提取任务。"""
    logger.info("Browser agent starting task")  # 记录浏览器智能体开始任务 
    result = browser_agent.invoke(state)  # 调用浏览器智能体处理当前状态
    logger.info("Browser agent completed task")  # 记录浏览器智能体完成任务
    logger.debug(f"Browser agent response: {result['messages'][-1].content}")  # 记录浏览器智能体的详细响应
    return Command(
        update={
            "messages": [
                HumanMessage(
                    content=RESPONSE_FORMAT.format(
                        "browser", result["messages"][-1].content
                    ),
                    name="browser",  # 设置消息的发送者为"browser"
                )
            ]
        },
        goto="supervisor",  # 指示下一步转到supervisor节点
    )


def supervisor_node(state: State) -> Command[Literal[*TEAM_MEMBERS, "__end__"]]:
    """Supervisor node that decides which agent should act next."""
    """主管节点，决定下一步由哪个智能体执行操作或完成任务。"""
    logger.info("Supervisor evaluating next action")  # 记录主管正在评估下一步操作
    messages = apply_prompt_template("supervisor", state)  # 应用主管的提示模板，生成消息列表
    response = (
        get_llm_by_type(AGENT_LLM_MAP["supervisor"])  # 获取主管智能体对应的语言模型
        .with_structured_output(Router)  # 设置输出为结构化的Router类型
        .invoke(messages)  # 调用语言模型处理消息
    )
    goto = response["next"]  # 获取下一步的目标节点
    logger.debug(f"Current state messages: {state['messages']}")  # 记录当前状态的消息
    logger.debug(f"Supervisor response: {response}")  # 记录主管的详细响应

    if goto == "FINISH":
        goto = "__end__"  # 如果下一步是FINISH，则将目标设为__end__，表示工作流结束
        logger.info("Workflow completed")  # 记录工作流已完成
    else:
        logger.info(f"Supervisor delegating to: {goto}")  # 记录主管将任务委派给哪个智能体

    return Command(goto=goto, update={"next": goto})  # 返回Command，指示下一步和更新状态


def planner_node(state: State) -> Command[Literal["supervisor", "__end__"]]:
    """Planner node that generate the full plan."""
    """规划者节点，生成完整的执行计划。"""
    logger.info("Planner generating full plan")  # 记录规划者正在生成完整计划
    messages = apply_prompt_template("planner", state)  # 应用规划者的提示模板，生成消息列表
    
    # 根据是否启用深度思考模式选择合适的语言模型
    llm = get_llm_by_type("basic")  # 默认使用基础语言模型
    if state.get("deep_thinking_mode"):
        llm = get_llm_by_type("reasoning")  # 如果启用深度思考模式，则使用推理语言模型
    
    # 如果启用规划前搜索，则使用Tavily工具搜索相关信息并添加到提示中
    if state.get("search_before_planning"):
        searched_content = tavily_tool.invoke({"query": state["messages"][-1].content})  # 使用Tavily搜索
        messages = deepcopy(messages)  # 创建消息列表的深拷贝
        messages[
            -1
        ].content += f"\n\n# Relative Search Results\n\n{json.dumps([{'titile': elem['title'], 'content': elem['content']} for elem in searched_content], ensure_ascii=False)}"  # 将搜索结果添加到最后一条消息中
    
    stream = llm.stream(messages)  # 使用流式API调用语言模型
    full_response = ""  # 初始化完整响应
    for chunk in stream:
        full_response += chunk.content  # 累积模型返回的内容块
    logger.debug(f"Current state messages: {state['messages']}")  # 记录当前状态的消息
    logger.debug(f"Planner response: {full_response}")  # 记录规划者的详细响应

    # 处理响应格式，移除可能的Markdown代码块标记
    if full_response.startswith("```json"):
        full_response = full_response.removeprefix("```json")

    if full_response.endswith("```"):
        full_response = full_response.removesuffix("```")

    goto = "supervisor"  # 默认下一步转到supervisor节点
    try:
        json.loads(full_response)  # 尝试解析响应为JSON格式
    except json.JSONDecodeError:
        logger.warning("Planner response is not a valid JSON")  # 记录规划者响应不是有效的JSON
        goto = "__end__"  # 如果JSON解析失败，则将下一步设置为__end__，结束工作流

    return Command(
        update={
            "messages": [HumanMessage(content=full_response, name="planner")],  # 添加规划者的响应消息
            "full_plan": full_response,  # 更新完整计划
        },
        goto=goto,  # 指示下一步
    )


def coordinator_node(state: State) -> Command[Literal["planner", "__end__"]]:
    """Coordinator node that communicate with customers."""
    """协调者节点，负责与用户沟通。"""
    logger.info("Coordinator talking.")  # 记录协调者正在交谈
    messages = apply_prompt_template("coordinator", state)  # 应用协调者的提示模板，生成消息列表
    response = get_llm_by_type(AGENT_LLM_MAP["coordinator"]).invoke(messages)  # 调用协调者对应的语言模型
    logger.debug(f"Current state messages: {state['messages']}")  # 记录当前状态的消息
    logger.debug(f"reporter response: {response}")  # 记录协调者的详细响应

    goto = "__end__"  # 默认下一步为__end__，结束工作流
    if "handoff_to_planner" in response.content:
        goto = "planner"  # 如果响应中包含"handoff_to_planner"，则将下一步设置为planner

    return Command(
        goto=goto,  # 指示下一步
    )


def reporter_node(state: State) -> Command[Literal["supervisor"]]:
    """Reporter node that write a final report."""
    """报告者节点，负责编写最终报告。"""
    logger.info("Reporter write final report")  # 记录报告者正在编写最终报告
    messages = apply_prompt_template("reporter", state)  # 应用报告者的提示模板，生成消息列表
    response = get_llm_by_type(AGENT_LLM_MAP["reporter"]).invoke(messages)  # 调用报告者对应的语言模型
    logger.debug(f"Current state messages: {state['messages']}")  # 记录当前状态的消息
    logger.debug(f"reporter response: {response}")  # 记录报告者的详细响应

    return Command(
        update={
            "messages": [
                HumanMessage(
                    content=RESPONSE_FORMAT.format("reporter", response.content),  # 格式化报告者的响应
                    name="reporter",  # 设置消息的发送者为"reporter"
                )
            ]
        },
        goto="supervisor",  # 指示下一步转到supervisor节点
    )
