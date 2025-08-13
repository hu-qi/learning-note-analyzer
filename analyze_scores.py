import pandas as pd
import os
from typing import Dict, Any
from collections import defaultdict

class ScoreAnalyzer:
    def __init__(self, csv_file: str = "data/note_scores_report.csv"):
        """初始化分析器，加载评分数据"""
        # 确保 data 目录存在
        self.data_dir = 'data'
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.csv_file = csv_file
        self.scores_data = self.load_scores_data()
        
    def load_scores_data(self) -> pd.DataFrame:
        """加载评分数据"""
        try:
            df = pd.read_csv(self.csv_file, encoding='utf-8')
            print(f"成功加载 {len(df)} 条评分记录")
            return df
        except FileNotFoundError:
            print(f"文件 {self.csv_file} 不存在")
            return pd.DataFrame()
        except Exception as e:
            print(f"加载文件时出错: {e}")
            return pd.DataFrame()
    
    def analyze_author_stats(self) -> Dict[str, Dict[str, Any]]:
        """分析每个作者的统计数据"""
        if self.scores_data.empty:
            return {}
            
        author_stats = defaultdict(lambda: {
            'checkin_count': 0,
            'total_score': 0,
            'avg_score': 0.0,
            'scores': [],
            'tasks': [],
            'max_score': 0,
            'min_score': 100,
            'content_length_total': 0,
            'avg_content_length': 0.0
        })
        
        # 统计每个作者的数据
        for _, row in self.scores_data.iterrows():
            author = row['author']
            score = row['score']
            task = row['task']
            content_length = row['content_length']
            
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
        
        # 计算平均分和平均内容长度
        for author, stats in author_stats.items():
            if stats['checkin_count'] > 0:
                stats['avg_score'] = stats['total_score'] / stats['checkin_count']
                stats['avg_content_length'] = stats['content_length_total'] / stats['checkin_count']
                # 去重任务列表
                stats['unique_tasks'] = list(set(stats['tasks']))
                stats['unique_task_count'] = len(stats['unique_tasks'])
        
        return dict(author_stats)
    
    def sort_authors(self, author_stats: Dict[str, Dict[str, Any]]) -> list:
        """按打卡次数从高到低、平均分从高到低排序"""
        # 转换为列表并排序
        # 首先按打卡次数降序，然后按平均分降序
        sorted_authors = sorted(
            author_stats.items(),
            key=lambda x: (x[1]['checkin_count'], x[1]['avg_score']),
            reverse=True
        )
        return sorted_authors
    
    def print_analysis_report(self):
        """打印分析报告"""
        print("=" * 80)
        print("学习笔记评分分析报告")
        print("=" * 80)
        
        if self.scores_data.empty:
            print("没有数据可分析")
            return
        
        # 获取统计数据
        author_stats = self.analyze_author_stats()
        sorted_authors = self.sort_authors(author_stats)
        
        print(f"\n总体统计:")
        print(f"  总记录数: {len(self.scores_data)}")
        print(f"  参与作者数: {len(author_stats)}")
        print(f"  平均分: {self.scores_data['score'].mean():.2f}")
        print(f"  最高分: {self.scores_data['score'].max()}")
        print(f"  最低分: {self.scores_data['score'].min()}")
        
        print(f"\n按打卡次数和平均分排序的作者统计:")
        print("-" * 80)
        print(f"{'排名':<4} {'作者':<20} {'打卡次数':<8} {'平均分':<8} {'总分':<8} {'最高分':<8} {'最低分':<8} {'完成任务数':<10}")
        print("-" * 80)
        
        for rank, (author, stats) in enumerate(sorted_authors, 1):
            print(f"{rank:<4} {author:<20} {stats['checkin_count']:<8} {stats['avg_score']:<8.2f} {stats['total_score']:<8} {stats['max_score']:<8} {stats['min_score']:<8} {stats['unique_task_count']:<10}")
        
        # 显示详细信息（前10名）
        print(f"\n详细信息（前10名）:")
        print("=" * 80)
        
        for rank, (author, stats) in enumerate(sorted_authors[:10], 1):
            print(f"\n{rank}. {author}:")
            print(f"   打卡次数: {stats['checkin_count']}")
            print(f"   平均分: {stats['avg_score']:.2f}")
            print(f"   总分: {stats['total_score']}")
            print(f"   分数范围: {stats['min_score']} - {stats['max_score']}")
            print(f"   完成任务数: {stats['unique_task_count']}")
            print(f"   平均内容长度: {stats['avg_content_length']:.0f} 字符")
            print(f"   完成的任务: {', '.join(sorted(stats['unique_tasks'], key=lambda x: int(x[3:])))}")
    
    def save_analysis_to_csv(self):
        """保存分析结果到CSV文件"""
        if self.scores_data.empty:
            print("没有数据可保存")
            return
        
        # 获取统计数据
        author_stats = self.analyze_author_stats()
        sorted_authors = self.sort_authors(author_stats)
        
        # 创建结果DataFrame
        results = []
        for rank, (author, stats) in enumerate(sorted_authors, 1):
            results.append({
                '排名': rank,
                '作者': author,
                '打卡次数': stats['checkin_count'],
                '平均分': round(stats['avg_score'], 2),
                '总分': stats['total_score'],
                '最高分': stats['max_score'],
                '最低分': stats['min_score'],
                '完成任务数': stats['unique_task_count'],
                '平均内容长度': round(stats['avg_content_length'], 0),
                '完成的任务': ', '.join(sorted(stats['unique_tasks'], key=lambda x: int(x[3:])))
            })
        
        result_df = pd.DataFrame(results)
        output_file = os.path.join(self.data_dir, 'author_analysis_report.csv')
        result_df.to_csv(output_file, index=False, encoding='utf-8')
        
        print(f"\n分析结果已保存到: {output_file}")
    
    def generate_report(self):
        """生成完整的分析报告"""
        self.print_analysis_report()
        self.save_analysis_to_csv()

if __name__ == "__main__":
    # 创建分析器实例
    analyzer = ScoreAnalyzer()
    
    # 生成分析报告
    analyzer.generate_report()