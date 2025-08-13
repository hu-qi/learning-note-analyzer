#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学习笔记分析器模块

提供学习笔记的分析功能，包括：
- 任务打卡情况分析
- 用户打卡情况分析
- 大模型评分功能
- 分析报告生成
"""

import os
import json
import re
import time
import pandas as pd
from typing import Dict, List, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

from ..utils.logger import get_logger
from ..utils.file_utils import ensure_dir, load_json, save_csv


class LearningNoteAnalyzer:
    """学习笔记分析器"""
    
    def __init__(self, data_dir: str = "data", config: Optional[Dict] = None):
        """
        初始化学习笔记分析器
        
        Args:
            data_dir: 数据目录路径
            config: 配置字典
        """
        self.logger = get_logger('analyzer')
        self.data_dir = data_dir
        self.config = config or {}
        
        # 确保数据目录存在
        ensure_dir(self.data_dir)
        
        # 加载环境变量
        load_dotenv()
        
        # 加载文章数据
        self.articles = self._load_articles()
        
        # 筛选学习笔记
        self.learning_notes = self._filter_learning_notes()
        
        # 初始化大模型客户端
        self._init_llm_client()
        
        self.logger.info(f"分析器初始化完成，共加载 {len(self.articles)} 篇文章，其中 {len(self.learning_notes)} 篇学习笔记")
    
    def _load_articles(self) -> List[Dict]:
        """加载文章数据"""
        articles_file = os.path.join(self.data_dir, 'articles_all.json')
        
        if not os.path.exists(articles_file):
            self.logger.warning(f"文章数据文件不存在: {articles_file}")
            return []
        
        try:
            articles = load_json(articles_file)
            self.logger.info(f"成功加载 {len(articles)} 篇文章")
            return articles
        except Exception as e:
            self.logger.error(f"加载文章数据失败: {e}")
            return []
    
    def _generate_task_name_mapping(self) -> Dict[str, str]:
        """根据配置生成任务名称映射"""
        filter_keywords = self.config.get('analysis', {}).get('filter_keywords', [])
        task_mapping = {}
        
        # 根据filter_keywords的长度生成DAY1-DAY12的映射
        for i, keyword in enumerate(filter_keywords[:12], 1):
            task_mapping[keyword] = f"DAY{i}"
        
        self.logger.info(f"生成任务名称映射: {task_mapping}")
        return task_mapping
    
    def _get_task_name_from_title(self, title: str, task_name: str) -> str:
        """从标题或任务名中提取标准化的任务名称"""
        filter_keywords = self.config.get('analysis', {}).get('filter_keywords', [])
        task_mapping = self._generate_task_name_mapping()
        
        # 检查标题或任务名是否包含任何关键词
        for keyword in filter_keywords:
            if keyword in title or keyword in task_name:
                return task_mapping.get(keyword, 'Unknown')
        
        return 'Unknown'
    
    def _filter_learning_notes(self) -> List[Dict]:
        """筛选学习笔记（从配置文件读取筛选模式）"""
        learning_notes = []
        
        # 从配置文件读取筛选关键词，如果不存在则使用默认的精确模式
        filter_keywords = self.config.get('analysis', {}).get('filter_keywords', [])
        
        if filter_keywords:
            # 使用配置文件中的关键词进行简单匹配
            title_patterns = filter_keywords
            self.logger.info(f"使用配置文件中的筛选关键词: {filter_keywords}")
        else:
            # 使用默认的精确标题模式作为后备
            title_patterns = [
                r'【0726-DAY1学习笔记】',
                r'【0727-DAY2学习笔记】', 
                r'【0728-DAY3学习笔记】',
                r'【0729-DAY4学习笔记】',
                r'【5天学习分享】',
                r'【0731-DAY6学习笔记】',
                r'【0801-DAY7学习笔记】',
                r'【8天学习分享】',
                r'【0803-DAY9学习笔记】',
                r'【0804-DAY10学习笔记】',
                r'【0805-DAY11学习笔记】',
                r'【十天成长计划】',
            ]
            self.logger.info("使用默认的精确标题模式进行筛选")
        
        # 根据模式类型进行不同的匹配处理
        if filter_keywords:
            # 配置文件中的关键词进行简单包含匹配
            for article in self.articles:
                title = article.get('title', '')
                task_name = article.get('task_name', '')
                
                # 检查标题或任务名是否包含任何关键词
                is_learning_note = False
                for keyword in filter_keywords:
                    if keyword in title or keyword in task_name:
                        is_learning_note = True
                        break
                
                if is_learning_note:
                    # 添加标准化的任务名称
                    article_copy = article.copy()
                    article_copy['standardized_task_name'] = self._get_task_name_from_title(title, task_name)
                    learning_notes.append(article_copy)
        else:
            # 默认精确模式使用正则表达式匹配
            compiled_patterns = [re.compile(pattern) for pattern in title_patterns]
            
            for article in self.articles:
                title = article.get('title', '')
                task_name = article.get('task_name', '')
                
                # 检查标题或任务名是否匹配任何一个正则表达式模式
                is_learning_note = False
                for pattern in compiled_patterns:
                    if pattern.search(title) or pattern.search(task_name):
                        is_learning_note = True
                        break
                
                if is_learning_note:
                    # 添加标准化的任务名称
                    article_copy = article.copy()
                    article_copy['standardized_task_name'] = self._get_task_name_from_title(title, task_name)
                    learning_notes.append(article_copy)
        
        self.logger.info(f"筛选出 {len(learning_notes)} 篇学习笔记")
        return learning_notes
    
    def _init_llm_client(self):
        """初始化大模型客户端"""
        try:
            # 从环境变量或配置中获取API配置
            api_key = os.getenv('OPENAI_API_KEY') or self.config.get('openai_api_key')
            base_url = os.getenv('OPENAI_BASE_URL') or self.config.get('openai_base_url')
            
            if not api_key:
                self.logger.warning("未找到OpenAI API密钥，评分功能将不可用")
                self.client = None
                return
            
            self.client = OpenAI(
                api_key=api_key,
                base_url=base_url
            )
            self.logger.info("大模型客户端初始化成功")
            
        except Exception as e:
            self.logger.error(f"初始化大模型客户端失败: {e}")
            self.client = None
    
    def analyze_task_checkin(self) -> Dict[str, Dict[str, Any]]:
        """分析每个任务的打卡情况"""
        task_stats = {}
        
        for note in self.learning_notes:
            # 使用标准化的任务名称
            task_name = note.get('standardized_task_name', 'Unknown')
            author_name = note.get('author_name', 'Unknown')
            
            if task_name not in task_stats:
                task_stats[task_name] = {
                    'total_checkins': 0,
                    'unique_participants': set(),
                    'participants_list': [],  # 新增：打卡人列表
                    'total_content_length': 0,
                    'total_views': 0,
                    'total_likes': 0,
                    'total_replies': 0
                }
            
            stats = task_stats[task_name]
            stats['total_checkins'] += 1
            stats['unique_participants'].add(author_name)
            
            # 添加到打卡人列表（避免重复，排除None值）
            if author_name and author_name != 'Unknown' and author_name not in stats['participants_list']:
                stats['participants_list'].append(author_name)
            
            stats['total_content_length'] += len(note.get('content_summary', ''))
            stats['total_views'] += note.get('views', 0)  # 修正字段名
            stats['total_likes'] += note.get('likes', 0)   # 修正字段名
            stats['total_replies'] += note.get('replies', 0) # 修正字段名
        
        # 计算平均值并转换set为数量
        for task_name, stats in task_stats.items():
            stats['unique_participants'] = len(stats['unique_participants'])
            if stats['total_checkins'] > 0:
                stats['avg_content_length'] = stats['total_content_length'] / stats['total_checkins']
            else:
                stats['avg_content_length'] = 0
            
            # 将打卡人列表转换为字符串格式，便于CSV保存（过滤None值）
            valid_participants = [p for p in stats['participants_list'] if p and p != 'Unknown']
            stats['participants_list_str'] = ', '.join(valid_participants)
        
        self.logger.info(f"分析了 {len(task_stats)} 个任务的打卡情况")
        return task_stats
    
    def analyze_user_checkin(self) -> Dict[str, Dict[str, Any]]:
        """分析每个用户的打卡情况"""
        user_stats = {}
        
        # 获取所有任务名称（使用标准化的任务名称）
        all_tasks = set(note.get('standardized_task_name', 'Unknown') for note in self.learning_notes)
        total_tasks = len(all_tasks)
        
        for note in self.learning_notes:
            author_name = note.get('author_name', 'Unknown')
            task_name = note.get('standardized_task_name', 'Unknown')  # 使用标准化的任务名称
            
            if author_name not in user_stats:
                user_stats[author_name] = {
                    'total_checkins': 0,
                    'completed_tasks': set(),
                    'total_content_length': 0,
                    'total_views': 0,
                    'total_likes': 0,
                    'total_replies': 0
                }
            
            stats = user_stats[author_name]
            stats['total_checkins'] += 1
            stats['completed_tasks'].add(task_name)
            stats['total_content_length'] += len(note.get('content_summary', ''))
            stats['total_views'] += note.get('views', 0)  # 修正字段名
            stats['total_likes'] += note.get('likes', 0)   # 修正字段名
            stats['total_replies'] += note.get('replies', 0) # 修正字段名
        
        # 计算衍生指标
        for author_name, stats in user_stats.items():
            stats['unique_tasks'] = len(stats['completed_tasks'])
            stats['completion_rate'] = (stats['unique_tasks'] / total_tasks) * 100 if total_tasks > 0 else 0
            
            if stats['total_checkins'] > 0:
                stats['avg_content_length'] = stats['total_content_length'] / stats['total_checkins']
            else:
                stats['avg_content_length'] = 0
            
            # 按DAY顺序排序完成的任务
            completed_tasks_list = list(stats['completed_tasks'])
            completed_tasks_list.sort(key=lambda x: int(x[3:]) if x.startswith('DAY') and x[3:].isdigit() else 999)
            stats['completed_tasks_sorted'] = completed_tasks_list
            
            # 转换set为list以便序列化
            stats['completed_tasks'] = completed_tasks_list
        
        self.logger.info(f"分析了 {len(user_stats)} 个用户的打卡情况")
        return user_stats
    
    def call_llm_for_scoring(self, content: str, title: str) -> tuple[int, str]:
        """调用大模型服务对学习笔记进行评分"""
        if not self.client:
            self.logger.warning("大模型客户端未初始化，返回默认分数")
            return 60, "大模型服务不可用，给予默认分数"
        
        try:
            # 构建评分提示
            prompt = f"""
请对以下学习笔记进行评分（0-100分），并给出简短评语。

标题：{title}
内容：{content[:1000]}  # 限制内容长度

评分标准：
1. 内容质量和深度（40分）
2. 学习收获和思考（30分）
3. 表达清晰度（20分）
4. 实用性和可操作性（10分）

请以JSON格式返回结果：
{{
    "score": 分数（整数），
    "comment": "评语内容"
}}
"""
            
            # 调用大模型API
            response = self.client.chat.completions.create(
                model="deepseek-v3",
                messages=[
                    {"role": "system", "content": "你是一个专业的学习笔记评分专家，请客观公正地评分。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3 # 
            )
            
            result_text = response.choices[0].message.content.strip()
            self.logger.debug(f"大模型返回结果: {result_text}")
            
            # 解析返回结果
            return self._parse_llm_result(result_text)
            
        except Exception as e:
            self.logger.error(f"调用大模型服务出错: {e}")
            return 60, f"评分服务暂时不可用，给予默认分数。错误信息: {str(e)}"
    
    def _parse_llm_result(self, result_text: str) -> tuple[int, str]:
        """解析大模型返回结果"""
        try:
            # 尝试直接解析JSON
            result = json.loads(result_text)
            score = int(result.get("score", 0))
            comment = result.get("comment", "无评语")
            score = max(0, min(100, score))  # 确保分数在0-100范围内
            return score, comment
            
        except json.JSONDecodeError:
            # 尝试清理文本后再解析
            cleaned_text = result_text.strip()
            if cleaned_text.startswith('```json'):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.endswith('```'):
                cleaned_text = cleaned_text[:-3]
            cleaned_text = cleaned_text.strip()
            
            try:
                result = json.loads(cleaned_text)
                score = int(result.get("score", 0))
                comment = result.get("comment", "无评语")
                score = max(0, min(100, score))
                return score, comment
            except json.JSONDecodeError:
                pass
            
            # 尝试从文本中提取JSON
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', result_text, re.DOTALL)
            if json_match:
                try:
                    json_str = json_match.group(0)
                    result = json.loads(json_str)
                    score = int(result.get("score", 0))
                    comment = result.get("comment", "无评语")
                    score = max(0, min(100, score))
                    return score, comment
                except json.JSONDecodeError:
                    pass
            
            # 使用正则表达式提取分数和评语
            self.logger.warning(f"无法解析JSON结果，尝试提取分数和评语: {result_text[:200]}...")
            
            # 提取分数
            score_match = re.search(r'["\']?score["\']?\s*[:\=]\s*(\d+)', result_text, re.IGNORECASE)
            if score_match:
                score = int(score_match.group(1))
                score = max(0, min(100, score))
            else:
                score = 60  # 默认分数
            
            # 提取评语 - 修复正则表达式
            comment_match = re.search(r'["\']?comment["\']?\s*[:\=]\s*["\']([^"\']+)["\']', result_text, re.IGNORECASE)
            if comment_match:
                comment = comment_match.group(1)
            else:
                # 尝试提取评语部分
                comment_lines = []
                for line in result_text.split('\n'):
                    if 'comment' in line.lower() or '评语' in line:
                        continue
                    if line.strip():
                        comment_lines.append(line.strip())
                
                if comment_lines:
                    comment = ' '.join(comment_lines)[:500]  # 限制评语长度
                else:
                    comment = "无法提取评语"
            
            return score, comment
    
    def score_notes(self) -> Dict[str, Dict[str, Any]]:
        """使用大模型服务给每个学习笔记打分"""
        note_scores = {}
        
        self.logger.info("开始使用大模型服务对学习笔记进行评分...")
        
        for i, note in enumerate(self.learning_notes):
            author_name = note.get('author_name', 'Unknown')
            task_name = note.get('standardized_task_name', 'Unknown')  # 使用标准化的任务名称
            content = note.get('content_summary', '')
            title = note.get('title', 'Unknown')
            note_id = note.get('id', '')
            
            # 构建笔记链接
            note_link = f"https://bbs.huaweicloud.com/forum/thread-{note_id}-1-1.html" if note_id else ''
            
            self.logger.info(f"正在评分第 {i+1}/{len(self.learning_notes)} 篇笔记: {title}")
            
            # 调用大模型服务进行评分
            score, comment = self.call_llm_for_scoring(content, title)
            self.logger.debug(f"评分结果: {score}, {comment}")
            
            if author_name not in note_scores:
                note_scores[author_name] = {
                    'notes': [],
                    'total_score': 0,
                    'avg_score': 0,
                    'best_note': None,
                    'worst_note': None
                }
            
            note_info = {
                'task_name': task_name,
                'score': score,
                'comment': comment,
                'content_length': len(content),
                'title': title,
                'note_link': note_link  # 新增：笔记链接
            }
            
            note_scores[author_name]['notes'].append(note_info)
            note_scores[author_name]['total_score'] += score
            
            # 添加延迟，避免API调用过于频繁
            time.sleep(1)
        
        # 计算平均分和最好/最差的笔记
        for author_name, scores in note_scores.items():
            if scores['notes']:  # 确保有笔记数据
                scores['avg_score'] = scores['total_score'] / len(scores['notes'])
                scores['notes'].sort(key=lambda x: x['score'], reverse=True)
                scores['best_note'] = scores['notes'][0]
                scores['worst_note'] = scores['notes'][-1]
        
        self.logger.info(f"完成 {len(note_scores)} 个用户的笔记评分")
        return note_scores
    
    def generate_report(self) -> Dict[str, Any]:
        """生成完整的分析报告"""
        self.logger.info("开始生成学习笔记分析报告")
        
        # 1. 任务打卡情况分析
        task_stats = self.analyze_task_checkin()
        
        # 2. 用户打卡情况分析
        user_stats = self.analyze_user_checkin()
        
        # 3. 学习笔记评分
        note_scores = self.score_notes()
        
        # 4. 保存详细报告到文件
        self.save_detailed_report(task_stats, user_stats, note_scores)
        
        # 返回报告数据
        report = {
            'task_stats': task_stats,
            'user_stats': user_stats,
            'note_scores': note_scores,
            'summary': {
                'total_articles': len(self.articles),
                'total_learning_notes': len(self.learning_notes),
                'total_tasks': len(task_stats),
                'total_users': len(user_stats)
            }
        }
        
        self.logger.info("学习笔记分析报告生成完成")
        return report
    
    def save_detailed_report(self, task_stats: Dict, user_stats: Dict, note_scores: Dict):
        """保存详细报告到文件"""
        try:
            # 保存任务打卡报告
            task_df = pd.DataFrame.from_dict(task_stats, orient='index')
            task_report_path = os.path.join(self.data_dir, 'task_checkin_report.csv')
            # 将 DataFrame 转换为字典列表格式
            save_csv(task_report_path, task_df.to_dict('records'))
            
            # 保存用户打卡报告
            user_df = pd.DataFrame.from_dict(user_stats, orient='index')
            user_report_path = os.path.join(self.data_dir, 'user_checkin_report.csv')
            # 将 DataFrame 转换为字典列表格式
            save_csv(user_report_path, user_df.to_dict('records'))
            
            # 保存评分详情
            score_details = []
            for author_name, scores in note_scores.items():
                for note in scores['notes']:
                    score_details.append({
                        'author': author_name,
                        'task': note['task_name'],
                        'score': note['score'],
                        'comment': note['comment'],
                        'content_length': note['content_length'],
                        'title': note['title'],
                        'note_link': note['note_link']  # 新增：笔记链接
                    })
            
            if score_details:
                score_report_path = os.path.join(self.data_dir, 'note_scores_report.csv')
                # score_details 已经是字典列表格式，直接传递
                save_csv(score_report_path, score_details)
            
            self.logger.info(f"详细报告已保存到 {self.data_dir} 目录")
            
        except Exception as e:
            self.logger.error(f"保存详细报告失败: {e}")
    
    def print_report(self, report: Dict[str, Any]):
        """打印分析报告到控制台"""
        print("=" * 60)
        print("学习笔记分析报告")
        print("=" * 60)
        
        # 1. 任务打卡情况分析
        print("\n1. 每个任务的打卡情况")
        print("-" * 40)
        task_stats = report['task_stats']
        
        # 按DAY顺序排序
        sorted_tasks = sorted(task_stats.keys(), key=lambda x: int(x[3:]) if x.startswith('DAY') and x[3:].isdigit() else 999)
        
        for task_name in sorted_tasks:
            stats = task_stats[task_name]
            print(f"\n{task_name}:")
            print(f"  总打卡数: {stats['total_checkins']}")
            print(f"  参与人数: {stats['unique_participants']}")
            print(f"  平均内容长度: {stats['avg_content_length']:.0f} 字符")
            print(f"  总浏览量: {stats['total_views']}")
            print(f"  总点赞数: {stats['total_likes']}")
            print(f"  总回复数: {stats['total_replies']}")
        
        # 2. 用户打卡情况分析
        print("\n\n2. 每个人的打卡情况")
        print("-" * 40)
        user_stats = report['user_stats']
        
        # 按打卡数排序
        sorted_users = sorted(user_stats.items(), key=lambda x: x[1]['total_checkins'], reverse=True)
        
        for author_name, stats in sorted_users[:10]:  # 显示前10名
            print(f"\n{author_name}:")
            print(f"  总打卡数: {stats['total_checkins']}")
            print(f"  完成任务数: {stats['unique_tasks']}")
            print(f"  完成率: {stats['completion_rate']:.1f}%")
            print(f"  平均内容长度: {stats['avg_content_length']:.0f} 字符")
            print(f"  总浏览量: {stats['total_views']}")
            print(f"  总点赞数: {stats['total_likes']}")
            print(f"  完成的任务: {', '.join(stats['completed_tasks_sorted'])}")
        
        # 3. 学习笔记评分
        print("\n\n3. 学习笔记评分情况")
        print("-" * 40)
        note_scores = report['note_scores']
        
        # 按平均分排序
        sorted_scores = sorted(note_scores.items(), key=lambda x: x[1]['avg_score'], reverse=True)
        
        for author_name, scores in sorted_scores[:10]:  # 显示前10名
            print(f"\n{author_name}:")
            print(f"  平均分: {scores['avg_score']:.1f}")
            print(f"  总分: {scores['total_score']}")
            print(f"  笔记数量: {len(scores['notes'])}")
            if scores['best_note']:
                print(f"  最佳笔记: {scores['best_note']['task_name']} ({scores['best_note']['score']}分)")
            if scores['worst_note']:
                print(f"  最差笔记: {scores['worst_note']['task_name']} ({scores['worst_note']['score']}分)")