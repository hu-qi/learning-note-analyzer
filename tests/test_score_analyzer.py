#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
评分分析器模块测试
"""

import unittest
import tempfile
import os
import json
import csv
from unittest.mock import patch, mock_open

# 添加src目录到Python路径
import sys
from pathlib import Path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from src.score_analyzer.score_analyzer import ScoreAnalyzer


class TestScoreAnalyzer(unittest.TestCase):
    """测试ScoreAnalyzer类"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        
        # 创建测试评分数据
        self.test_scores = {
            "张三": {
                "notes": [
                    {
                        "task_name": "DAY1",
                        "title": "DAY1 学习总结",
                        "score": 85,
                        "comment": "内容详实，思考深入",
                        "content_length": 500,
                        "view_count": 100,
                        "like_count": 10,
                        "reply_count": 5
                    },
                    {
                        "task_name": "DAY2",
                        "title": "DAY2 实践心得",
                        "score": 90,
                        "comment": "实践与理论结合很好",
                        "content_length": 600,
                        "view_count": 120,
                        "like_count": 15,
                        "reply_count": 8
                    }
                ],
                "total_score": 175,
                "avg_score": 87.5,
                "best_note": {
                    "task_name": "DAY2",
                    "score": 90
                },
                "worst_note": {
                    "task_name": "DAY1",
                    "score": 85
                }
            },
            "李四": {
                "notes": [
                    {
                        "task_name": "DAY1",
                        "title": "DAY1 学习笔记",
                        "score": 75,
                        "comment": "基础掌握较好",
                        "content_length": 400,
                        "view_count": 80,
                        "like_count": 8,
                        "reply_count": 3
                    },
                    {
                        "task_name": "DAY3",
                        "title": "DAY3 进阶学习",
                        "score": 80,
                        "comment": "有一定进步",
                        "content_length": 450,
                        "view_count": 90,
                        "like_count": 9,
                        "reply_count": 4
                    },
                    {
                        "task_name": "DAY4",
                        "title": "DAY4 综合练习",
                        "score": 88,
                        "comment": "综合运用能力强",
                        "content_length": 550,
                        "view_count": 110,
                        "like_count": 12,
                        "reply_count": 6
                    }
                ],
                "total_score": 243,
                "avg_score": 81.0,
                "best_note": {
                    "task_name": "DAY4",
                    "score": 88
                },
                "worst_note": {
                    "task_name": "DAY1",
                    "score": 75
                }
            },
            "王五": {
                "notes": [
                    {
                        "task_name": "DAY1",
                        "title": "DAY1 初学体验",
                        "score": 70,
                        "comment": "需要加强理解",
                        "content_length": 300,
                        "view_count": 60,
                        "like_count": 5,
                        "reply_count": 2
                    }
                ],
                "total_score": 70,
                "avg_score": 70.0,
                "best_note": {
                    "task_name": "DAY1",
                    "score": 70
                },
                "worst_note": {
                    "task_name": "DAY1",
                    "score": 70
                }
            }
        }
        
        # 保存测试数据到文件
        scores_file = os.path.join(self.temp_dir, 'note_scores.json')
        with open(scores_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_scores, f, ensure_ascii=False, indent=2)
    
    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_analyzer_initialization(self):
        """测试分析器初始化"""
        analyzer = ScoreAnalyzer(data_dir=self.temp_dir)
        
        self.assertEqual(analyzer.data_dir, self.temp_dir)
        self.assertEqual(len(analyzer.scores), 3)  # 三个作者
        self.assertIn("张三", analyzer.scores)
        self.assertIn("李四", analyzer.scores)
        self.assertIn("王五", analyzer.scores)
    
    def test_load_scores_file_not_exist(self):
        """测试评分文件不存在的情况"""
        empty_dir = tempfile.mkdtemp()
        try:
            analyzer = ScoreAnalyzer(data_dir=empty_dir)
            self.assertEqual(len(analyzer.scores), 0)
        finally:
            import shutil
            shutil.rmtree(empty_dir, ignore_errors=True)
    
    def test_analyze_authors(self):
        """测试分析作者统计数据"""
        analyzer = ScoreAnalyzer(data_dir=self.temp_dir)
        author_stats = analyzer.analyze_authors()
        
        # 检查作者数量
        self.assertEqual(len(author_stats), 3)
        
        # 检查张三的统计
        zhangsan_stats = author_stats["张三"]
        self.assertEqual(zhangsan_stats['checkin_count'], 2)
        self.assertEqual(zhangsan_stats['total_score'], 175)
        self.assertEqual(zhangsan_stats['avg_score'], 87.5)
        self.assertEqual(zhangsan_stats['max_score'], 90)
        self.assertEqual(zhangsan_stats['min_score'], 85)
        self.assertEqual(zhangsan_stats['total_content_length'], 1100)  # 500 + 600
        self.assertEqual(zhangsan_stats['avg_content_length'], 550.0)
        self.assertEqual(zhangsan_stats['total_views'], 220)  # 100 + 120
        self.assertEqual(zhangsan_stats['total_likes'], 25)  # 10 + 15
        self.assertEqual(zhangsan_stats['total_replies'], 13)  # 5 + 8
        
        # 检查李四的统计
        lisi_stats = author_stats["李四"]
        self.assertEqual(lisi_stats['checkin_count'], 3)
        self.assertEqual(lisi_stats['total_score'], 243)
        self.assertEqual(lisi_stats['avg_score'], 81.0)
        self.assertEqual(lisi_stats['max_score'], 88)
        self.assertEqual(lisi_stats['min_score'], 75)
        
        # 检查王五的统计
        wangwu_stats = author_stats["王五"]
        self.assertEqual(wangwu_stats['checkin_count'], 1)
        self.assertEqual(wangwu_stats['total_score'], 70)
        self.assertEqual(wangwu_stats['avg_score'], 70.0)
        self.assertEqual(wangwu_stats['max_score'], 70)
        self.assertEqual(wangwu_stats['min_score'], 70)
    
    def test_sort_authors_by_checkin_count(self):
        """测试按打卡次数排序作者"""
        analyzer = ScoreAnalyzer(data_dir=self.temp_dir)
        sorted_authors = analyzer.sort_authors_by('checkin_count')
        
        # 应该按打卡次数降序排列：李四(3) > 张三(2) > 王五(1)
        self.assertEqual(len(sorted_authors), 3)
        self.assertEqual(sorted_authors[0][0], "李四")
        self.assertEqual(sorted_authors[0][1]['checkin_count'], 3)
        self.assertEqual(sorted_authors[1][0], "张三")
        self.assertEqual(sorted_authors[1][1]['checkin_count'], 2)
        self.assertEqual(sorted_authors[2][0], "王五")
        self.assertEqual(sorted_authors[2][1]['checkin_count'], 1)
    
    def test_sort_authors_by_avg_score(self):
        """测试按平均分排序作者"""
        analyzer = ScoreAnalyzer(data_dir=self.temp_dir)
        sorted_authors = analyzer.sort_authors_by('avg_score')
        
        # 应该按平均分降序排列：张三(87.5) > 李四(81.0) > 王五(70.0)
        self.assertEqual(len(sorted_authors), 3)
        self.assertEqual(sorted_authors[0][0], "张三")
        self.assertEqual(sorted_authors[0][1]['avg_score'], 87.5)
        self.assertEqual(sorted_authors[1][0], "李四")
        self.assertEqual(sorted_authors[1][1]['avg_score'], 81.0)
        self.assertEqual(sorted_authors[2][0], "王五")
        self.assertEqual(sorted_authors[2][1]['avg_score'], 70.0)
    
    def test_sort_authors_by_total_score(self):
        """测试按总分排序作者"""
        analyzer = ScoreAnalyzer(data_dir=self.temp_dir)
        sorted_authors = analyzer.sort_authors_by('total_score')
        
        # 应该按总分降序排列：李四(243) > 张三(175) > 王五(70)
        self.assertEqual(len(sorted_authors), 3)
        self.assertEqual(sorted_authors[0][0], "李四")
        self.assertEqual(sorted_authors[0][1]['total_score'], 243)
        self.assertEqual(sorted_authors[1][0], "张三")
        self.assertEqual(sorted_authors[1][1]['total_score'], 175)
        self.assertEqual(sorted_authors[2][0], "王五")
        self.assertEqual(sorted_authors[2][1]['total_score'], 70)
    
    def test_sort_authors_invalid_key(self):
        """测试使用无效排序键"""
        analyzer = ScoreAnalyzer(data_dir=self.temp_dir)
        
        # 使用无效的排序键，应该默认按平均分排序
        sorted_authors = analyzer.sort_authors_by('invalid_key')
        
        # 应该按平均分降序排列
        self.assertEqual(sorted_authors[0][0], "张三")
        self.assertEqual(sorted_authors[1][0], "李四")
        self.assertEqual(sorted_authors[2][0], "王五")
    
    def test_get_overall_stats(self):
        """测试获取总体统计信息"""
        analyzer = ScoreAnalyzer(data_dir=self.temp_dir)
        overall_stats = analyzer.get_overall_stats()
        
        # 检查总体统计
        self.assertEqual(overall_stats['total_authors'], 3)
        self.assertEqual(overall_stats['total_notes'], 6)  # 2 + 3 + 1
        self.assertEqual(overall_stats['total_score'], 488)  # 175 + 243 + 70
        self.assertEqual(overall_stats['avg_score'], 81.33)  # 488 / 6，保留2位小数
        self.assertEqual(overall_stats['max_score'], 90)  # 张三的最高分
        self.assertEqual(overall_stats['min_score'], 70)  # 王五的最低分
        self.assertEqual(overall_stats['total_views'], 560)  # 所有笔记的总浏览量
        self.assertEqual(overall_stats['total_likes'], 59)  # 所有笔记的总点赞数
        self.assertEqual(overall_stats['total_replies'], 28)  # 所有笔记的总回复数
    
    def test_get_author_rank(self):
        """测试获取作者排名"""
        analyzer = ScoreAnalyzer(data_dir=self.temp_dir)
        
        # 测试按平均分排名
        zhangsan_rank = analyzer.get_author_rank("张三", 'avg_score')
        self.assertEqual(zhangsan_rank, 1)  # 张三平均分最高，排名第1
        
        lisi_rank = analyzer.get_author_rank("李四", 'avg_score')
        self.assertEqual(lisi_rank, 2)  # 李四平均分第二，排名第2
        
        wangwu_rank = analyzer.get_author_rank("王五", 'avg_score')
        self.assertEqual(wangwu_rank, 3)  # 王五平均分最低，排名第3
        
        # 测试按打卡次数排名
        lisi_checkin_rank = analyzer.get_author_rank("李四", 'checkin_count')
        self.assertEqual(lisi_checkin_rank, 1)  # 李四打卡次数最多，排名第1
        
        # 测试不存在的作者
        nonexistent_rank = analyzer.get_author_rank("不存在的作者", 'avg_score')
        self.assertIsNone(nonexistent_rank)
    
    def test_get_top_authors(self):
        """测试获取排名前N的作者"""
        analyzer = ScoreAnalyzer(data_dir=self.temp_dir)
        
        # 获取前2名（按平均分）
        top_2_authors = analyzer.get_top_authors(2, 'avg_score')
        self.assertEqual(len(top_2_authors), 2)
        self.assertEqual(top_2_authors[0][0], "张三")
        self.assertEqual(top_2_authors[1][0], "李四")
        
        # 获取前1名（按打卡次数）
        top_1_author = analyzer.get_top_authors(1, 'checkin_count')
        self.assertEqual(len(top_1_author), 1)
        self.assertEqual(top_1_author[0][0], "李四")
        
        # 获取前10名（超过实际作者数量）
        all_authors = analyzer.get_top_authors(10, 'avg_score')
        self.assertEqual(len(all_authors), 3)  # 只有3个作者
    
    def test_generate_report(self):
        """测试生成完整分析报告"""
        analyzer = ScoreAnalyzer(data_dir=self.temp_dir)
        report = analyzer.generate_report()
        
        # 检查报告结构
        self.assertIn('overall_stats', report)
        self.assertIn('author_stats', report)
        self.assertIn('top_authors_by_avg_score', report)
        self.assertIn('top_authors_by_checkin_count', report)
        self.assertIn('top_authors_by_total_score', report)
        
        # 检查总体统计
        overall_stats = report['overall_stats']
        self.assertEqual(overall_stats['total_authors'], 3)
        self.assertEqual(overall_stats['total_notes'], 6)
        
        # 检查作者统计
        author_stats = report['author_stats']
        self.assertEqual(len(author_stats), 3)
        self.assertIn("张三", author_stats)
        
        # 检查排行榜
        top_avg_score = report['top_authors_by_avg_score']
        self.assertEqual(len(top_avg_score), 3)
        self.assertEqual(top_avg_score[0][0], "张三")  # 平均分最高
    
    def test_print_analysis_report(self):
        """测试打印分析报告（简单测试，主要检查不抛异常）"""
        analyzer = ScoreAnalyzer(data_dir=self.temp_dir)
        
        # 这个测试主要确保print_analysis_report不会抛出异常
        try:
            analyzer.print_analysis_report()
        except Exception as e:
            self.fail(f"print_analysis_report raised an exception: {e}")
    
    def test_save_analysis_to_csv(self):
        """测试保存分析结果到CSV文件"""
        analyzer = ScoreAnalyzer(data_dir=self.temp_dir)
        csv_file = os.path.join(self.temp_dir, 'test_analysis.csv')
        
        # 保存分析结果
        analyzer.save_analysis_to_csv(csv_file)
        
        # 检查文件是否创建
        self.assertTrue(os.path.exists(csv_file))
        
        # 读取CSV文件并检查内容
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            # 应该有3行数据（3个作者）
            self.assertEqual(len(rows), 3)
            
            # 检查列名
            expected_columns = [
                '作者', '打卡次数', '总分', '平均分', '最高分', '最低分',
                '总内容长度', '平均内容长度', '总浏览量', '总点赞数', '总回复数'
            ]
            self.assertEqual(list(rows[0].keys()), expected_columns)
            
            # 检查第一行数据（应该是按平均分排序的张三）
            first_row = rows[0]
            self.assertEqual(first_row['作者'], '张三')
            self.assertEqual(first_row['打卡次数'], '2')
            self.assertEqual(first_row['平均分'], '87.5')
    
    def test_export_detailed_reports(self):
        """测试导出详细分析报告"""
        analyzer = ScoreAnalyzer(data_dir=self.temp_dir)
        
        # 导出详细报告
        analyzer.export_detailed_reports()
        
        # 检查文件是否创建
        expected_files = [
            'score_analysis_summary.csv',
            'score_analysis_by_avg_score.csv',
            'score_analysis_by_checkin_count.csv',
            'score_analysis_by_total_score.csv'
        ]
        
        for filename in expected_files:
            filepath = os.path.join(self.temp_dir, filename)
            self.assertTrue(os.path.exists(filepath), f"文件 {filename} 未创建")
            
            # 检查文件不为空
            self.assertGreater(os.path.getsize(filepath), 0, f"文件 {filename} 为空")
    
    def test_empty_scores(self):
        """测试空评分数据的处理"""
        empty_dir = tempfile.mkdtemp()
        try:
            analyzer = ScoreAnalyzer(data_dir=empty_dir)
            
            # 测试各种方法在空数据下的表现
            author_stats = analyzer.analyze_authors()
            self.assertEqual(len(author_stats), 0)
            
            sorted_authors = analyzer.sort_authors_by('avg_score')
            self.assertEqual(len(sorted_authors), 0)
            
            overall_stats = analyzer.get_overall_stats()
            self.assertEqual(overall_stats['total_authors'], 0)
            self.assertEqual(overall_stats['total_notes'], 0)
            self.assertEqual(overall_stats['avg_score'], 0)
            
            top_authors = analyzer.get_top_authors(5, 'avg_score')
            self.assertEqual(len(top_authors), 0)
            
            # 测试打印和保存方法不抛异常
            try:
                analyzer.print_analysis_report()
                csv_file = os.path.join(empty_dir, 'empty_test.csv')
                analyzer.save_analysis_to_csv(csv_file)
                analyzer.export_detailed_reports()
            except Exception as e:
                self.fail(f"Empty data handling raised an exception: {e}")
                
        finally:
            import shutil
            shutil.rmtree(empty_dir, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()