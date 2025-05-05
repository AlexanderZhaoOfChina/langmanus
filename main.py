"""
Entry point script for the LangGraph Demo.
LangManus系统的入口点脚本，用于启动LangGraph演示。
"""

from src.workflow import run_agent_workflow

if __name__ == "__main__":
    import sys

    # 获取用户查询
    # 如果命令行参数存在，则使用命令行参数作为用户查询
    # 例如：python main.py 查询天气预报
    if len(sys.argv) > 1:
        user_query = " ".join(sys.argv[1:])  # 将所有命令行参数连接成一个查询字符串
    else:
        # 如果没有命令行参数，则通过命令行交互方式获取用户输入
        user_query = input("Enter your query: ")

    # 运行智能体工作流
    # 传入用户查询并启用调试模式
    # debug=True 表示启用详细的日志记录，帮助开发者了解系统运行状态
    result = run_agent_workflow(user_input=user_query, debug=True)

    # 打印对话历史
    # 遍历结果中的所有消息，显示每个消息的角色和内容
    print("\n=== Conversation History ===")
    for message in result["messages"]:
        role = message.type  # 获取消息的角色类型（如user、assistant等）
        print(f"\n[{role.upper()}]: {message.content}")  # 以格式化方式显示消息
