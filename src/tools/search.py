import logging
from langchain_community.tools.tavily_search import TavilySearchResults
from src.config import TAVILY_MAX_RESULTS
from .decorators import create_logged_tool

# 初始化日志记录器
logger = logging.getLogger(__name__)

# 初始化带日志记录功能的Tavily搜索工具
# Tavily是一个专为AI设计的搜索API，提供结构化的搜索结果
# 使用create_logged_tool装饰器为TavilySearchResults添加日志记录功能
LoggedTavilySearch = create_logged_tool(TavilySearchResults)
# 实例化搜索工具，设置名称和最大结果数量
# max_results参数从配置中获取，控制每次搜索返回的最大结果数
tavily_tool = LoggedTavilySearch(name="tavily_search", max_results=TAVILY_MAX_RESULTS)
