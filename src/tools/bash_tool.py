import logging
import subprocess
from typing import Annotated
from langchain_core.tools import tool
from .decorators import log_io

# 初始化日志记录器
logger = logging.getLogger(__name__)


@tool  # 使用LangChain的工具装饰器，将函数注册为工具
@log_io  # 使用自定义装饰器记录输入输出
def bash_tool(
    cmd: Annotated[str, "The bash command to be executed."],  # 使用Annotated提供参数说明
):
    """Use this to execute bash command and do necessary operations."""
    """使用此工具执行Bash命令并完成必要的操作。"""
    # 记录即将执行的命令
    logger.info(f"Executing Bash Command: {cmd}")
    try:
        # 执行命令并捕获输出
        # shell=True：允许执行shell命令
        # check=True：如果命令返回非零退出码，则抛出异常
        # text=True：以文本模式处理输出（而非字节）
        # capture_output=True：捕获标准输出和标准错误
        result = subprocess.run(
            cmd, shell=True, check=True, text=True, capture_output=True
        )
        # 返回标准输出作为结果
        return result.stdout
    except subprocess.CalledProcessError as e:
        # 如果命令执行失败，返回错误信息
        # 包含退出码、标准输出和标准错误
        error_message = f"Command failed with exit code {e.returncode}.\nStdout: {e.stdout}\nStderr: {e.stderr}"
        logger.error(error_message)
        return error_message
    except Exception as e:
        # 捕获其他任何异常
        error_message = f"Error executing command: {str(e)}"
        logger.error(error_message)
        return error_message


# 当直接运行此文件时执行测试代码
if __name__ == "__main__":
    print(bash_tool.invoke("ls -all"))  # 测试执行ls命令并打印结果
