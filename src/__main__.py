#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI续写红楼梦 - 主入口
允许通过 `python -m src` 运行CLI
"""

import sys
from pathlib import Path

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from cli.main import cli

if __name__ == '__main__':
    cli()
