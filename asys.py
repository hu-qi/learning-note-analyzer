import json
import re
from typing import List, Dict, Any, Tuple
from collections import defaultdict, Counter
import pandas as pd
from datetime import datetime
from openai import OpenAI
import time
import os
import dotenv
dotenv.load_dotenv()

class LearningNoteAnalyzer:
    def __init__(self, json_file: str = "data/articles.json"):
        """初始化分析器，加载文章数据"""
        # 确保 data 目录存在
        self.data_dir = 'data'
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.json_file = json_file
        self.articles = self.load_articles()
        self.learning_notes = self.filter_learning_notes()
        
        # 初始化大模型客户端
        base_url = "https://api.modelarts-maas.com/v1"  # API地址
        api_key = os.getenv("API_KEY")  # 把yourApiKey替换成已获取的API Key
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        
    def load_articles(self) -> List[Dict[str, Any]]:
        """加载文章数据"""
        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"文件 {self.json_file} 不存在")
            return []
        except json.JSONDecodeError:
            print(f"文件 {self.json_file} 格式错误")
            return []
    
    def filter_learning_notes(self) -> List[Dict[str, Any]]:
        """筛选学习笔记文章"""
        # 定义要匹配的标题模式
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
        
        learning_notes = []
        for article in self.articles:
            title = article.get('title', '')
            for pattern in title_patterns:
                if re.match(pattern, title):
                    # 提取日期和DAY信息
                    match = re.search(r'【(\d{4})-DAY(\d+)学习笔记】', title)
                    if match:
                        article['date'] = match.group(1)
                        article['day'] = int(match.group(2))
                        article['task_name'] = f"DAY{match.group(2)}"
                        learning_notes.append(article)
                    break
        
        print(f"筛选出 {len(learning_notes)} 篇学习笔记")
        return learning_notes
    
    def analyze_task_checkin(self) -> Dict[str, Dict[str, Any]]:
        """分析每个任务的打卡情况"""
        task_stats = defaultdict(lambda: {
            'total_checkins': 0,
            'participants': [],
            'unique_participants': 0,
            'avg_content_length': 0,
            'total_views': 0,
            'total_likes': 0,
            'total_replies': 0
        })
        
        for note in self.learning_notes:
            task_name = note['task_name']
            author_name = note['author_name']
            content_length = len(note.get('content_summary', ''))
            
            task_stats[task_name]['total_checkins'] += 1
            task_stats[task_name]['participants'].append(author_name)
            task_stats[task_name]['total_views'] += note.get('views', 0)
            task_stats[task_name]['total_likes'] += note.get('likes', 0)
            task_stats[task_name]['total_replies'] += note.get('replies', 0)
            task_stats[task_name]['content_lengths'] = task_stats[task_name].get('content_lengths', []) + [content_length]
        
        # 计算统计数据
        for task_name, stats in task_stats.items():
            stats['unique_participants'] = len(set(stats['participants']))
            stats['avg_content_length'] = sum(stats.get('content_lengths', [])) / len(stats.get('content_lengths', []))
            del stats['content_lengths']  # 删除临时数据
        
        return dict(task_stats)
    
    def analyze_user_checkin(self) -> Dict[str, Dict[str, Any]]:
        """分析每个人的打卡情况"""
        user_stats = defaultdict(lambda: {
            'total_checkins': 0,
            'completed_tasks': [],
            'checkin_dates': [],
            'total_content_length': 0,
            'total_views': 0,
            'total_likes': 0,
            'total_replies': 0,
            'avg_content_length': 0,
            'completion_rate': 0.0
        })
        
        # 获取所有任务
        all_tasks = set(note['task_name'] for note in self.learning_notes)
        total_tasks = len(all_tasks)
        
        for note in self.learning_notes:
            author_name = note['author_name']
            task_name = note['task_name']
            date = note['date']
            content_length = len(note.get('content_summary', ''))
            
            user_stats[author_name]['total_checkins'] += 1
            user_stats[author_name]['completed_tasks'].append(task_name)
            user_stats[author_name]['checkin_dates'].append(date)
            user_stats[author_name]['total_content_length'] += content_length
            user_stats[author_name]['total_views'] += note.get('views', 0)
            user_stats[author_name]['total_likes'] += note.get('likes', 0)
            user_stats[author_name]['total_replies'] += note.get('replies', 0)
        
        # 计算统计数据
        for author_name, stats in user_stats.items():
            stats['unique_tasks'] = len(set(stats['completed_tasks']))
            stats['completion_rate'] = stats['unique_tasks'] / total_tasks * 100
            stats['avg_content_length'] = stats['total_content_length'] / stats['total_checkins'] if stats['total_checkins'] > 0 else 0
            stats['completed_tasks_sorted'] = sorted(set(stats['completed_tasks']), key=lambda x: int(x[3:]))
        
        return dict(user_stats)
    
    def call_llm_for_scoring(self, note_content: str, note_title: str) -> Tuple[int, str]:
        """
        调用大模型服务对学习笔记进行评分
        
        参数:
            note_content: 学习笔记内容
            note_title: 学习笔记标题
            
        返回:
            Tuple[int, str]: (分数, 评语)
        """
        # 构建评分提示
        scoring_prompt = f"""
        请根据以下标准对学习笔记进行评分（满分100分），并给出具体评语：
        
        评分标准：
        1. 内容完整性（30分）：
        - 是否涵盖了课程的核心知识点
        - 是否有详细的解释和说明
        - 是否包含个人理解和思考
        
        2. 结构清晰度（20分）：
        - 是否有清晰的结构和层次
        - 是否使用标题、列表等格式
        - 逻辑是否连贯
        
        3. 实用性（25分）：
        - 是否有实际应用案例
        - 是否包含可操作的建议
        - 是否有创新性的见解
        
        4. 表达质量（15分）：
        - 语言表达是否清晰准确
        - 是否有适当的例子和说明
        - 是否避免了冗余和模糊表达
        
        5. 互动性（10分）：
        - 是否有提问或引发思考的内容
        - 是否有与其他学习者的互动
        - 是否有后续学习计划
        
        学习笔记标题：{note_title}
        学习笔记内容：
        {note_content}
        
        请严格按照以下JSON格式返回评分结果，不要添加任何其他文本或格式：
        {{
            "score": 分数（0-100的整数）,
            "comment": "评语（详细说明评分理由）"
        }}
        """
        
        try:
            # 调用大模型服务
            response = self.client.chat.completions.create(
                model=os.getenv("MODEL_NAME"),  # model参数
                messages=[
                    {"role": "system", "content": "你是一位专业的教育评估专家，擅长对学习笔记进行评分和评价。请严格按照JSON格式返回结果。"},
                    {"role": "user", "content": scoring_prompt},
                ],
                temperature=0.3,  # 降低温度以获得更一致的评分
                stream=False
            )
            
            # 获取返回结果
            result_text = response.choices[0].message.content.strip()
            
            # 处理可能包含的代码块标记
            # 情况1: ```json\n{...}\n```
            if result_text.startswith("```json") and result_text.endswith("```"):
                # 提取JSON部分
                json_str = result_text[7:-3].strip()
                try:
                    result = json.loads(json_str)
                    score = int(result.get("score", 0))
                    comment = result.get("comment", "无评语")
                    score = max(0, min(100, score))
                    return score, comment
                except json.JSONDecodeError:
                    pass
            
            # 情况2: ```\n{...}\n```
            if result_text.startswith("```") and result_text.endswith("```"):
                # 提取JSON部分
                json_str = result_text[3:-3].strip()
                # 如果以json开头，去掉它
                if json_str.startswith("json"):
                    json_str = json_str[4:].strip()
                try:
                    result = json.loads(json_str)
                    score = int(result.get("score", 0))
                    comment = result.get("comment", "无评语")
                    score = max(0, min(100, score))
                    return score, comment
                except json.JSONDecodeError:
                    pass
            
            # 情况3: 直接尝试解析整个文本
            try:
                result = json.loads(result_text)
                score = int(result.get("score", 0))
                comment = result.get("comment", "无评语")
                score = max(0, min(100, score))
                return score, comment
            except json.JSONDecodeError:
                pass
            
            # 如果以上都失败，尝试从文本中提取JSON
            # 使用正则表达式查找JSON对象
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
            
            # 如果仍然失败，尝试使用正则表达式提取分数和评语
            print(f"无法解析JSON结果，尝试提取分数和评语: {result_text[:200]}...")
            
            # 提取分数
            score_match = re.search(r'["\']?score["\']?\s*[:\=]\s*(\d+)', result_text, re.IGNORECASE)
            if score_match:
                score = int(score_match.group(1))
                score = max(0, min(100, score))
            else:
                score = 60  # 默认分数
            
            # 提取评语
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
                
        except Exception as e:
            print(f"调用大模型服务出错: {e}")
            # 返回默认分数和评语
            return 60, f"评分服务暂时不可用，给予默认分数。错误信息: {str(e)}"
    def score_notes(self) -> Dict[str, Dict[str, Any]]:
        """使用大模型服务给每个学习笔记打分"""
        note_scores = {}
        
        print("开始使用大模型服务对学习笔记进行评分...")
        
        for i, note in enumerate(self.learning_notes):
            author_name = note['author_name']
            task_name = note['task_name']
            content = note.get('content_summary', '')
            title = note['title']
            
            print(f"正在评分第 {i+1}/{len(self.learning_notes)} 篇笔记: {title}")
            
            # 调用大模型服务进行评分
            score, comment = self.call_llm_for_scoring(content, title)
            print(f"评分结果: {score}, {comment}")
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
                'title': title
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
        
        return note_scores
    
    def generate_report(self):
        """生成完整的分析报告"""
        print("=" * 60)
        print("学习笔记分析报告")
        print("=" * 60)
        
        # 1. 任务打卡情况分析
        print("\n1. 每个任务的打卡情况")
        print("-" * 40)
        task_stats = self.analyze_task_checkin()
        
        # 按DAY顺序排序
        sorted_tasks = sorted(task_stats.keys(), key=lambda x: int(x[3:]))
        
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
        user_stats = self.analyze_user_checkin()
        
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
        note_scores = self.score_notes()
        
        # 按平均分排序
        sorted_scores = sorted(note_scores.items(), key=lambda x: x[1]['avg_score'], reverse=True)
        
        for author_name, scores in sorted_scores[:10]:  # 显示前10名
            print(f"\n{author_name}:")
            print(f"  平均分: {scores['avg_score']:.1f}")
            print(f"  总分: {scores['total_score']}")
            print(f"  笔记数量: {len(scores['notes'])}")
            print(f"  最佳笔记: {scores['best_note']['task_name']} ({scores['best_note']['score']}分)")
            print(f"  最差笔记: {scores['worst_note']['task_name']} ({scores['worst_note']['score']}分)")
        
        # 4. 保存详细报告到文件
        self.save_detailed_report(task_stats, user_stats, note_scores)
    
    def save_detailed_report(self, task_stats, user_stats, note_scores):
        """保存详细报告到文件"""
        # 创建DataFrame并保存到 data 目录
        task_df = pd.DataFrame.from_dict(task_stats, orient='index')
        task_report_path = os.path.join(self.data_dir, 'task_checkin_report.csv')
        task_df.to_csv(task_report_path, encoding='utf-8')
        
        user_df = pd.DataFrame.from_dict(user_stats, orient='index')
        user_report_path = os.path.join(self.data_dir, 'user_checkin_report.csv')
        user_df.to_csv(user_report_path, encoding='utf-8')
        
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
                    'title': note['title']
                })
        
        score_df = pd.DataFrame(score_details)
        score_report_path = os.path.join(self.data_dir, 'note_scores_report.csv')
        score_df.to_csv(score_report_path, encoding='utf-8')
        
        print(f"\n详细报告已保存到 data 目录:")
        print(f"  - {task_report_path} (任务打卡情况)")
        print(f"  - {user_report_path} (用户打卡情况)")
        print(f"  - {score_report_path} (笔记评分情况)")

if __name__ == "__main__":
    # 创建分析器实例
    analyzer = LearningNoteAnalyzer()
    
    # 生成分析报告
    analyzer.generate_report()