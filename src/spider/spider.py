"""Article Spider Module

Provides web scraping functionality for articles with support for:
- Single configuration crawling
- Batch crawling
- Incremental crawling
- Time-filtered crawling
"""

import requests
import json
import time
import math
import os
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from dotenv import load_dotenv

from ..utils import get_logger, ensure_dir, save_json, save_csv

# 加载环境变量
load_dotenv()

@dataclass
class SpiderConfig:
    """爬虫配置类"""
    section_id: str
    topic_class_id: str
    name: str  # 配置名称，用于标识不同的爬取目标
    description: str = ""  # 配置描述
    base_url: str = "https://www.hiascend.com/ascendgateway/ascendservice/devCenter/bbs/servlet/get-topic-list"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'section_id': self.section_id,
            'topic_class_id': self.topic_class_id,
            'name': self.name,
            'description': self.description,
            'base_url': self.base_url
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SpiderConfig':
        """从字典创建配置"""
        return cls(
            section_id=data['section_id'],
            topic_class_id=data['topic_class_id'],
            name=data['name'],
            description=data.get('description', ''),
            base_url=data.get('base_url', 'https://www.hiascend.com/ascendgateway/ascendservice/devCenter/bbs/servlet/get-topic-list')
        )

class ArticleSpider:
    """文章爬虫类"""
    
    def __init__(self, data_dir: str = 'data'):
        self.base_url = "https://www.hiascend.com/ascendgateway/ascendservice/devCenter/bbs/servlet/get-topic-list"
        self.logger = get_logger(__name__)
        
        # 从环境变量读取 cookies 字符串并解析为字典
        cookies_str = os.getenv('COOKIES', '')
        self.cookies = self._parse_cookies(cookies_str)
        
        # 确保 data 目录存在
        self.data_dir = data_dir
        ensure_dir(self.data_dir)
        
        # 增量爬取相关属性
        self.existing_article_ids: Set[str] = set()  # 已存在的文章ID集合
        self.last_crawl_time: Optional[datetime] = None  # 上次爬取时间
        self.crawl_history_file = os.path.join(self.data_dir, 'crawl_history.json')  # 爬取历史文件
        
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://www.hiascend.com/"
        }
        self.all_articles = []
        
        # 预定义的爬取配置
        self.configs = {
            "original": SpiderConfig(
                section_id="0157117713657966001",
                topic_class_id="0672154839186846001",
                name="原始配置",
                description="原始的爬取配置"
            ),
            "new_target": SpiderConfig(
                section_id="0101178462695499013",
                topic_class_id="0697178462739351002",
                name="新目标配置",
                description="新增的爬取目标配置"
            )
        }
        
        # 当前使用的配置
        self.current_config = self.configs["original"]
    
    def _parse_cookies(self, cookies_str: str) -> Dict[str, str]:
        """解析 cookies 字符串为字典"""
        cookies = {}
        if cookies_str:
            for cookie in cookies_str.split('; '):
                if '=' in cookie:
                    key, value = cookie.split('=', 1)
                    cookies[key] = value
        return cookies
    
    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """解析时间戳字符串为 datetime 对象"""
        if not timestamp_str:
            return None
        try:
            # 尝试解析毫秒时间戳
            timestamp = int(timestamp_str)
            if timestamp > 1e12:  # 毫秒时间戳
                timestamp = timestamp / 1000
            return datetime.fromtimestamp(timestamp, tz=timezone.utc)
        except (ValueError, TypeError):
            return None
    
    def _is_article_newer(self, article: Dict[str, Any], since_time: Optional[datetime]) -> bool:
        """检查文章是否比指定时间更新"""
        if since_time is None:
            return True
        
        # 检查发布时间和更新时间
        publish_time = self._parse_timestamp(article.get('publish_time', ''))
        update_time = self._parse_timestamp(article.get('update_time', ''))
        
        # 如果有更新时间，优先使用更新时间；否则使用发布时间
        article_time = update_time if update_time else publish_time
        
        if article_time is None:
            return True  # 如果无法解析时间，默认包含
        
        return article_time > since_time
    
    def load_existing_data(self, filename: str = None) -> List[Dict[str, Any]]:
        """加载已存在的文章数据"""
        if filename is None:
            filename = "articles_all.json"
        
        filepath = os.path.join(self.data_dir, filename)
        
        if not os.path.exists(filepath):
            self.logger.info(f"数据文件 {filepath} 不存在，将进行全量爬取")
            return []
        
        try:
            articles = load_json(filepath)
            
            # 更新已存在的文章ID集合
            self.existing_article_ids = {article.get('id', '') for article in articles if article.get('id')}
            self.logger.info(f"加载了 {len(articles)} 篇已存在文章，{len(self.existing_article_ids)} 个唯一ID")
            
            return articles
        except Exception as e:
            self.logger.error(f"加载数据文件失败: {e}")
            return []
    
    def load_crawl_history(self) -> None:
        """加载爬取历史记录"""
        if not os.path.exists(self.crawl_history_file):
            return
        
        try:
            history = load_json(self.crawl_history_file)
            
            last_crawl_str = history.get('last_crawl_time')
            if last_crawl_str:
                self.last_crawl_time = datetime.fromisoformat(last_crawl_str)
                self.logger.info(f"上次爬取时间: {self.last_crawl_time}")
        except Exception as e:
            self.logger.error(f"加载爬取历史失败: {e}")
    
    def save_crawl_history(self) -> None:
        """保存爬取历史记录"""
        history = {
            'last_crawl_time': datetime.now(timezone.utc).isoformat(),
            'total_articles': len(self.all_articles)
        }
        
        try:
            save_json(self.crawl_history_file, history)
            self.logger.info(f"爬取历史已保存到 {self.crawl_history_file}")
        except Exception as e:
            self.logger.error(f"保存爬取历史失败: {e}")
    
    def filter_new_articles(self, articles: List[Dict[str, Any]], since_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """过滤出新文章（去重 + 时间过滤）"""
        new_articles = []
        duplicate_count = 0
        time_filtered_count = 0
        
        for article in articles:
            article_id = article.get('id', '')
            
            # 去重检查
            if article_id and article_id in self.existing_article_ids:
                duplicate_count += 1
                continue
            
            # 时间过滤检查
            if not self._is_article_newer(article, since_time):
                time_filtered_count += 1
                continue
            
            new_articles.append(article)
            if article_id:
                self.existing_article_ids.add(article_id)
        
        if duplicate_count > 0:
            self.logger.info(f"过滤掉 {duplicate_count} 篇重复文章")
        if time_filtered_count > 0:
            self.logger.info(f"过滤掉 {time_filtered_count} 篇旧文章")
        
        return new_articles
        
    def get_page_data(self, page_index: int, page_size: int = 12, config: Optional[SpiderConfig] = None) -> Dict[str, Any]:
        """获取指定页的数据"""
        if config is None:
            config = self.current_config
            
        params = {
            "sectionId": config.section_id,
            "filterCondition": "1",
            "pageIndex": str(page_index),
            "pageSize": str(page_size),
            "topicClassId": config.topic_class_id
        }
        
        try:
            response = requests.get(
                self.base_url,
                params=params,
                headers=self.headers,
                cookies=self.cookies,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"请求失败: {e}")
            return {}
    
    def parse_articles(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """解析文章列表"""
        articles = []
        if "data" in data and "resultList" in data["data"]:
            for item in data["data"]["resultList"]:
                article = {
                    "id": item.get("postId", ""),
                    "title": item.get("title", ""),
                    "content": item.get("content", ""),
                    "content_summary": item.get("contentSummary", ""),
                    "author_id": item.get("authorId", ""),
                    "author_name": item.get("nickName", ""),
                    "author_icon": item.get("authorIcon", ""),
                    "create_time": item.get("createTime", ""),
                    "update_time": item.get("lastEditTime", ""),
                    "publish_time": item.get("dateline", ""),
                    "last_post_time": item.get("lastPostTime", ""),
                    "views": item.get("views", 0),
                    "replies": item.get("replies", 0),
                    "comments": item.get("comments", 0),
                    "likes": item.get("likes", 0),
                    "favorites": item.get("favTimes", 0),
                    "shares": item.get("shareTimes", 0),
                    "topic_id": item.get("topicId", ""),
                    "topic_class_id": item.get("topicClassId", ""),
                    "topic_class_name": item.get("topicClassName", ""),
                    "section_id": item.get("sectionId", ""),
                    "section_name": item.get("sectionName", ""),
                    "section_icon": item.get("sectionIcon", ""),
                    "level_name": item.get("levelName", ""),
                    "is_top": item.get("top", 0) == 1,
                    "is_digest": item.get("digest", 0) == 1,
                    "is_recommend": item.get("recommend", 0) == 1,
                    "is_hot": item.get("hot", 0) == 1,
                    "is_question": item.get("isQuestion", 0) == 1,
                    "is_solved": item.get("solved", 0) == 1,
                    "is_edited": item.get("isEdited", 0) == 1,
                    "pictures": item.get("pictures", 0),
                    "attachments": item.get("attachments", 0),
                    "status": item.get("status", 0),
                    "tags": item.get("topicTagInfoList", []),
                    "upload_info": item.get("uploadInfoList", []),
                    "additional_option": item.get("additionalOption", {})
                }
                articles.append(article)
        return articles
    
    def set_config(self, config_name: str) -> bool:
        """设置当前使用的配置"""
        if config_name in self.configs:
            self.current_config = self.configs[config_name]
            self.logger.info(f"已切换到配置: {self.current_config.name}")
            return True
        else:
            self.logger.warning(f"配置 '{config_name}' 不存在")
            return False
    
    def add_config(self, config_name: str, section_id: str, topic_class_id: str, name: str, description: str = "") -> None:
        """添加新的爬取配置"""
        self.configs[config_name] = SpiderConfig(
            section_id=section_id,
            topic_class_id=topic_class_id,
            name=name,
            description=description
        )
        self.logger.info(f"已添加配置: {name}")
    
    def list_configs(self) -> None:
        """列出所有可用的配置"""
        self.logger.info("可用的爬取配置:")
        for key, config in self.configs.items():
            current_mark = " (当前)" if config == self.current_config else ""
            self.logger.info(f"  {key}: {config.name}{current_mark}")
            if config.description:
                self.logger.info(f"    描述: {config.description}")
            self.logger.info(f"    sectionId: {config.section_id}")
            self.logger.info(f"    topicClassId: {config.topic_class_id}")
    
    def get_all_articles(self, max_pages: int = 100, config: Optional[SpiderConfig] = None, 
                        incremental: bool = False, since_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """获取所有文章
        
        Args:
            max_pages: 最大爬取页数
            config: 爬取配置
            incremental: 是否启用增量模式
            since_time: 增量爬取的起始时间
        """
        if config is None:
            config = self.current_config
            
        page_index = 1
        total_count = 0  # 初始值，后续会根据实际数据更新
        page_size = 12
        new_articles_count = 0
        
        # 如果启用增量模式，使用上次爬取时间或指定时间
        filter_time = since_time if since_time else (self.last_crawl_time if incremental else None)
        
        mode_desc = "增量" if incremental else "全量"
        self.logger.info(f"开始{mode_desc}获取文章列表... (使用配置: {config.name})")
        if filter_time:
            self.logger.info(f"过滤时间: {filter_time}")
        
        while page_index <= max_pages:
            self.logger.info(f"正在获取第 {page_index} 页数据...")
            
            # 获取当前页数据
            data = self.get_page_data(page_index, page_size, config)
            
            # 检查返回数据是否有效
            if not data or "data" not in data or "resultList" not in data["data"]:
                self.logger.warning(f"第 {page_index} 页数据获取失败或格式不正确，尝试下一页...")
                page_index += 1
                continue
            
            # 更新总文章数
            if "totalCount" in data["data"]:
                total_count = data["data"]["totalCount"]
                total_pages = math.ceil(total_count / page_size)
                self.logger.info(f"总文章数: {total_count}, 总页数: {total_pages}")
                
                # 如果已经获取的页数超过总页数，则停止
                if page_index > total_pages:
                    self.logger.info(f"已获取所有 {total_pages} 页数据")
                    break
            
            # 解析文章列表
            articles = self.parse_articles(data)
            
            # 如果启用增量模式，过滤新文章
            if incremental or filter_time:
                filtered_articles = self.filter_new_articles(articles, filter_time)
                new_articles_count += len(filtered_articles)
                self.all_articles.extend(filtered_articles)
                self.logger.info(f"第 {page_index} 页获取到 {len(articles)} 篇文章，过滤后新增 {len(filtered_articles)} 篇")
                
                # 如果连续几页都没有新文章，可以考虑提前结束（增量模式优化）
                if incremental and len(filtered_articles) == 0 and page_index > 3:
                    self.logger.info("连续多页无新文章，增量爬取可能已完成")
            else:
                self.all_articles.extend(articles)
                new_articles_count += len(articles)
                self.logger.info(f"第 {page_index} 页获取到 {len(articles)} 篇文章")
            
            # 如果当前页的文章数量小于请求的页面大小，说明已经是最后一页
            if len(articles) < page_size:
                self.logger.info(f"当前页文章数({len(articles)})小于页面大小({page_size})，可能是最后一页")
                break
                
            # 增加页码
            page_index += 1
            
            # 添加延时，避免请求过于频繁
            time.sleep(1)
        
        self.logger.info(f"{mode_desc}获取完成，共获取到 {len(self.all_articles)} 篇文章")
        if incremental:
            self.logger.info(f"本次新增 {new_articles_count} 篇文章")
        return self.all_articles
    
    def get_all_articles_batch(self, config_names: List[str] = None, max_pages: int = 100, 
                                  incremental: bool = False, since_time: Optional[datetime] = None) -> Dict[str, List[Dict[str, Any]]]:
        """批量获取多个配置的文章
        
        Args:
            config_names: 配置名称列表
            max_pages: 最大爬取页数
            incremental: 是否启用增量模式
            since_time: 增量爬取的起始时间
        """
        if config_names is None:
            config_names = list(self.configs.keys())
        
        results = {}
        for config_name in config_names:
            if config_name not in self.configs:
                self.logger.warning(f"配置 '{config_name}' 不存在，跳过")
                continue
                
            self.logger.info(f"\n开始爬取配置: {config_name}")
            config = self.configs[config_name]
            
            # 临时清空文章列表
            temp_articles = self.all_articles.copy()
            self.all_articles = []
            
            # 获取当前配置的文章
            articles = self.get_all_articles(max_pages, config, incremental, since_time)
            results[config_name] = articles.copy()
            
            # 恢复原有文章列表并合并新文章
            self.all_articles = temp_articles + articles
            
            self.logger.info(f"配置 '{config_name}' 爬取完成，获得 {len(articles)} 篇文章")
            time.sleep(2)  # 配置间延时
        
        return results
    
    def incremental_crawl(self, config_names: List[str] = None, max_pages: int = 100, 
                         load_existing: bool = True) -> Dict[str, List[Dict[str, Any]]]:
        """增量爬取便捷方法
        
        Args:
            config_names: 配置名称列表
            max_pages: 最大爬取页数
            load_existing: 是否加载已存在的数据
        """
        self.logger.info("=== 开始增量爬取 ===")
        
        # 加载爬取历史
        self.load_crawl_history()
        
        # 加载已存在的数据（如果需要）
        existing_articles = []
        if load_existing:
            existing_articles = self.load_existing_data()
        
        # 执行增量爬取
        results = self.get_all_articles_batch(config_names, max_pages, incremental=True)
        
        # 合并已存在的数据和新数据
        if existing_articles:
            self.logger.info(f"合并 {len(existing_articles)} 篇已存在文章")
            # 将已存在的文章添加到结果中（避免重复）
            all_new_articles = []
            for articles in results.values():
                all_new_articles.extend(articles)
            
            # 合并去重
            combined_articles = existing_articles + all_new_articles
            self.all_articles = combined_articles
        
        # 保存爬取历史
        self.save_crawl_history()
        
        return results
    
    def merge_and_save_incremental(self, new_results: Dict[str, List[Dict[str, Any]]], 
                                  base_filename: str = "articles") -> None:
        """合并增量数据并保存
        
        Args:
            new_results: 新爬取的结果
            base_filename: 基础文件名
        """
        # 加载已存在的数据
        existing_articles = self.load_existing_data(f"{base_filename}_all.json")
        
        # 合并新数据
        all_new_articles = []
        for articles in new_results.values():
            all_new_articles.extend(articles)
        
        # 去重合并
        existing_ids = {article.get('id', '') for article in existing_articles if article.get('id')}
        unique_new_articles = [article for article in all_new_articles 
                              if article.get('id', '') not in existing_ids]
        
        combined_articles = existing_articles + unique_new_articles
        
        self.logger.info(f"合并数据: 已存在 {len(existing_articles)} 篇，新增 {len(unique_new_articles)} 篇，总计 {len(combined_articles)} 篇")
        
        # 保存合并后的数据
        self.save_to_json(f"{base_filename}_all.json", combined_articles)
        self.save_to_csv(f"{base_filename}_all.csv", combined_articles)
        
        # 保存各配置的增量数据
        for config_name, articles in new_results.items():
            if articles:
                json_filename = f"{base_filename}_{config_name}_incremental.json"
                csv_filename = f"{base_filename}_{config_name}_incremental.csv"
                
                self.save_to_json(json_filename, articles)
                self.save_to_csv(csv_filename, articles)
                
                self.logger.info(f"配置 '{config_name}' 的 {len(articles)} 篇增量文章已保存")
    
    def save_to_json(self, filename: str = "articles.json", articles: List[Dict[str, Any]] = None) -> None:
        """将文章列表保存为JSON文件"""
        if articles is None:
            articles = self.all_articles
        
        # 确保文件保存到 data 目录
        filepath = os.path.join(self.data_dir, filename)
        save_json(filepath, articles)
        self.logger.info(f"文章列表已保存到 {filepath}")
    
    def save_to_csv(self, filename: str = "articles.csv", articles: List[Dict[str, Any]] = None) -> None:
        """将文章列表保存为CSV文件"""
        if articles is None:
            articles = self.all_articles
            
        if not articles:
            self.logger.warning("没有文章数据可保存")
            return
        
        # 确保文件保存到 data 目录
        filepath = os.path.join(self.data_dir, filename)
        save_csv(filepath, articles)
        self.logger.info(f"文章列表已保存到 {filepath}")
    
    def save_batch_results(self, batch_results: Dict[str, List[Dict[str, Any]]], base_filename: str = "articles") -> None:
        """保存批量爬取的结果"""
        for config_name, articles in batch_results.items():
            if articles:
                json_filename = f"{base_filename}_{config_name}.json"
                csv_filename = f"{base_filename}_{config_name}.csv"
                
                self.save_to_json(json_filename, articles)
                self.save_to_csv(csv_filename, articles)
                
                self.logger.info(f"配置 '{config_name}' 的 {len(articles)} 篇文章已保存")
        
        # 保存合并的结果
        all_articles = []
        for articles in batch_results.values():
            all_articles.extend(articles)
        
        if all_articles:
            self.save_to_json(f"{base_filename}_all.json", all_articles)
            self.save_to_csv(f"{base_filename}_all.csv", all_articles)
            self.logger.info(f"所有配置的文章已合并保存到 data 目录，共 {len(all_articles)} 篇文章")