import logging
from typing import Annotated

from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from .decorators import log_io

from src.crawler import Crawler

# 初始化日志记录器
logger = logging.getLogger(__name__)


@tool  # 使用LangChain的工具装饰器，将函数注册为工具
@log_io  # 使用自定义装饰器记录输入输出
def crawl_tool(
    url: Annotated[str, "The url to crawl."],  # 要抓取的URL，使用Annotated提供参数说明
) -> HumanMessage:
    """Use this to crawl a url and get a readable content in markdown format."""
    """使用此工具抓取指定URL的内容，并获取可读性良好的markdown格式文本。"""
    try:
        # 创建爬虫实例
        crawler = Crawler()
        # 执行网页抓取
        article = crawler.crawl(url)
        # 将抓取到的文章转换为消息格式返回
        # 使用role=user让内容在对话中以用户角色呈现
        return {"role": "user", "content": article.to_message()}
    except BaseException as e:
        # 捕获任何可能的异常
        error_msg = f"Failed to crawl. Error: {repr(e)}"
        # 记录错误日志
        logger.error(error_msg)
        # 返回错误信息
        return error_msg
