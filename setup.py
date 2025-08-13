#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学习笔记分析系统安装脚本
"""

from setuptools import setup, find_packages
import os

# 读取README文件
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "学习笔记分析系统 - 集成文章爬虫、学习笔记分析和评分分析的综合系统"

# 读取requirements.txt
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    requirements = []
    if os.path.exists(requirements_path):
        with open(requirements_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    requirements.append(line)
    return requirements

setup(
    name="learning-note-analyzer",
    version="1.0.0",
    author="huqi",
    author_email="huqi1024@gmail.com",
    description="学习笔记分析系统 - 集成文章爬虫、学习笔记分析和评分分析",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/hu-qi/learning-note-analyzer",
    
    # 包配置
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    
    # 包含非Python文件
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.yml", "*.json", "*.txt", "*.md"],
    },
    
    # 依赖
    install_requires=read_requirements(),
    
    # 额外依赖
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=0.991",
        ],
        "docs": [
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.0.0",
        ],
    },
    
    # 命令行入口
    entry_points={
        "console_scripts": [
            "learning-analyzer=cli:main",
            "lna=cli:main",  # 简短别名
        ],
    },
    
    # 分类信息
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Education",
        "Topic :: Text Processing :: General",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    
    # Python版本要求
    python_requires=">=3.8",
    
    # 关键词
    keywords="learning, note, analysis, spider, crawler, nlp, education",
    
    # 项目URL
    project_urls={
        "Bug Reports": "https://github.com/yourusername/learning-note-analyzer/issues",
        "Source": "https://github.com/yourusername/learning-note-analyzer",
        "Documentation": "https://learning-note-analyzer.readthedocs.io/",
    },
    
    # 许可证
    license="MIT",
    
    # 是否为zip安全
    zip_safe=False,
)