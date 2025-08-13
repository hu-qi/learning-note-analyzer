"""Configuration Utility Module

Provides configuration management functionality.
"""

import os
import yaml
from typing import Any, Dict, Optional
from .logger import get_logger
from .file_utils import file_exists, load_json

logger = get_logger(__name__)

# 全局配置缓存
_config_cache: Optional[Dict[str, Any]] = None

def load_config(config_path: str = 'config/config.yaml', use_default: bool = True) -> Dict[str, Any]:
    """加载配置文件
    
    Args:
        config_path: 配置文件路径
        use_default: 是否在失败时使用默认配置
    
    Returns:
        配置字典
    """
    global _config_cache
    
    if not file_exists(config_path):
        logger.warning(f"配置文件不存在: {config_path}")
        if use_default:
            return get_default_config()
        else:
            return {}
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        
        if use_default:
            # 合并默认配置
            default_config = get_default_config()
            merged_config = merge_configs(default_config, config)
            _config_cache = merged_config
            logger.info(f"配置文件已加载: {config_path}")
            return merged_config
        else:
            logger.info(f"配置文件已加载: {config_path}")
            return config
    
    except yaml.YAMLError as e:
        logger.error(f"配置文件格式错误 {config_path}: {e}")
        if use_default:
            return get_default_config()
        else:
            return {}
    except Exception as e:
        logger.error(f"加载配置文件失败 {config_path}: {e}")
        if use_default:
            return get_default_config()
        else:
            return {}

def get_config(key: str = None, default: Any = None) -> Any:
    """获取配置值
    
    Args:
        key: 配置键，支持点号分隔的嵌套键，如 'spider.max_pages'
        default: 默认值
    
    Returns:
        配置值
    """
    global _config_cache
    
    if _config_cache is None:
        _config_cache = load_config()
    
    if key is None:
        return _config_cache
    
    # 支持嵌套键访问
    keys = key.split('.')
    value = _config_cache
    
    try:
        for k in keys:
            value = value[k]
        return value
    except (KeyError, TypeError):
        return default

def get_config_value(config: Dict[str, Any], key: str, default: Any = None) -> Any:
    """从配置字典中获取值
    
    Args:
        config: 配置字典
        key: 配置键，支持点号分隔的嵌套键
        default: 默认值
    
    Returns:
        配置值
    """
    keys = key.split('.')
    value = config
    
    try:
        for k in keys:
            value = value[k]
        return value
    except (KeyError, TypeError):
        return default

def set_config(key: str, value: Any) -> None:
    """设置配置值（仅在内存中）
    
    Args:
        key: 配置键
        value: 配置值
    """
    global _config_cache
    
    if _config_cache is None:
        _config_cache = load_config()
    
    keys = key.split('.')
    config = _config_cache
    
    # 创建嵌套结构
    for k in keys[:-1]:
        if k not in config:
            config[k] = {}
        config = config[k]
    
    config[keys[-1]] = value
    logger.info(f"配置已更新: {key} = {value}")

def set_config_value(config: Dict[str, Any], key: str, value: Any) -> None:
    """在配置字典中设置值
    
    Args:
        config: 配置字典
        key: 配置键，支持点号分隔的嵌套键
        value: 配置值
    """
    keys = key.split('.')
    current = config
    
    # 创建嵌套结构
    for k in keys[:-1]:
        if k not in current:
            current[k] = {}
        current = current[k]
    
    current[keys[-1]] = value

def save_config(config: Dict[str, Any], config_path: str = 'config/config.yaml') -> None:
    """保存配置到文件
    
    Args:
        config: 配置字典
        config_path: 配置文件路径
    """
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True, indent=2)
        
        logger.info(f"配置已保存到: {config_path}")
    except Exception as e:
        logger.error(f"保存配置文件失败 {config_path}: {e}")
        raise

def merge_configs(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """合并配置字典
    
    Args:
        base: 基础配置
        override: 覆盖配置
    
    Returns:
        合并后的配置
    """
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_configs(result[key], value)
        else:
            result[key] = value
    
    return result

def get_default_config() -> Dict[str, Any]:
    """获取默认配置
    
    Returns:
        默认配置字典
    """
    return {
        'app': {
            'name': 'Data Analysis Toolkit',
            'version': '1.0.0',
            'debug': False
        },
        'logging': {
            'level': 'INFO',
            'enable_file_logging': True,
            'log_dir': 'logs',
            'max_log_files': 10
        },
        'spider': {
            'max_pages': 100,
            'page_size': 12,
            'request_timeout': 10,
            'request_delay': 1,
            'batch_delay': 2,
            'data_dir': 'data',
            'base_url': 'https://www.hiascend.com/ascendgateway/ascendservice/devCenter/bbs/servlet/get-topic-list',
            'headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Referer': 'https://www.hiascend.com/'
            },
            'configs': {
                'original': {
                    'section_id': '0157117713657966001',
                    'topic_class_id': '0672154839186846001',
                    'name': '原始配置',
                    'description': '原始的爬取配置'
                },
                'new_target': {
                    'section_id': '0101178462695499013',
                    'topic_class_id': '0697178462739351002',
                    'name': '新目标配置',
                    'description': '新增的爬取目标配置'
                }
            }
        },
        'analyzer': {
            'data_dir': 'data',
            'llm': {
                'api_url': 'https://api.modelarts-maas.com/v1/chat/completions',
                'model': 'deepseek-v3',
                'max_tokens': 1000,
                'temperature': 0.7,
                'timeout': 30
            },
            'scoring': {
                'criteria': {
                    'content_completeness': 0.3,
                    'structure_clarity': 0.2,
                    'practicality': 0.2,
                    'expression_quality': 0.15,
                    'interactivity': 0.15
                },
                'max_score': 10,
                'min_score': 1
            }
        },
        'score_analyzer': {
            'data_dir': 'data',
            'output_dir': 'data',
            'min_checkin_count': 1,
            'sort_by': 'average_score',
            'sort_order': 'desc'
        }
    }

def reload_config(config_path: str = 'config/config.yaml') -> Dict[str, Any]:
    """重新加载配置文件
    
    Args:
        config_path: 配置文件路径
    
    Returns:
        重新加载的配置
    """
    global _config_cache
    _config_cache = None
    return load_config(config_path)

def get_env_config() -> Dict[str, Any]:
    """从环境变量获取配置
    
    Returns:
        环境变量配置
    """
    env_config = {}
    
    # 日志级别
    if os.getenv('LOG_LEVEL'):
        env_config['logging'] = {'level': os.getenv('LOG_LEVEL')}
    
    # 调试模式
    if os.getenv('DEBUG'):
        env_config['app'] = {'debug': os.getenv('DEBUG').lower() == 'true'}
    
    # 数据目录
    if os.getenv('DATA_DIR'):
        env_config['spider'] = {'data_dir': os.getenv('DATA_DIR')}
        env_config['analyzer'] = {'data_dir': os.getenv('DATA_DIR')}
        env_config['score_analyzer'] = {'data_dir': os.getenv('DATA_DIR')}
    
    # LLM API配置
    if os.getenv('LLM_API_URL'):
        if 'analyzer' not in env_config:
            env_config['analyzer'] = {}
        env_config['analyzer']['llm'] = {'api_url': os.getenv('LLM_API_URL')}
    
    if os.getenv('LLM_API_KEY'):
        if 'analyzer' not in env_config:
            env_config['analyzer'] = {}
        if 'llm' not in env_config['analyzer']:
            env_config['analyzer']['llm'] = {}
        env_config['analyzer']['llm']['api_key'] = os.getenv('LLM_API_KEY')
    
    return env_config

def init_config(config_path: str = 'config/config.yaml') -> Dict[str, Any]:
    """初始化配置系统
    
    Args:
        config_path: 配置文件路径
    
    Returns:
        初始化后的配置
    """
    # 加载基础配置
    config = load_config(config_path)
    
    # 合并环境变量配置
    env_config = get_env_config()
    if env_config:
        config = merge_configs(config, env_config)
        logger.info("已合并环境变量配置")
    
    return config