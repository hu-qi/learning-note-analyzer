"""Web Spider Module

Provides article scraping functionality with support for:
- Single configuration crawling
- Batch crawling
- Incremental crawling
- Time-filtered crawling
"""

from .spider import ArticleSpider

__all__ = ['ArticleSpider']