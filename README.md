# 学习笔记分析系统

> 本项目仅供学习交流使用，不涉及任何商业用途。如有侵权，敬请联系删除！

一个集成文章爬虫、学习笔记分析和评分分析的综合系统。仅供娱乐，博您一笑！

## 功能特性

### 🕷️ 文章爬虫模块 (Spider)
- **多模式爬取**: 支持单配置、批量、增量爬取
- **智能去重**: 自动过滤重复文章
- **增量更新**: 只爬取新发布的文章
- **配置管理**: 支持多个爬取配置的管理
- **数据导出**: 支持JSON和CSV格式导出

### 📊 学习笔记分析模块 (Analyzer)
- **任务分析**: 分析每个学习任务的打卡情况
- **用户分析**: 统计每个用户的学习进度和表现
- **AI评分**: 使用大模型对学习笔记进行智能评分
- **报告生成**: 生成详细的分析报告

### 📈 评分分析模块 (Score Analyzer)
- **作者统计**: 分析每个作者的评分数据
- **排名系统**: 多种排序方式的排名统计
- **数据导出**: 导出详细的分析报告
- **可视化**: 提供清晰的数据展示

## 项目结构

```
learning-note-analyzer/
├── src/                    # 源代码目录
│   ├── spider/            # 文章爬虫模块
│   │   ├── __init__.py
│   │   └── spider.py
│   ├── analyzer/          # 学习笔记分析模块
│   │   ├── __init__.py
│   │   └── analyzer.py
│   ├── score_analyzer/    # 评分分析模块
│   │   ├── __init__.py
│   │   └── score_analyzer.py
│   └── utils/             # 工具模块
│       ├── __init__.py
│       ├── config_utils.py
│       ├── file_utils.py
│       └── logger.py
├── config/                # 配置文件目录
│   ├── default.yaml       # 默认配置
│   └── config.example.yaml # 示例配置
├── data/                  # 数据目录
├── logs/                  # 日志目录
├── tests/                 # 测试目录
├── docs/                  # 文档目录
├── cli.py                 # 命令行接口
├── requirements.txt       # 依赖列表
├── setup.py              # 安装脚本
├── .env.example          # 环境变量示例
└── README.md             # 项目说明
```

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd learning-note-analyzer

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置设置

```bash
# 复制配置文件
cp config/config.example.yaml config/config.yaml

# 复制环境变量文件
cp .env.example .env
```

编辑 `.env` 文件，设置必要的环境变量：

```env
# OpenAI API配置（用于学习笔记评分）
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_BASE_URL=https://api.modelarts-maas.com/v1
```

### 3. 使用方法

#### 命令行界面

```bash
# 查看帮助
python cli.py --help

# 运行文章爬虫
python cli.py spider --mode batch

# 运行学习笔记分析
python cli.py analyzer --print-report

# 运行评分分析
python cli.py score_analyzer --print-report --export

# 运行所有模块
python cli.py all --print-report
```

#### 作为Python包使用

```python
from src.spider import ArticleSpider
from src.analyzer import LearningNoteAnalyzer
from src.score_analyzer import ScoreAnalyzer

# 使用爬虫
spider = ArticleSpider()
articles = spider.get_all_articles_batch()

# 使用分析器
analyzer = LearningNoteAnalyzer()
report = analyzer.generate_report()

# 使用评分分析器
score_analyzer = ScoreAnalyzer()
analysis = score_analyzer.generate_analysis_report()
```

## 详细使用说明

### 文章爬虫模块

#### 单配置爬取
```bash
python cli.py spider --mode single --config-name your_config_name
```

#### 批量爬取
```bash
python cli.py spider --mode batch
```

#### 增量爬取
```bash
python cli.py spider --mode incremental
```

### 学习笔记分析模块

分析模块会自动：
1. 加载文章数据
2. 筛选学习笔记（包含"DAY"关键词的文章）
3. 分析任务打卡情况
4. 分析用户打卡情况
5. 使用AI对笔记进行评分
6. 生成综合分析报告

### 评分分析模块

评分分析模块提供：
- 作者统计分析
- 多种排序方式
- 详细报告导出
- 排名查询功能

## 配置说明

### 主配置文件 (config/config.yaml)

```yaml
# 应用程序基本信息
app:
  name: "学习笔记分析系统"
  version: "1.0.0"

# 数据目录配置
data:
  base_dir: "data"

# 日志配置
logging:
  level: "INFO"
  file_enabled: true
  console_enabled: true

# 爬虫配置
spider:
  timeout: 30
  max_retries: 3
  
# 分析器配置
analyzer:
  llm:
    model: "deepseek-v3"
    temperature: 0.3
  scoring:
    enabled: true
    api_delay: 1

# 评分分析器配置
score_analyzer:
  sorting:
    default_method: "checkin_and_score"
```

### 环境变量 (.env)

```env
# OpenAI API配置
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=https://api.modelarts-maas.com/v1
```

## 数据格式

### 文章数据格式
```json
{
  "title": "文章标题",
  "author_name": "作者名称",
  "task_name": "任务名称",
  "content_summary": "内容摘要",
  "view_count": 100,
  "like_count": 10,
  "reply_count": 5,
  "publish_time": "2024-01-01 12:00:00"
}
```

### 评分数据格式
```csv
author,task,score,comment,content_length,title
张三,DAY1,85,"内容详实，思考深入",500,"DAY1学习总结"
```

## 开发指南

### 安装开发依赖
```bash
pip install -e ".[dev]"
```

### 运行测试
```bash
pytest tests/
```

### 代码格式化
```bash
black src/ tests/
```

### 类型检查
```bash
mypy src/
```

## 常见问题

### Q: 如何添加新的爬虫配置？
A: 在爬虫实例中使用 `add_config()` 方法添加新配置，或直接修改配置文件。

### Q: 评分功能不工作怎么办？
A: 请检查 `.env` 文件中的 `OPENAI_API_KEY` 是否正确设置。

### Q: 如何自定义评分规则？
A: 可以修改 `analyzer.py` 中的评分提示词，或在配置文件中调整评分参数。

### Q: 数据文件在哪里？
A: 默认情况下，所有数据文件都保存在 `data/` 目录中。

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 更新日志

### v1.0.0
- 初始版本发布
- 集成三个核心模块
- 提供统一的CLI接口
- 完善的配置管理系统