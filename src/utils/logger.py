"""Logging Utility Module

Provides centralized logging configuration for the project.
"""

import logging
import os
from datetime import datetime
from typing import Optional

# 全局日志配置
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# 日志级别映射
LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}

def setup_logger(name: str = 'main', 
                level: str = 'INFO', 
                log_file: Optional[str] = None,
                log_dir: str = 'logs') -> logging.Logger:
    """设置并返回配置好的日志记录器
    
    Args:
        name: 日志记录器名称
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 日志文件名，如果为None则不写入文件
        log_dir: 日志文件目录
    
    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    
    # 避免重复添加处理器
    if logger.handlers:
        return logger
    
    # 设置日志级别
    log_level = LOG_LEVELS.get(level.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # 创建格式化器
    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    
    # 添加控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 添加文件处理器（如果指定了日志文件）
    if log_file:
        # 确保日志目录存在
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # 如果没有扩展名，添加.log
        if not log_file.endswith('.log'):
            log_file += '.log'
        
        log_path = os.path.join(log_dir, log_file)
        
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str = 'main') -> logging.Logger:
    """获取日志记录器
    
    Args:
        name: 日志记录器名称
    
    Returns:
        日志记录器实例
    """
    logger = logging.getLogger(name)
    
    # 如果日志记录器还没有配置，使用默认配置
    if not logger.handlers:
        return setup_logger(name)
    
    return logger

def create_daily_log_file(base_name: str = 'app') -> str:
    """创建基于日期的日志文件名
    
    Args:
        base_name: 基础文件名
    
    Returns:
        带日期的日志文件名
    """
    today = datetime.now().strftime('%Y-%m-%d')
    return f"{base_name}_{today}.log"

def setup_module_logger(module_name: str, 
                       level: str = 'INFO',
                       enable_file_logging: bool = True) -> logging.Logger:
    """为模块设置专用日志记录器
    
    Args:
        module_name: 模块名称
        level: 日志级别
        enable_file_logging: 是否启用文件日志
    
    Returns:
        配置好的日志记录器
    """
    log_file = None
    if enable_file_logging:
        # 从模块名生成日志文件名
        clean_name = module_name.replace('.', '_').replace('src_', '')
        log_file = create_daily_log_file(clean_name)
    
    return setup_logger(module_name, level, log_file)

class LoggerMixin:
    """日志记录器混入类
    
    为类提供便捷的日志记录功能
    """
    
    @property
    def logger(self) -> logging.Logger:
        """获取当前类的日志记录器"""
        if not hasattr(self, '_logger'):
            class_name = f"{self.__class__.__module__}.{self.__class__.__name__}"
            self._logger = get_logger(class_name)
        return self._logger

# 预配置的日志记录器
def get_spider_logger() -> logging.Logger:
    """获取爬虫模块的日志记录器"""
    return setup_module_logger('spider', enable_file_logging=True)

def get_analyzer_logger() -> logging.Logger:
    """获取分析器模块的日志记录器"""
    return setup_module_logger('analyzer', enable_file_logging=True)

def get_score_analyzer_logger() -> logging.Logger:
    """获取评分分析器模块的日志记录器"""
    return setup_module_logger('score_analyzer', enable_file_logging=True)