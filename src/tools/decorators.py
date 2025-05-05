import logging
import functools
from typing import Any, Callable, Type, TypeVar

# 初始化日志记录器
logger = logging.getLogger(__name__)

# 定义泛型类型变量，用于类型注解
T = TypeVar("T")


def log_io(func: Callable) -> Callable:
    """
    A decorator that logs the input parameters and output of a tool function.

    Args:
        func: The tool function to be decorated

    Returns:
        The wrapped function with input/output logging
    """
    """
    一个装饰器，用于记录工具函数的输入参数和输出结果。
    
    参数:
        func: 要被装饰的工具函数
        
    返回:
        带有输入/输出日志记录功能的包装函数
    """

    @functools.wraps(func)  # 保留原函数的元数据（如名称、文档字符串等）
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # 记录输入参数
        func_name = func.__name__  # 获取函数名称
        # 将所有参数格式化为字符串
        params = ", ".join(
            [*(str(arg) for arg in args), *(f"{k}={v}" for k, v in kwargs.items())]
        )
        # 记录调用信息
        logger.debug(f"Tool {func_name} called with parameters: {params}")

        # 执行原函数
        result = func(*args, **kwargs)

        # 记录输出结果
        logger.debug(f"Tool {func_name} returned: {result}")

        # 返回结果
        return result

    return wrapper


class LoggedToolMixin:
    """A mixin class that adds logging functionality to any tool."""
    """一个混入类，为任何工具添加日志记录功能。"""

    def _log_operation(self, method_name: str, *args: Any, **kwargs: Any) -> None:
        """Helper method to log tool operations."""
        """辅助方法，用于记录工具操作。"""
        # 获取工具名称（移除"Logged"前缀，仅保留原始工具名）
        tool_name = self.__class__.__name__.replace("Logged", "")
        # 将所有参数格式化为字符串
        params = ", ".join(
            [*(str(arg) for arg in args), *(f"{k}={v}" for k, v in kwargs.items())]
        )
        # 记录调用信息
        logger.debug(f"Tool {tool_name}.{method_name} called with parameters: {params}")

    def _run(self, *args: Any, **kwargs: Any) -> Any:
        """Override _run method to add logging."""
        """重写_run方法以添加日志记录。"""
        # 调用日志记录辅助方法
        self._log_operation("_run", *args, **kwargs)
        # 调用父类的_run方法执行实际操作
        result = super()._run(*args, **kwargs)
        # 记录返回结果
        logger.debug(
            f"Tool {self.__class__.__name__.replace('Logged', '')} returned: {result}"
        )
        # 返回结果
        return result


def create_logged_tool(base_tool_class: Type[T]) -> Type[T]:
    """
    Factory function to create a logged version of any tool class.

    Args:
        base_tool_class: The original tool class to be enhanced with logging

    Returns:
        A new class that inherits from both LoggedToolMixin and the base tool class
    """
    """
    工厂函数，用于创建任何工具类的带日志记录版本。
    
    参数:
        base_tool_class: 要增强日志功能的原始工具类
        
    返回:
        一个新类，继承自LoggedToolMixin和基础工具类
    """

    # 创建新类，同时继承LoggedToolMixin和基础工具类
    class LoggedTool(LoggedToolMixin, base_tool_class):
        pass

    # 为新类设置更具描述性的名称
    LoggedTool.__name__ = f"Logged{base_tool_class.__name__}"
    return LoggedTool
