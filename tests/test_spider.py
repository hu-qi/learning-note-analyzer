#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爬虫模块测试
"""

import unittest
import tempfile
import os
import json
from unittest.mock import Mock, patch, MagicMock

# 添加src目录到Python路径
import sys
from pathlib import Path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from src.spider.spider import ArticleSpider, SpiderConfig


class TestSpiderConfig(unittest.TestCase):
    """测试SpiderConfig类"""
    
    def test_spider_config_creation(self):
        """测试SpiderConfig创建"""
        config = SpiderConfig(
            name="test_config",
            base_url="https://example.com",
            cookies="test_cookies"
        )
        
        self.assertEqual(config.name, "test_config")
        self.assertEqual(config.base_url, "https://example.com")
        self.assertEqual(config.cookies, "test_cookies")
        self.assertIsInstance(config.headers, dict)
    
    def test_spider_config_to_dict(self):
        """测试SpiderConfig转换为字典"""
        config = SpiderConfig(
            name="test_config",
            base_url="https://example.com",
            cookies="test_cookies"
        )
        
        config_dict = config.to_dict()
        self.assertIsInstance(config_dict, dict)
        self.assertEqual(config_dict['name'], "test_config")
        self.assertEqual(config_dict['base_url'], "https://example.com")
    
    def test_spider_config_from_dict(self):
        """测试从字典创建SpiderConfig"""
        config_dict = {
            'name': 'test_config',
            'base_url': 'https://example.com',
            'cookies': 'test_cookies',
            'headers': {'User-Agent': 'test'}
        }
        
        config = SpiderConfig.from_dict(config_dict)
        self.assertEqual(config.name, "test_config")
        self.assertEqual(config.base_url, "https://example.com")
        self.assertEqual(config.headers['User-Agent'], "test")


class TestArticleSpider(unittest.TestCase):
    """测试ArticleSpider类"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.spider = ArticleSpider(data_dir=self.temp_dir)
    
    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_spider_initialization(self):
        """测试爬虫初始化"""
        self.assertEqual(self.spider.data_dir, self.temp_dir)
        self.assertIsInstance(self.spider.configs, dict)
        self.assertIsInstance(self.spider.crawl_history, dict)
    
    def test_parse_cookies(self):
        """测试cookies解析"""
        cookies_str = "key1=value1; key2=value2"
        cookies_dict = self.spider._parse_cookies(cookies_str)
        
        expected = {'key1': 'value1', 'key2': 'value2'}
        self.assertEqual(cookies_dict, expected)
    
    def test_parse_cookies_empty(self):
        """测试空cookies解析"""
        cookies_dict = self.spider._parse_cookies("")
        self.assertEqual(cookies_dict, {})
        
        cookies_dict = self.spider._parse_cookies(None)
        self.assertEqual(cookies_dict, {})
    
    def test_add_config(self):
        """测试添加配置"""
        config = SpiderConfig(
            name="test_config",
            base_url="https://example.com",
            cookies="test_cookies"
        )
        
        self.spider.add_config(config)
        self.assertIn("test_config", self.spider.configs)
        self.assertEqual(self.spider.configs["test_config"].base_url, "https://example.com")
    
    def test_set_config(self):
        """测试设置配置"""
        # 先添加一个配置
        config = SpiderConfig(
            name="test_config",
            base_url="https://example.com",
            cookies="test_cookies"
        )
        self.spider.add_config(config)
        
        # 修改配置
        success = self.spider.set_config("test_config", base_url="https://newurl.com")
        self.assertTrue(success)
        self.assertEqual(self.spider.configs["test_config"].base_url, "https://newurl.com")
        
        # 尝试修改不存在的配置
        success = self.spider.set_config("nonexistent", base_url="https://test.com")
        self.assertFalse(success)
    
    def test_list_configs(self):
        """测试列出配置"""
        # 添加几个配置
        config1 = SpiderConfig(name="config1", base_url="https://example1.com")
        config2 = SpiderConfig(name="config2", base_url="https://example2.com")
        
        self.spider.add_config(config1)
        self.spider.add_config(config2)
        
        configs = self.spider.list_configs()
        self.assertEqual(len(configs), 2)
        self.assertIn("config1", configs)
        self.assertIn("config2", configs)
    
    def test_filter_new_articles(self):
        """测试过滤新文章"""
        # 模拟历史记录
        self.spider.crawl_history = {
            "test_config": {
                "last_crawl_time": "2024-01-01 00:00:00",
                "crawled_articles": ["article1", "article2"]
            }
        }
        
        # 模拟文章列表
        articles = [
            {"title": "article1", "url": "url1"},
            {"title": "article2", "url": "url2"},
            {"title": "article3", "url": "url3"},
        ]
        
        new_articles = self.spider._filter_new_articles(articles, "test_config")
        
        # 应该只返回新文章
        self.assertEqual(len(new_articles), 1)
        self.assertEqual(new_articles[0]["title"], "article3")
    
    def test_save_to_json(self):
        """测试保存JSON文件"""
        test_data = [{"title": "test", "content": "test content"}]
        filename = "test_articles.json"
        
        self.spider.save_to_json(test_data, filename)
        
        # 检查文件是否创建
        file_path = os.path.join(self.temp_dir, filename)
        self.assertTrue(os.path.exists(file_path))
        
        # 检查文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        
        self.assertEqual(loaded_data, test_data)
    
    def test_save_to_csv(self):
        """测试保存CSV文件"""
        test_data = [
            {"title": "test1", "content": "content1"},
            {"title": "test2", "content": "content2"}
        ]
        filename = "test_articles.csv"
        
        self.spider.save_to_csv(test_data, filename)
        
        # 检查文件是否创建
        file_path = os.path.join(self.temp_dir, filename)
        self.assertTrue(os.path.exists(file_path))
    
    @patch('requests.get')
    def test_get_page_data_success(self, mock_get):
        """测试成功获取页面数据"""
        # 模拟成功的HTTP响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_get.return_value = mock_response
        
        config = SpiderConfig(
            name="test_config",
            base_url="https://example.com",
            cookies="test_cookies"
        )
        
        result = self.spider.get_page_data(config, page=1)
        
        self.assertEqual(result, {"data": "test"})
        mock_get.assert_called_once()
    
    @patch('requests.get')
    def test_get_page_data_failure(self, mock_get):
        """测试获取页面数据失败"""
        # 模拟失败的HTTP响应
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        config = SpiderConfig(
            name="test_config",
            base_url="https://example.com",
            cookies="test_cookies"
        )
        
        result = self.spider.get_page_data(config, page=1)
        
        self.assertIsNone(result)
    
    def test_parse_articles(self):
        """测试解析文章"""
        # 模拟API响应数据
        page_data = {
            "data": {
                "list": [
                    {
                        "title": "Test Article 1",
                        "author_name": "Author 1",
                        "content_summary": "Summary 1",
                        "view_count": 100,
                        "like_count": 10,
                        "reply_count": 5
                    },
                    {
                        "title": "Test Article 2",
                        "author_name": "Author 2",
                        "content_summary": "Summary 2",
                        "view_count": 200,
                        "like_count": 20,
                        "reply_count": 10
                    }
                ]
            }
        }
        
        articles = self.spider.parse_articles(page_data, "test_task")
        
        self.assertEqual(len(articles), 2)
        self.assertEqual(articles[0]["title"], "Test Article 1")
        self.assertEqual(articles[0]["task_name"], "test_task")
        self.assertEqual(articles[1]["title"], "Test Article 2")
    
    def test_parse_articles_empty(self):
        """测试解析空数据"""
        page_data = {"data": {"list": []}}
        articles = self.spider.parse_articles(page_data, "test_task")
        self.assertEqual(len(articles), 0)
        
        # 测试None数据
        articles = self.spider.parse_articles(None, "test_task")
        self.assertEqual(len(articles), 0)
    
    def test_load_and_save_crawl_history(self):
        """测试加载和保存爬取历史"""
        # 创建测试历史数据
        test_history = {
            "test_config": {
                "last_crawl_time": "2024-01-01 00:00:00",
                "crawled_articles": ["article1", "article2"]
            }
        }
        
        # 保存历史
        self.spider.crawl_history = test_history
        self.spider._save_crawl_history()
        
        # 创建新的爬虫实例并加载历史
        new_spider = ArticleSpider(data_dir=self.temp_dir)
        
        self.assertEqual(new_spider.crawl_history, test_history)


if __name__ == '__main__':
    unittest.main()