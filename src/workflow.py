import logging
from src.config import TEAM_MEMBERS
from src.graph import build_graph

# 配置日志系统
# 设置日志级别为INFO，格式包含时间、模块名、日志级别和消息内容
logging.basicConfig(
    level=logging.INFO,  # 默认日志级别为INFO
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def enable_debug_logging():
    """Enable debug level logging for more detailed execution information."""
    """启用DEBUG级别的日志，以获取更详细的执行信息。"""
    # 将src包及其子模块的日志级别设置为DEBUG
    logging.getLogger("src").setLevel(logging.DEBUG)


# 获取当前模块的日志记录器
logger = logging.getLogger(__name__)

# 创建工作流图
# 调用build_graph函数构建完整的智能体工作流图
graph = build_graph()


def run_agent_workflow(user_input: str, debug: bool = False):
    """Run the agent workflow with the given user input.

    Args:
        user_input: The user's query or request
        debug: If True, enables debug level logging

    Returns:
        The final state after the workflow completes
    """
    """
    运行智能体工作流，处理用户输入并返回结果。
    
    参数:
        user_input: 用户的查询或请求文本
        debug: 如果为True，则启用DEBUG级别的日志记录，提供更详细的执行信息
        
    返回:
        工作流完成后的最终状态
    """
    # 验证输入不能为空
    if not user_input:
        raise ValueError("Input could not be empty")

    # 如果启用了debug模式，则设置更详细的日志级别
    if debug:
        enable_debug_logging()

    # 记录工作流开始的信息
    logger.info(f"Starting workflow with user input: {user_input}")
    
    # 调用工作流图的invoke方法，传入初始状态
    result = graph.invoke(
        {
            # 常量设置
            "TEAM_MEMBERS": TEAM_MEMBERS,  # 团队成员列表，包含所有可用的智能体名称
            
            # 运行时变量
            "messages": [{"role": "user", "content": user_input}],  # 初始化消息历史，包含用户输入
            "deep_thinking_mode": True,  # 启用深度思考模式，使用更复杂的推理模型
            "search_before_planning": True,  # 启用规划前搜索，为规划提供更多上下文信息
        }
    )
    
    # 以DEBUG级别记录工作流的最终状态
    logger.debug(f"Final workflow state: {result}")
    # 记录工作流成功完成的信息
    logger.info("Workflow completed successfully")
    # 返回工作流的最终状态
    return result


# 如果直接运行此文件（而非作为模块导入）
if __name__ == "__main__":
    # 输出工作流图的Mermaid格式图表，用于可视化工作流结构
    print(graph.get_graph().draw_mermaid())
