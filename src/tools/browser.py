import asyncio

from pydantic import BaseModel, Field
from typing import Optional, ClassVar, Type
from langchain.tools import BaseTool
from browser_use import AgentHistoryList, Browser, BrowserConfig
from browser_use import Agent as BrowserAgent
from src.agents.llm import vl_llm
from src.tools.decorators import create_logged_tool
from src.config import CHROME_INSTANCE_PATH

# 保存全局浏览器实例
expected_browser = None

# 如果配置了Chrome实例路径，则使用指定的Chrome
if CHROME_INSTANCE_PATH:
    # 创建浏览器实例，使用指定的Chrome可执行文件路径
    expected_browser = Browser(
        config=BrowserConfig(chrome_instance_path=CHROME_INSTANCE_PATH)
    )


# 定义浏览器工具的输入模型
class BrowserUseInput(BaseModel):
    """Input for WriteFileTool."""
    """浏览器工具的输入模型。"""

    # 用户给浏览器的指令，如"打开Google并搜索..."
    instruction: str = Field(..., description="The instruction to use browser")


# 定义浏览器工具类
class BrowserTool(BaseTool):
    # 工具名称，用于在系统中标识此工具
    name: ClassVar[str] = "browser"
    # 参数模式，使用前面定义的输入模型
    args_schema: Type[BaseModel] = BrowserUseInput
    # 工具描述，告诉用户如何使用此工具
    description: ClassVar[str] = (
        "Use this tool to interact with web browsers. Input should be a natural language description of what you want to do with the browser, such as 'Go to google.com and search for browser-use', or 'Navigate to Reddit and find the top post about AI'."
    )

    # 浏览器代理实例，用于执行实际的浏览操作
    _agent: Optional[BrowserAgent] = None

    def _run(self, instruction: str) -> str:
        """Run the browser task synchronously."""
        """同步执行浏览器任务。"""
        # 创建浏览器代理，使用视觉语言模型(VL模型)以支持图像理解
        self._agent = BrowserAgent(
            task=instruction,  # 设置任务指令
            llm=vl_llm,        # 使用视觉语言模型
            browser=expected_browser,  # 使用预先配置的浏览器实例
        )
        try:
            # 创建新的事件循环
            loop = asyncio.new_event_loop()
            # 设置当前线程的事件循环
            asyncio.set_event_loop(loop)
            try:
                # 在事件循环中运行浏览器代理的异步任务
                result = loop.run_until_complete(self._agent.run())
                # 处理不同类型的结果并格式化返回
                return (
                    str(result)  # 如果是简单类型，直接转为字符串
                    if not isinstance(result, AgentHistoryList)
                    else result.final_result  # 如果是历史列表，返回最终结果
                )
            finally:
                # 确保事件循环被关闭
                loop.close()
        except Exception as e:
            # 处理任何异常并返回错误信息
            return f"Error executing browser task: {str(e)}"

    async def _arun(self, instruction: str) -> str:
        """Run the browser task asynchronously."""
        """异步执行浏览器任务。"""
        # 创建浏览器代理
        self._agent = BrowserAgent(
            task=instruction,  # 设置任务指令
            llm=vl_llm         # 使用视觉语言模型
        )
        try:
            # 直接异步运行浏览器代理
            result = await self._agent.run()
            # 处理不同类型的结果并格式化返回
            return (
                str(result)  # 如果是简单类型，直接转为字符串
                if not isinstance(result, AgentHistoryList)
                else result.final_result  # 如果是历史列表，返回最终结果
            )
        except Exception as e:
            # 处理任何异常并返回错误信息
            return f"Error executing browser task: {str(e)}"


# 使用装饰器创建带日志记录功能的浏览器工具
BrowserTool = create_logged_tool(BrowserTool)
# 实例化浏览器工具
browser_tool = BrowserTool()
