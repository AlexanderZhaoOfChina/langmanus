from langgraph.prebuilt import create_react_agent

from src.prompts import apply_prompt_template
from src.tools import (
    bash_tool,
    browser_tool,
    crawl_tool,
    python_repl_tool,
    tavily_tool,
)

from .llm import get_llm_by_type
from src.config.agents import AGENT_LLM_MAP

# 创建智能体，使用配置好的LLM类型
# 使用ReAct (Reasoning + Acting) 模式创建各种专业智能体

# 创建研究员智能体
# 职责：收集信息、执行网络搜索和内容抓取
# 工具：tavily_tool（网络搜索）和crawl_tool（网页内容抓取）
research_agent = create_react_agent(
    get_llm_by_type(AGENT_LLM_MAP["researcher"]),  # 获取研究员配置的LLM模型
    tools=[tavily_tool, crawl_tool],               # 配置可用工具
    prompt=lambda state: apply_prompt_template("researcher", state),  # 动态应用研究员提示模板
)

# 创建程序员智能体
# 职责：执行代码、运行命令行操作、解决技术问题
# 工具：python_repl_tool（Python代码执行）和bash_tool（命令行操作）
coder_agent = create_react_agent(
    get_llm_by_type(AGENT_LLM_MAP["coder"]),       # 获取程序员配置的LLM模型
    tools=[python_repl_tool, bash_tool],           # 配置可用工具
    prompt=lambda state: apply_prompt_template("coder", state),  # 动态应用程序员提示模板
)

# 创建浏览器智能体
# 职责：执行网页浏览、交互和信息提取
# 工具：browser_tool（浏览器自动化工具）
browser_agent = create_react_agent(
    get_llm_by_type(AGENT_LLM_MAP["browser"]),     # 获取浏览器智能体配置的LLM模型
    tools=[browser_tool],                          # 配置可用工具
    prompt=lambda state: apply_prompt_template("browser", state),  # 动态应用浏览器提示模板
)
