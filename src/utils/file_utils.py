"""File Utility Functions

Provides common file operations for the project.
"""

import os
import json
import csv
from typing import Any, Dict, List
from .logger import get_logger

logger = get_logger(__name__)

def ensure_dir(directory: str) -> None:
    """确保目录存在，如果不存在则创建"""
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        logger.info(f"创建目录: {directory}")

def save_json(filepath: str, data: Any, indent: int = 2) -> None:
    """保存数据为JSON文件"""
    try:
        # 确保目录存在
        ensure_dir(os.path.dirname(filepath))
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
        logger.info(f"JSON文件已保存: {filepath}")
    except Exception as e:
        logger.error(f"保存JSON文件失败 {filepath}: {e}")
        raise

def load_json(filepath: str) -> Any:
    """从JSON文件加载数据"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"JSON文件已加载: {filepath}")
        return data
    except FileNotFoundError:
        logger.warning(f"JSON文件不存在: {filepath}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"JSON文件格式错误 {filepath}: {e}")
        raise
    except Exception as e:
        logger.error(f"加载JSON文件失败 {filepath}: {e}")
        raise

def save_csv(filepath: str, data: List[Dict[str, Any]]) -> None:
    """保存数据为CSV文件"""
    if not data:
        logger.warning("没有数据可保存到CSV")
        return
    
    try:
        # 确保目录存在
        ensure_dir(os.path.dirname(filepath))
        
        # 获取所有字段名
        fieldnames = set()
        for item in data:
            for key in item.keys():
                fieldnames.add(key)
        fieldnames = sorted(fieldnames)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for item in data:
                # 处理列表和字典类型的字段，转换为字符串
                row = {}
                for key, value in item.items():
                    if isinstance(value, (list, dict)):
                        row[key] = json.dumps(value, ensure_ascii=False)
                    else:
                        row[key] = value
                writer.writerow(row)
        
        logger.info(f"CSV文件已保存: {filepath}")
    except Exception as e:
        logger.error(f"保存CSV文件失败 {filepath}: {e}")
        raise

def load_csv(filepath: str) -> List[Dict[str, Any]]:
    """从CSV文件加载数据"""
    try:
        data = []
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 尝试解析JSON字符串字段
                parsed_row = {}
                for key, value in row.items():
                    try:
                        # 尝试解析为JSON
                        parsed_value = json.loads(value)
                        parsed_row[key] = parsed_value
                    except (json.JSONDecodeError, TypeError):
                        # 如果不是JSON，保持原值
                        parsed_row[key] = value
                data.append(parsed_row)
        
        logger.info(f"CSV文件已加载: {filepath}, 共 {len(data)} 条记录")
        return data
    except FileNotFoundError:
        logger.warning(f"CSV文件不存在: {filepath}")
        return []
    except Exception as e:
        logger.error(f"加载CSV文件失败 {filepath}: {e}")
        raise

def get_file_size(filepath: str) -> int:
    """获取文件大小（字节）"""
    try:
        return os.path.getsize(filepath)
    except OSError:
        return 0

def file_exists(filepath: str) -> bool:
    """检查文件是否存在"""
    return os.path.exists(filepath) and os.path.isfile(filepath)

def dir_exists(directory: str) -> bool:
    """检查目录是否存在"""
    return os.path.exists(directory) and os.path.isdir(directory)