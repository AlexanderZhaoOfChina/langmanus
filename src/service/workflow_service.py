import logging

from src.config import TEAM_MEMBERS
from src.graph import build_graph
from langchain_community.adapters.openai import convert_message_to_dict
import uuid

# 配置日志系统
# 设置日志级别为INFO，格式包含时间、模块名、日志级别和消息内容
logging.basicConfig(
    level=logging.INFO,  # 默认日志级别为INFO
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def enable_debug_logging():
    """Enable debug level logging for more detailed execution information."""
    """启用DEBUG级别的日志，以获取更详细的执行信息。"""
    logging.getLogger("src").setLevel(logging.DEBUG)


# 获取当前模块的日志记录器
logger = logging.getLogger(__name__)

# 创建工作流图
# 调用build_graph函数构建完整的智能体工作流图
graph = build_graph()

# 协调者消息缓存
# 用于临时存储协调者产生的消息块，以便进行消息处理和判断
coordinator_cache = []
MAX_CACHE_SIZE = 2  # 最大缓存大小，用于决定何时处理和发送协调者消息


async def run_agent_workflow(
    user_input_messages: list,
    debug: bool = False,
    deep_thinking_mode: bool = False,
    search_before_planning: bool = False,
):
    """Run the agent workflow with the given user input.

    Args:
        user_input_messages: The user request messages
        debug: If True, enables debug level logging

    Returns:
        The final state after the workflow completes
    """
    """
    以异步方式运行智能体工作流，处理用户输入并流式返回结果事件。
    
    参数:
        user_input_messages: 用户的消息列表
        debug: 如果为True，则启用DEBUG级别的日志记录
        deep_thinking_mode: 如果为True，则启用深度思考模式，使用推理LLM
        search_before_planning: 如果为True，则在规划前执行搜索
        
    返回:
        异步生成工作流事件流
    """
    # 验证输入不能为空
    if not user_input_messages:
        raise ValueError("Input could not be empty")

    # 如果启用了debug模式，则设置更详细的日志级别
    if debug:
        enable_debug_logging()

    # 记录工作流开始的信息
    logger.info(f"Starting workflow with user input: {user_input_messages}")

    # 生成唯一的工作流ID，用于标识此次执行的工作流实例
    workflow_id = str(uuid.uuid4())

    # 定义需要流式处理的LLM智能体列表
    # 包括所有团队成员以及planner和coordinator
    streaming_llm_agents = [*TEAM_MEMBERS, "planner", "coordinator"]

    # 在每次工作流启动时重置协调者缓存
    global coordinator_cache
    coordinator_cache = []
    global is_handoff_case
    is_handoff_case = False  # 标记是否为切换到planner的情况

    # 使用异步流式API获取工作流事件
    # TODO: 提取消息内容，特别是用于on_chat_model_stream事件
    async for event in graph.astream_events(
        {
            # 常量设置
            "TEAM_MEMBERS": TEAM_MEMBERS,  # 团队成员列表
            # 运行时变量
            "messages": user_input_messages,  # 用户输入消息
            "deep_thinking_mode": deep_thinking_mode,  # 深度思考模式设置
            "search_before_planning": search_before_planning,  # 规划前搜索设置
        },
        version="v2",  # 使用v2版本的事件流API
    ):
        # 从事件中提取关键信息
        kind = event.get("event")  # 事件类型
        data = event.get("data")   # 事件数据
        name = event.get("name")   # 事件名称
        metadata = event.get("metadata")  # 元数据
        
        # 提取当前节点名称（从checkpoint命名空间中）
        node = (
            ""
            if (metadata.get("checkpoint_ns") is None)
            else metadata.get("checkpoint_ns").split(":")[0]
        )
        
        # 提取LangGraph执行步骤
        langgraph_step = (
            ""
            if (metadata.get("langgraph_step") is None)
            else str(metadata["langgraph_step"])
        )
        
        # 提取运行ID
        run_id = "" if (event.get("run_id") is None) else str(event["run_id"])

        # 根据事件类型和节点名称处理不同的事件
        # 1. 智能体链开始事件
        if kind == "on_chain_start" and name in streaming_llm_agents:
            # 如果是规划者开始，则发出工作流开始事件
            if name == "planner":
                yield {
                    "event": "start_of_workflow",
                    "data": {"workflow_id": workflow_id, "input": user_input_messages},
                }
            # 为所有智能体发出智能体开始事件
            ydata = {
                "event": "start_of_agent",
                "data": {
                    "agent_name": name,  # 智能体名称
                    "agent_id": f"{workflow_id}_{name}_{langgraph_step}",  # 唯一智能体实例ID
                },
            }
        # 2. 智能体链结束事件
        elif kind == "on_chain_end" and name in streaming_llm_agents:
            ydata = {
                "event": "end_of_agent",
                "data": {
                    "agent_name": name,  # 智能体名称
                    "agent_id": f"{workflow_id}_{name}_{langgraph_step}",  # 唯一智能体实例ID
                },
            }
        # 3. 语言模型开始事件
        elif kind == "on_chat_model_start" and node in streaming_llm_agents:
            ydata = {
                "event": "start_of_llm",
                "data": {"agent_name": node},  # 使用LLM的智能体名称
            }
        # 4. 语言模型结束事件
        elif kind == "on_chat_model_end" and node in streaming_llm_agents:
            ydata = {
                "event": "end_of_llm",
                "data": {"agent_name": node},  # 使用LLM的智能体名称
            }
        # 5. 语言模型流式输出事件（处理模型生成的内容块）
        elif kind == "on_chat_model_stream" and node in streaming_llm_agents:
            content = data["chunk"].content  # 获取内容块
            
            # 处理空内容或只有推理内容的情况
            if content is None or content == "":
                if not data["chunk"].additional_kwargs.get("reasoning_content"):
                    # 跳过完全空的消息
                    continue
                # 生成包含推理内容的事件
                ydata = {
                    "event": "message",
                    "data": {
                        "message_id": data["chunk"].id,  # 消息ID
                        "delta": {
                            "reasoning_content": (
                                data["chunk"].additional_kwargs["reasoning_content"]  # 推理内容
                            )
                        },
                    },
                }
            else:
                # 处理有实际内容的消息
                # 特别处理来自协调者的消息
                if node == "coordinator":
                    if len(coordinator_cache) < MAX_CACHE_SIZE:
                        # 将内容添加到缓存
                        coordinator_cache.append(content)
                        cached_content = "".join(coordinator_cache)  # 合并缓存内容
                        
                        # 检查是否为切换到planner的指令
                        if cached_content.startswith("handoff"):
                            is_handoff_case = True  # 标记为切换情况
                            continue
                            
                        # 如果缓存未满，继续收集
                        if len(coordinator_cache) < MAX_CACHE_SIZE:
                            continue
                            
                        # 缓存已满，发送完整的缓存内容
                        ydata = {
                            "event": "message",
                            "data": {
                                "message_id": data["chunk"].id,
                                "delta": {"content": cached_content},  # 发送合并后的内容
                            },
                        }
                    elif not is_handoff_case:
                        # 如果不是切换情况且缓存已满，直接发送当前内容
                        ydata = {
                            "event": "message",
                            "data": {
                                "message_id": data["chunk"].id,
                                "delta": {"content": content},
                            },
                        }
                else:
                    # 对于其他智能体，直接发送消息内容
                    ydata = {
                        "event": "message",
                        "data": {
                            "message_id": data["chunk"].id,
                            "delta": {"content": content},
                        },
                    }
        # 6. 工具调用开始事件
        elif kind == "on_tool_start" and node in TEAM_MEMBERS:
            ydata = {
                "event": "tool_call",
                "data": {
                    "tool_call_id": f"{workflow_id}_{node}_{name}_{run_id}",  # 唯一工具调用ID
                    "tool_name": name,  # 工具名称
                    "tool_input": data.get("input"),  # 工具输入参数
                },
            }
        # 7. 工具调用结束事件
        elif kind == "on_tool_end" and node in TEAM_MEMBERS:
            ydata = {
                "event": "tool_call_result",
                "data": {
                    "tool_call_id": f"{workflow_id}_{node}_{name}_{run_id}",  # 唯一工具调用ID
                    "tool_name": name,  # 工具名称
                    "tool_result": data["output"].content if data.get("output") else "",  # 工具执行结果
                },
            }
        else:
            # 跳过不需要处理的事件
            continue
            
        # 生成事件数据
        yield ydata

    # 如果是切换到planner的情况，在工作流结束时发送最终事件
    if is_handoff_case:
        yield {
            "event": "end_of_workflow",
            "data": {
                "workflow_id": workflow_id,  # 工作流ID
                "messages": [
                    # 将消息对象转换为字典格式
                    convert_message_to_dict(msg)
                    for msg in data["output"].get("messages", [])
                ],
            },
        }
