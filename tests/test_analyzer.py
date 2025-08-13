#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学习笔记分析器模块测试
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

from src.analyzer.analyzer import LearningNoteAnalyzer


class TestLearningNoteAnalyzer(unittest.TestCase):
    """测试LearningNoteAnalyzer类"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        
        # 创建测试文章数据
        self.test_articles = [
            {
                "title": "DAY1 学习总结",
                "author_name": "张三",
                "task_name": "DAY1",
                "content_summary": "今天学习了Python基础知识，收获很大。",
                "view_count": 100,
                "like_count": 10,
                "reply_count": 5,
                "publish_time": "2024-01-01 12:00:00"
            },
            {
                "title": "DAY2 实践心得",
                "author_name": "李四",
                "task_name": "DAY2",
                "content_summary": "通过实际编程练习，对面向对象有了更深的理解。",
                "view_count": 150,
                "like_count": 15,
                "reply_count": 8,
                "publish_time": "2024-01-02 14:00:00"
            },
            {
                "title": "普通文章",
                "author_name": "王五",
                "task_name": "其他",
                "content_summary": "这是一篇普通文章，不是学习笔记。",
                "view_count": 50,
                "like_count": 5,
                "reply_count": 2,
                "publish_time": "2024-01-03 10:00:00"
            },
            {
                "title": "DAY1 补充学习",
                "author_name": "张三",
                "task_name": "DAY1",
                "content_summary": "对昨天的学习内容进行了补充和深化。",
                "view_count": 80,
                "like_count": 8,
                "reply_count": 3,
                "publish_time": "2024-01-04 16:00:00"
            }
        ]
        
        # 保存测试数据到文件
        articles_file = os.path.join(self.temp_dir, 'all_articles.json')
        with open(articles_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_articles, f, ensure_ascii=False, indent=2)
    
    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    def test_analyzer_initialization(self):
        """测试分析器初始化"""
        analyzer = LearningNoteAnalyzer(data_dir=self.temp_dir)
        
        self.assertEqual(analyzer.data_dir, self.temp_dir)
        self.assertEqual(len(analyzer.articles), 4)
        self.assertEqual(len(analyzer.learning_notes), 3)  # 只有包含DAY的文章
    
    def test_load_articles(self):
        """测试加载文章数据"""
        analyzer = LearningNoteAnalyzer(data_dir=self.temp_dir)
        
        self.assertEqual(len(analyzer.articles), 4)
        self.assertEqual(analyzer.articles[0]['title'], "DAY1 学习总结")
    
    def test_load_articles_file_not_exist(self):
        """测试文章文件不存在的情况"""
        empty_dir = tempfile.mkdtemp()
        try:
            analyzer = LearningNoteAnalyzer(data_dir=empty_dir)
            self.assertEqual(len(analyzer.articles), 0)
            self.assertEqual(len(analyzer.learning_notes), 0)
        finally:
            import shutil
            shutil.rmtree(empty_dir, ignore_errors=True)
    
    def test_filter_learning_notes(self):
        """测试筛选学习笔记"""
        analyzer = LearningNoteAnalyzer(data_dir=self.temp_dir)
        
        # 应该筛选出3篇包含DAY的文章
        self.assertEqual(len(analyzer.learning_notes), 3)
        
        # 检查筛选结果
        titles = [note['title'] for note in analyzer.learning_notes]
        self.assertIn("DAY1 学习总结", titles)
        self.assertIn("DAY2 实践心得", titles)
        self.assertIn("DAY1 补充学习", titles)
        self.assertNotIn("普通文章", titles)
    
    def test_analyze_task_checkin(self):
        """测试任务打卡情况分析"""
        analyzer = LearningNoteAnalyzer(data_dir=self.temp_dir)
        task_stats = analyzer.analyze_task_checkin()
        
        # 应该有2个任务（DAY1和DAY2）
        self.assertEqual(len(task_stats), 2)
        self.assertIn("DAY1", task_stats)
        self.assertIn("DAY2", task_stats)
        
        # 检查DAY1的统计
        day1_stats = task_stats["DAY1"]
        self.assertEqual(day1_stats['total_checkins'], 2)  # 张三的两篇文章
        self.assertEqual(day1_stats['unique_participants'], 1)  # 只有张三
        self.assertEqual(day1_stats['total_views'], 180)  # 100 + 80
        self.assertEqual(day1_stats['total_likes'], 18)  # 10 + 8
        
        # 检查DAY2的统计
        day2_stats = task_stats["DAY2"]
        self.assertEqual(day2_stats['total_checkins'], 1)  # 李四的一篇文章
        self.assertEqual(day2_stats['unique_participants'], 1)  # 只有李四
    
    def test_analyze_user_checkin(self):
        """测试用户打卡情况分析"""
        analyzer = LearningNoteAnalyzer(data_dir=self.temp_dir)
        user_stats = analyzer.analyze_user_checkin()
        
        # 应该有2个用户（张三和李四）
        self.assertEqual(len(user_stats), 2)
        self.assertIn("张三", user_stats)
        self.assertIn("李四", user_stats)
        
        # 检查张三的统计
        zhangsan_stats = user_stats["张三"]
        self.assertEqual(zhangsan_stats['total_checkins'], 2)
        self.assertEqual(zhangsan_stats['unique_tasks'], 1)  # 只完成了DAY1
        self.assertEqual(zhangsan_stats['completion_rate'], 50.0)  # 2个任务中完成了1个
        self.assertIn("DAY1", zhangsan_stats['completed_tasks'])
        
        # 检查李四的统计
        lisi_stats = user_stats["李四"]
        self.assertEqual(lisi_stats['total_checkins'], 1)
        self.assertEqual(lisi_stats['unique_tasks'], 1)  # 完成了DAY2
        self.assertEqual(lisi_stats['completion_rate'], 50.0)  # 2个任务中完成了1个
        self.assertIn("DAY2", lisi_stats['completed_tasks'])
    
    def test_parse_llm_result_json(self):
        """测试解析大模型JSON结果"""
        analyzer = LearningNoteAnalyzer(data_dir=self.temp_dir)
        
        # 测试标准JSON格式
        json_result = '{"score": 85, "comment": "内容详实，思考深入"}'
        score, comment = analyzer._parse_llm_result(json_result)
        self.assertEqual(score, 85)
        self.assertEqual(comment, "内容详实，思考深入")
    
    def test_parse_llm_result_with_markdown(self):
        """测试解析带markdown的大模型结果"""
        analyzer = LearningNoteAnalyzer(data_dir=self.temp_dir)
        
        # 测试带```json标记的格式
        markdown_result = '```json\n{"score": 90, "comment": "优秀的学习总结"}\n```'
        score, comment = analyzer._parse_llm_result(markdown_result)
        self.assertEqual(score, 90)
        self.assertEqual(comment, "优秀的学习总结")
    
    def test_parse_llm_result_regex_fallback(self):
        """测试正则表达式解析后备方案"""
        analyzer = LearningNoteAnalyzer(data_dir=self.temp_dir)
        
        # 测试非标准格式
        text_result = 'score: 75, comment: "还需要更多思考"'
        score, comment = analyzer._parse_llm_result(text_result)
        self.assertEqual(score, 75)
        self.assertEqual(comment, "还需要更多思考")
    
    def test_parse_llm_result_invalid(self):
        """测试解析无效结果"""
        analyzer = LearningNoteAnalyzer(data_dir=self.temp_dir)
        
        # 测试完全无效的结果
        invalid_result = "这是一个无效的结果"
        score, comment = analyzer._parse_llm_result(invalid_result)
        self.assertEqual(score, 60)  # 默认分数
        self.assertIn("无法提取评语", comment)
    
    @patch('openai.OpenAI')
    def test_call_llm_for_scoring_success(self, mock_openai):
        """测试成功调用大模型评分"""
        # 模拟OpenAI客户端
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"score": 88, "comment": "很好的学习笔记"}'
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        analyzer = LearningNoteAnalyzer(data_dir=self.temp_dir)
        analyzer.client = mock_client
        
        score, comment = analyzer.call_llm_for_scoring("测试内容", "测试标题")
        
        self.assertEqual(score, 88)
        self.assertEqual(comment, "很好的学习笔记")
        mock_client.chat.completions.create.assert_called_once()
    
    def test_call_llm_for_scoring_no_client(self):
        """测试没有大模型客户端的情况"""
        analyzer = LearningNoteAnalyzer(data_dir=self.temp_dir)
        analyzer.client = None
        
        score, comment = analyzer.call_llm_for_scoring("测试内容", "测试标题")
        
        self.assertEqual(score, 60)  # 默认分数
        self.assertIn("大模型服务不可用", comment)
    
    @patch('openai.OpenAI')
    def test_call_llm_for_scoring_exception(self, mock_openai):
        """测试大模型调用异常"""
        # 模拟OpenAI客户端抛出异常
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API错误")
        mock_openai.return_value = mock_client
        
        analyzer = LearningNoteAnalyzer(data_dir=self.temp_dir)
        analyzer.client = mock_client
        
        score, comment = analyzer.call_llm_for_scoring("测试内容", "测试标题")
        
        self.assertEqual(score, 60)  # 默认分数
        self.assertIn("评分服务暂时不可用", comment)
        self.assertIn("API错误", comment)
    
    @patch('src.analyzer.analyzer.LearningNoteAnalyzer.call_llm_for_scoring')
    @patch('time.sleep')  # 模拟sleep以加速测试
    def test_score_notes(self, mock_sleep, mock_call_llm):
        """测试笔记评分"""
        # 模拟大模型评分结果
        mock_call_llm.side_effect = [
            (85, "很好的DAY1总结"),
            (90, "优秀的DAY2心得"),
            (80, "不错的DAY1补充")
        ]
        
        analyzer = LearningNoteAnalyzer(data_dir=self.temp_dir)
        note_scores = analyzer.score_notes()
        
        # 检查结果
        self.assertEqual(len(note_scores), 2)  # 两个作者
        self.assertIn("张三", note_scores)
        self.assertIn("李四", note_scores)
        
        # 检查张三的评分（两篇笔记）
        zhangsan_scores = note_scores["张三"]
        self.assertEqual(len(zhangsan_scores['notes']), 2)
        self.assertEqual(zhangsan_scores['total_score'], 165)  # 85 + 80
        self.assertEqual(zhangsan_scores['avg_score'], 82.5)  # (85 + 80) / 2
        self.assertEqual(zhangsan_scores['best_note']['score'], 85)  # 最高分
        self.assertEqual(zhangsan_scores['worst_note']['score'], 80)  # 最低分
        
        # 检查李四的评分（一篇笔记）
        lisi_scores = note_scores["李四"]
        self.assertEqual(len(lisi_scores['notes']), 1)
        self.assertEqual(lisi_scores['total_score'], 90)
        self.assertEqual(lisi_scores['avg_score'], 90.0)
    
    @patch('src.analyzer.analyzer.LearningNoteAnalyzer.score_notes')
    def test_generate_report(self, mock_score_notes):
        """测试生成分析报告"""
        # 模拟评分结果
        mock_score_notes.return_value = {
            "张三": {
                "notes": [{"task_name": "DAY1", "score": 85, "comment": "很好"}],
                "total_score": 85,
                "avg_score": 85.0,
                "best_note": {"task_name": "DAY1", "score": 85},
                "worst_note": {"task_name": "DAY1", "score": 85}
            }
        }
        
        analyzer = LearningNoteAnalyzer(data_dir=self.temp_dir)
        report = analyzer.generate_report()
        
        # 检查报告结构
        self.assertIn('task_stats', report)
        self.assertIn('user_stats', report)
        self.assertIn('note_scores', report)
        self.assertIn('summary', report)
        
        # 检查摘要信息
        summary = report['summary']
        self.assertEqual(summary['total_articles'], 4)
        self.assertEqual(summary['total_learning_notes'], 3)
        self.assertEqual(summary['total_tasks'], 2)
        self.assertEqual(summary['total_users'], 2)
    
    def test_print_report(self):
        """测试打印报告（简单测试，主要检查不抛异常）"""
        analyzer = LearningNoteAnalyzer(data_dir=self.temp_dir)
        
        # 创建一个简单的报告
        report = {
            'task_stats': {'DAY1': {'total_checkins': 1, 'unique_participants': 1, 
                                   'avg_content_length': 100, 'total_views': 100, 
                                   'total_likes': 10, 'total_replies': 5}},
            'user_stats': {'张三': {'total_checkins': 1, 'unique_tasks': 1, 
                                  'completion_rate': 50.0, 'avg_content_length': 100,
                                  'total_views': 100, 'total_likes': 10, 
                                  'completed_tasks_sorted': ['DAY1']}},
            'note_scores': {'张三': {'avg_score': 85.0, 'total_score': 85, 
                                   'notes': [{'task_name': 'DAY1', 'score': 85}],
                                   'best_note': {'task_name': 'DAY1', 'score': 85},
                                   'worst_note': {'task_name': 'DAY1', 'score': 85}}},
            'summary': {'total_articles': 4, 'total_learning_notes': 3, 
                       'total_tasks': 2, 'total_users': 2}
        }
        
        # 这个测试主要确保print_report不会抛出异常
        try:
            analyzer.print_report(report)
        except Exception as e:
            self.fail(f"print_report raised an exception: {e}")


if __name__ == '__main__':
    unittest.main()