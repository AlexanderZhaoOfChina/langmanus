import logging
from typing import Annotated
from langchain_core.tools import tool
from langchain_experimental.utilities import PythonREPL
from .decorators import log_io

# 初始化Python代码执行环境和日志记录器
# PythonREPL提供了一个读取-求值-打印循环环境，允许执行Python代码
repl = PythonREPL()
# 创建日志记录器实例
logger = logging.getLogger(__name__)


@tool  # 使用LangChain的工具装饰器，将函数注册为工具
@log_io  # 使用自定义装饰器记录输入输出
def python_repl_tool(
    code: Annotated[
        str, "The python code to execute to do further analysis or calculation."
    ],  # 要执行的Python代码，使用Annotated提供参数说明
):
    """Use this to execute python code and do data analysis or calculation. If you want to see the output of a value,
    you should print it out with `print(...)`. This is visible to the user."""
    """
    使用此工具执行Python代码并进行数据分析或计算。如果你想看到某个值的输出，
    应该使用`print(...)`将其打印出来。这些输出对用户是可见的。
    """
    # 记录即将执行Python代码的信息
    logger.info("Executing Python code")
    try:
        # 在REPL环境中执行代码
        result = repl.run(code)
        # 记录代码执行成功的信息
        logger.info("Code execution successful")
    except BaseException as e:
        # 捕获所有可能的异常
        error_msg = f"Failed to execute. Error: {repr(e)}"
        # 记录错误日志
        logger.error(error_msg)
        # 返回错误信息
        return error_msg
    # 格式化执行结果
    # 包括原始代码和执行输出
    result_str = f"Successfully executed:\n```python\n{code}\n```\nStdout: {result}"
    return result_str
