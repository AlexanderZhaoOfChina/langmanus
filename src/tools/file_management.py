import logging
from langchain_community.tools.file_management import WriteFileTool
from .decorators import create_logged_tool

# 初始化日志记录器
logger = logging.getLogger(__name__)

# 初始化带日志记录功能的文件管理工具
# 使用create_logged_tool装饰器为WriteFileTool添加日志记录功能
LoggedWriteFile = create_logged_tool(WriteFileTool)
# 实例化文件写入工具
# 该工具允许智能体将内容写入文件系统，常用于保存爬取的数据、生成的报告等
write_file_tool = LoggedWriteFile()
