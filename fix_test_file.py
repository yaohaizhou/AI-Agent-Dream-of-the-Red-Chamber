#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 修复test_scoring_v2.py文件
import re

with open('/home/azureuser/code/AI-Agent-Dream-of-the-Red-Chamber/test_scoring_v2.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 替换中文标点符号
content = content.replace('：', ':')
content = content.replace('，', ',')
content = content.replace('；', ';')
content = content.replace('？', '?')
content = content.replace('！', '!')

# 修复字符串问题 - 移除多余的空字符串
content = content.replace('            "",', '')

# 修复可能的字符串拼接问题
content = re.sub(r'"""([^"]*)"""\s*"",\s*', r'"""\1""",\n', content)

with open('/home/azureuser/code/AI-Agent-Dream-of-the-Red-Chamber/test_scoring_v2.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("文件修复完成")