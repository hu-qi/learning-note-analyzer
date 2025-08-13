#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一CLI接口

提供命令行接口来运行不同的功能模块：
- spider: 文章爬虫
- analyzer: 学习笔记分析
- score_analyzer: 评分分析
- all: 运行所有模块
"""

import argparse
import sys
import os
from pathlib import Path

# 添加src目录到Python路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.spider import ArticleSpider
from src.analyzer import LearningNoteAnalyzer
from src.score_analyzer import ScoreAnalyzer
from src.utils.config_utils import load_config
from src.utils.logger import setup_logger, get_logger


def setup_environment():
    """设置环境"""
    # 加载配置
    config = load_config()
    
    # 设置日志
    setup_logger('cli', config.get('logging', {}).get('level', 'INFO'))
    
    return config


def run_spider(config, args):
    """运行文章爬虫"""
    logger = get_logger('cli')
    logger.info("启动文章爬虫模块")
    
    try:
        # 获取爬虫配置
        spider_config = config.get('spider', {})
        data_dir = config.get('data', {}).get('spider_data_dir', 'data')
        
        # 创建爬虫实例
        spider = ArticleSpider(data_dir=data_dir)
        
        if args.mode == 'single':
            # 单配置爬取
            if not args.config_name:
                logger.error("单配置模式需要指定配置名称 --config-name")
                return False
            
            logger.info(f"使用配置 '{args.config_name}' 进行单配置爬取")
            articles = spider.get_all_articles(
                config_name=args.config_name,
                incremental=args.incremental,
                time_filter=args.time_filter
            )
            logger.info(f"爬取完成，共获取 {len(articles)} 篇文章")
            
            # 保存单配置爬取的结果
            if articles:
                spider.save_to_json(f"articles_{args.config_name}.json", articles)
                spider.save_to_csv(f"articles_{args.config_name}.csv", articles)
                logger.info(f"单配置爬取数据已保存到文件")
            
        elif args.mode == 'batch':
            # 批量爬取
            logger.info("开始批量爬取")
            results = spider.get_all_articles_batch()
            total_articles = sum(len(articles) for articles in results.values())
            logger.info(f"批量爬取完成，共获取 {total_articles} 篇文章")
            
            # 保存批量爬取的结果
            spider.save_batch_results(results)
            logger.info("批量爬取数据已保存到文件")
            
        elif args.mode == 'incremental':
            # 增量爬取
            logger.info("开始增量爬取")
            results = spider.incremental_crawl()
            total_new = sum(len(articles) for articles in results.values())
            logger.info(f"增量爬取完成，共获取 {total_new} 篇新文章")
            
            # 保存增量爬取的结果
            if results and any(articles for articles in results.values()):
                spider.merge_and_save_incremental(results)
                logger.info("增量爬取数据已合并并保存到文件")
            
        else:
            logger.error(f"未知的爬虫模式: {args.mode}")
            return False
        
        logger.info("文章爬虫模块执行完成")
        return True
        
    except Exception as e:
        logger.error(f"文章爬虫模块执行失败: {e}")
        return False


def run_analyzer(config, args):
    """运行学习笔记分析"""
    logger = get_logger('cli')
    logger.info("启动学习笔记分析模块")
    
    try:
        # 获取分析器配置
        analyzer_config = config.get('analyzer', {})
        data_dir = config.get('data', {}).get('analyzer_data_dir', 'data')
        
        # 创建分析器实例
        analyzer = LearningNoteAnalyzer(data_dir=data_dir, config=analyzer_config)
        
        # 生成分析报告
        report = analyzer.generate_report()
        
        if args.print_report:
            analyzer.print_report(report)
        
        logger.info("学习笔记分析模块执行完成")
        return True
        
    except Exception as e:
        logger.error(f"学习笔记分析模块执行失败: {e}")
        return False


def run_score_analyzer(config, args):
    """运行评分分析"""
    logger = get_logger('cli')
    logger.info("启动评分分析模块")
    
    try:
        # 获取评分分析器配置
        score_config = config.get('score_analyzer', {})
        data_dir = config.get('data', {}).get('score_analyzer_data_dir', 'data')
        
        # 获取数据源文件
        csv_file = score_config.get('data_source', {}).get('csv_file', 'data/note_scores_report.csv')
        
        # 创建评分分析器实例
        score_analyzer = ScoreAnalyzer(csv_file=csv_file, data_dir=data_dir)
        
        # 生成分析报告
        report = score_analyzer.generate_analysis_report()
        
        if args.print_report:
            score_analyzer.print_analysis_report(report)
        
        if args.export:
            score_analyzer.export_detailed_report()
        
        logger.info("评分分析模块执行完成")
        return True
        
    except Exception as e:
        logger.error(f"评分分析模块执行失败: {e}")
        return False


def run_all_modules(config, args):
    """运行所有模块"""
    logger = get_logger('cli')
    logger.info("启动所有模块")
    
    success_count = 0
    total_modules = 3
    
    # 1. 运行爬虫模块
    logger.info("=== 第1步：运行文章爬虫 ===")
    if run_spider(config, args):
        success_count += 1
        logger.info("文章爬虫模块执行成功")
    else:
        logger.error("文章爬虫模块执行失败")
    
    # 2. 运行学习笔记分析模块
    logger.info("=== 第2步：运行学习笔记分析 ===")
    if run_analyzer(config, args):
        success_count += 1
        logger.info("学习笔记分析模块执行成功")
    else:
        logger.error("学习笔记分析模块执行失败")
    
    # 3. 运行评分分析模块
    logger.info("=== 第3步：运行评分分析 ===")
    if run_score_analyzer(config, args):
        success_count += 1
        logger.info("评分分析模块执行成功")
    else:
        logger.error("评分分析模块执行失败")
    
    logger.info(f"所有模块执行完成，成功: {success_count}/{total_modules}")
    return success_count == total_modules


def create_parser():
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description="学习笔记分析系统 - 集成文章爬虫、学习笔记分析和评分分析",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  %(prog)s spider --mode single --config-name example_config
  %(prog)s spider --mode batch
  %(prog)s spider --mode incremental
  %(prog)s analyzer --print-report
  %(prog)s score_analyzer --print-report --export
  %(prog)s all --print-report
        """
    )
    
    # 添加全局参数
    parser.add_argument(
        '--config', '-c',
        type=str,
        default='config/config.yaml',
        help='配置文件路径 (默认: config/config.yaml)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='启用详细输出'
    )
    
    # 创建子命令
    subparsers = parser.add_subparsers(
        dest='command',
        help='可用命令',
        metavar='COMMAND'
    )
    
    # 爬虫命令
    spider_parser = subparsers.add_parser(
        'spider',
        aliases=['crawl', 'fetch'],
        help='运行文章爬虫'
    )
    spider_parser.add_argument(
        '--mode', '-m',
        choices=['single', 'batch', 'incremental'],
        default='batch',
        help='爬取模式 (默认: batch)'
    )
    spider_parser.add_argument(
        '--config-name',
        type=str,
        help='单配置模式下的配置名称'
    )
    spider_parser.add_argument(
        '--incremental',
        action='store_true',
        help='启用增量爬取'
    )
    spider_parser.add_argument(
        '--time-filter',
        type=str,
        help='时间过滤器 (格式: YYYY-MM-DD)'
    )
    
    # 分析器命令
    analyzer_parser = subparsers.add_parser(
        'analyzer',
        aliases=['analyze', 'analysis'],
        help='运行学习笔记分析'
    )
    analyzer_parser.add_argument(
        '--print-report',
        action='store_true',
        default=True,
        help='打印分析报告到控制台'
    )
    
    # 评分分析器命令
    score_parser = subparsers.add_parser(
        'score_analyzer',
        aliases=['score', 'ranking'],
        help='运行评分分析'
    )
    score_parser.add_argument(
        '--print-report',
        action='store_true',
        default=True,
        help='打印分析报告到控制台'
    )
    score_parser.add_argument(
        '--export',
        action='store_true',
        help='导出详细报告'
    )
    
    # 全部模块命令
    all_parser = subparsers.add_parser(
        'all',
        aliases=['full', 'complete'],
        help='运行所有模块'
    )
    all_parser.add_argument(
        '--mode', '-m',
        choices=['single', 'batch', 'incremental'],
        default='batch',
        help='爬虫模式 (默认: batch)'
    )
    all_parser.add_argument(
        '--config-name',
        type=str,
        help='单配置模式下的配置名称'
    )
    all_parser.add_argument(
        '--incremental',
        action='store_true',
        help='启用增量爬取'
    )
    all_parser.add_argument(
        '--time-filter',
        type=str,
        help='时间过滤器 (格式: YYYY-MM-DD)'
    )
    all_parser.add_argument(
        '--print-report',
        action='store_true',
        default=True,
        help='打印分析报告到控制台'
    )
    all_parser.add_argument(
        '--export',
        action='store_true',
        help='导出详细报告'
    )
    
    return parser


def main():
    """主函数"""
    parser = create_parser()
    args = parser.parse_args()
    
    # 如果没有指定命令，显示帮助
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        # 设置环境
        config = setup_environment()
        
        # 根据命令执行相应的模块
        if args.command in ['spider', 'crawl', 'fetch']:
            success = run_spider(config, args)
        elif args.command in ['analyzer', 'analyze', 'analysis']:
            success = run_analyzer(config, args)
        elif args.command in ['score_analyzer', 'score', 'ranking']:
            success = run_score_analyzer(config, args)
        elif args.command in ['all', 'full', 'complete']:
            success = run_all_modules(config, args)
        else:
            print(f"未知命令: {args.command}")
            parser.print_help()
            return 1
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n用户中断执行")
        return 1
    except Exception as e:
        print(f"执行失败: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())