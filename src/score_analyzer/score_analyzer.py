#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
评分分析器模块

提供学习笔记评分数据的分析功能，包括：
- 作者统计分析
- 排序和排名
- 分析报告生成
- 数据导出
"""

import os
import pandas as pd
from typing import Dict, Any, List, Tuple
from collections import defaultdict

from ..utils.logger import get_logger
from ..utils.file_utils import ensure_dir, save_csv


class ScoreAnalyzer:
    """评分分析器"""
    
    def __init__(self, csv_file: str = "data/note_scores_report.csv", data_dir: str = "data"):
        """
        初始化评分分析器
        
        Args:
            csv_file: 评分数据CSV文件路径
            data_dir: 数据目录路径
        """
        self.logger = get_logger('score_analyzer')
        self.data_dir = data_dir
        self.csv_file = csv_file
        
        # 确保数据目录存在
        ensure_dir(self.data_dir)
        
        # 加载评分数据
        self.scores_data = self._load_scores_data()
        
        self.logger.info(f"评分分析器初始化完成，加载了 {len(self.scores_data)} 条评分记录")
    
    def _load_scores_data(self) -> pd.DataFrame:
        """加载评分数据"""
        try:
            if not os.path.exists(self.csv_file):
                self.logger.warning(f"评分数据文件不存在: {self.csv_file}")
                return pd.DataFrame()
            
            df = pd.read_csv(self.csv_file, encoding='utf-8')
            self.logger.info(f"成功加载 {len(df)} 条评分记录")
            return df
            
        except Exception as e:
            self.logger.error(f"加载评分数据失败: {e}")
            return pd.DataFrame()
    
    def analyze_author_stats(self) -> Dict[str, Dict[str, Any]]:
        """分析每个作者的统计数据"""
        if self.scores_data.empty:
            self.logger.warning("没有评分数据可分析")
            return {}
        
        # 总任务数（根据config.yaml中的DAY1-DAY12）
        total_tasks = 12
        
        author_stats = defaultdict(lambda: {
            'checkin_count': 0,
            'total_score': 0,
            'avg_score': 0.0,
            'scores': [],
            'tasks': [],
            'max_score': 0,
            'min_score': 100,
            'content_length_total': 0,
            'avg_content_length': 0.0,
            'unique_tasks': [],
            'unique_task_count': 0,
            'completion_rate': 0.0
        })
        
        # 统计每个作者的数据
        for _, row in self.scores_data.iterrows():
            author = row['author']
            score = row['score']
            task = row['task']
            content_length = row.get('content_length', 0)
            
            author_stats[author]['checkin_count'] += 1
            author_stats[author]['total_score'] += score
            author_stats[author]['scores'].append(score)
            author_stats[author]['tasks'].append(task)
            author_stats[author]['content_length_total'] += content_length
            
            # 更新最高分和最低分
            if score > author_stats[author]['max_score']:
                author_stats[author]['max_score'] = score
            if score < author_stats[author]['min_score']:
                author_stats[author]['min_score'] = score
        
        # 计算平均分、平均内容长度和完成率
        for author, stats in author_stats.items():
            if stats['checkin_count'] > 0:
                stats['avg_score'] = stats['total_score'] / stats['checkin_count']
                stats['avg_content_length'] = stats['content_length_total'] / stats['checkin_count']
                # 去重任务列表并按DAY顺序排序
                unique_tasks = list(set(stats['tasks']))
                unique_tasks.sort(key=lambda x: int(x[3:]) if x.startswith('DAY') and x[3:].isdigit() else 999)
                stats['unique_tasks'] = unique_tasks
                stats['unique_task_count'] = len(unique_tasks)
                # 计算完成率（完成的任务数 / 总任务数）
                stats['completion_rate'] = stats['unique_task_count'] / total_tasks
        
        self.logger.info(f"分析了 {len(author_stats)} 个作者的统计数据")
        return dict(author_stats)
    
    def sort_authors(self, author_stats: Dict[str, Dict[str, Any]], 
                    sort_by: str = 'completion_and_score') -> List[Tuple[str, Dict[str, Any]]]:
        """
        按指定方式排序作者
        
        Args:
            author_stats: 作者统计数据
            sort_by: 排序方式，可选值：
                - 'completion_and_score': 按完成率和平均分排序（默认）
                - 'completion_rate': 按完成率排序
                - 'checkin_and_score': 按打卡次数和平均分排序
                - 'avg_score': 按平均分排序
                - 'total_score': 按总分排序
                - 'checkin_count': 按打卡次数排序
        
        Returns:
            排序后的作者列表
        """
        if sort_by == 'completion_rate':
            key_func = lambda x: x[1]['completion_rate']
        elif sort_by == 'avg_score':
            key_func = lambda x: x[1]['avg_score']
        elif sort_by == 'total_score':
            key_func = lambda x: x[1]['total_score']
        elif sort_by == 'checkin_count':
            key_func = lambda x: x[1]['checkin_count']
        elif sort_by == 'checkin_and_score':
            key_func = lambda x: (x[1]['checkin_count'], x[1]['avg_score'])
        else:  # 默认按完成率和平均分排序
            key_func = lambda x: (x[1]['completion_rate'], x[1]['avg_score'])
        
        sorted_authors = sorted(author_stats.items(), key=key_func, reverse=True)
        self.logger.debug(f"按 {sort_by} 排序了 {len(sorted_authors)} 个作者")
        return sorted_authors
    
    def get_overall_stats(self) -> Dict[str, Any]:
        """获取总体统计信息"""
        if self.scores_data.empty:
            return {}
        
        author_stats = self.analyze_author_stats()
        
        overall_stats = {
            'total_records': len(self.scores_data),
            'total_authors': len(author_stats),
            'avg_score': float(self.scores_data['score'].mean()),
            'max_score': int(self.scores_data['score'].max()),
            'min_score': int(self.scores_data['score'].min()),
            'score_std': float(self.scores_data['score'].std()),
            'total_tasks': len(self.scores_data['task'].unique()) if 'task' in self.scores_data.columns else 0
        }
        
        return overall_stats
    
    def generate_analysis_report(self) -> Dict[str, Any]:
        """生成完整的分析报告"""
        self.logger.info("开始生成评分分析报告")
        
        if self.scores_data.empty:
            self.logger.warning("没有数据可分析")
            return {'error': '没有数据可分析'}
        
        # 获取统计数据
        author_stats = self.analyze_author_stats()
        sorted_authors = self.sort_authors(author_stats)
        overall_stats = self.get_overall_stats()
        
        # 构建报告
        report = {
            'overall_stats': overall_stats,
            'author_stats': author_stats,
            'sorted_authors': sorted_authors,
            'top_performers': sorted_authors[:10] if sorted_authors else []
        }
        
        self.logger.info("评分分析报告生成完成")
        return report
    
    def print_analysis_report(self, report: Dict[str, Any] = None):
        """打印分析报告到控制台"""
        if report is None:
            report = self.generate_analysis_report()
        
        if 'error' in report:
            print(report['error'])
            return
        
        print("=" * 80)
        print("学习笔记评分分析报告")
        print("=" * 80)
        
        # 总体统计
        overall_stats = report['overall_stats']
        print(f"\n总体统计:")
        print(f"  总记录数: {overall_stats['total_records']}")
        print(f"  参与作者数: {overall_stats['total_authors']}")
        print(f"  总任务数: {overall_stats['total_tasks']}")
        print(f"  平均分: {overall_stats['avg_score']:.2f}")
        print(f"  最高分: {overall_stats['max_score']}")
        print(f"  最低分: {overall_stats['min_score']}")
        print(f"  分数标准差: {overall_stats['score_std']:.2f}")
        
        # 作者排名
        sorted_authors = report['sorted_authors']
        print(f"\n按完成率和平均分排序的作者统计:")
        print("-" * 100)
        print(f"{'排名':<4} {'作者':<20} {'完成率':<8} {'打卡次数':<8} {'平均分':<8} {'总分':<8} {'最高分':<8} {'最低分':<8} {'完成任务数':<10}")
        print("-" * 100)
        
        for rank, (author, stats) in enumerate(sorted_authors, 1):
            completion_rate_str = f"{stats['completion_rate']*100:.1f}%"
            print(f"{rank:<4} {author:<20} {completion_rate_str:<8} {stats['checkin_count']:<8} {stats['avg_score']:<8.2f} {stats['total_score']:<8} {stats['max_score']:<8} {stats['min_score']:<8} {stats['unique_task_count']:<10}")
        
        # 详细信息（前10名）
        print(f"\n详细信息（前10名）:")
        print("=" * 80)
        
        for rank, (author, stats) in enumerate(sorted_authors[:10], 1):
            print(f"\n{rank}. {author}:")
            print(f"   完成率: {stats['completion_rate']*100:.1f}% ({stats['unique_task_count']}/12)")
            print(f"   打卡次数: {stats['checkin_count']}")
            print(f"   平均分: {stats['avg_score']:.2f}")
            print(f"   总分: {stats['total_score']}")
            print(f"   分数范围: {stats['min_score']} - {stats['max_score']}")
            print(f"   平均内容长度: {stats['avg_content_length']:.0f} 字符")
            print(f"   完成的任务: {', '.join(stats['unique_tasks'])}")
    
    def save_analysis_to_csv(self, report: Dict[str, Any] = None, output_file: str = None):
        """保存分析结果到CSV文件"""
        if report is None:
            report = self.generate_analysis_report()
        
        if 'error' in report:
            self.logger.error(f"无法保存分析结果: {report['error']}")
            return
        
        if output_file is None:
            output_file = os.path.join(self.data_dir, 'author_analysis_report.csv')
        
        try:
            # 创建结果DataFrame
            sorted_authors = report['sorted_authors']
            results = []
            
            for rank, (author, stats) in enumerate(sorted_authors, 1):
                results.append({
                    '排名': rank,
                    '作者': author,
                    '完成率': f"{stats['completion_rate']*100:.1f}%",
                    '打卡次数': stats['checkin_count'],
                    '平均分': round(stats['avg_score'], 2),
                    '总分': stats['total_score'],
                    '最高分': stats['max_score'],
                    '最低分': stats['min_score'],
                    '完成任务数': stats['unique_task_count'],
                    '平均内容长度': round(stats['avg_content_length'], 0),
                    '完成的任务': ', '.join(stats['unique_tasks'])
                })
            
            result_df = pd.DataFrame(results)
            save_csv(result_df, output_file)
            
            self.logger.info(f"分析结果已保存到: {output_file}")
            
        except Exception as e:
            self.logger.error(f"保存分析结果失败: {e}")
    
    def get_author_ranking(self, author_name: str) -> Dict[str, Any]:
        """获取指定作者的排名信息"""
        report = self.generate_analysis_report()
        
        if 'error' in report:
            return {'error': report['error']}
        
        sorted_authors = report['sorted_authors']
        
        for rank, (author, stats) in enumerate(sorted_authors, 1):
            if author == author_name:
                return {
                    'rank': rank,
                    'author': author,
                    'stats': stats,
                    'total_authors': len(sorted_authors)
                }
        
        return {'error': f'未找到作者: {author_name}'}
    
    def get_top_performers(self, top_n: int = 10, sort_by: str = 'completion_and_score') -> List[Tuple[str, Dict[str, Any]]]:
        """获取排名前N的作者"""
        author_stats = self.analyze_author_stats()
        if not author_stats:
            return []
        
        sorted_authors = self.sort_authors(author_stats, sort_by)
        return sorted_authors[:top_n]
    
    def export_detailed_report(self, output_dir: str = None) -> Dict[str, str]:
        """导出详细的分析报告到多个文件"""
        if output_dir is None:
            output_dir = self.data_dir
        
        ensure_dir(output_dir)
        
        report = self.generate_analysis_report()
        if 'error' in report:
            return {'error': report['error']}
        
        output_files = {}
        
        try:
            # 1. 保存作者分析报告
            author_file = os.path.join(output_dir, 'author_analysis_report.csv')
            self.save_analysis_to_csv(report, author_file)
            output_files['author_analysis'] = author_file
            
            # 2. 保存总体统计
            overall_stats = report['overall_stats']
            overall_df = pd.DataFrame([overall_stats])
            overall_file = os.path.join(output_dir, 'overall_stats.csv')
            save_csv(overall_df, overall_file)
            output_files['overall_stats'] = overall_file
            
            # 3. 保存前10名详细信息
            top_performers = report['top_performers']
            top_details = []
            for rank, (author, stats) in enumerate(top_performers, 1):
                top_details.append({
                    '排名': rank,
                    '作者': author,
                    '完成率': f"{stats['completion_rate']*100:.1f}%",
                    '打卡次数': stats['checkin_count'],
                    '平均分': round(stats['avg_score'], 2),
                    '总分': stats['total_score'],
                    '最高分': stats['max_score'],
                    '最低分': stats['min_score'],
                    '完成任务数': stats['unique_task_count'],
                    '平均内容长度': round(stats['avg_content_length'], 0),
                    '所有分数': ', '.join(map(str, stats['scores'])),
                    '完成的任务': ', '.join(stats['unique_tasks'])
                })
            
            if top_details:
                top_df = pd.DataFrame(top_details)
                top_file = os.path.join(output_dir, 'top_performers_detailed.csv')
                save_csv(top_df, top_file)
                output_files['top_performers'] = top_file
            
            self.logger.info(f"详细报告已导出到 {output_dir} 目录")
            return output_files
            
        except Exception as e:
            self.logger.error(f"导出详细报告失败: {e}")
            return {'error': str(e)}