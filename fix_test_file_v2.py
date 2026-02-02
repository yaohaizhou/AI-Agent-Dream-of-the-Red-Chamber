#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 修复test_scoring_v2.py文件的三引号字符串问题
import re

with open('/home/azureuser/code/AI-Agent-Dream-of-the-Red-Chamber/test_scoring_v2.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 使用正则表达式查找并修复所有的内容字符串
def fix_content_strings(match):
    content_str = match.group(1)
    # 在三引号字符串中，正常的双引号不需要转义，但要确保格式正确
    # 我们需要确保内部的文本不会干扰三引号的边界
    return f'"""{content_str}""",'

# 修复所有content字段
content = re.sub(r'"""((?:(?!""").)*)""",', fix_content_strings, content, flags=re.DOTALL)

# 修复引号问题
content = content.replace('\\"', '"')  # 先清理错误的转义

# 重新处理，确保content字段格式正确
pattern = r'"content":\s*"""\s*\n(.*?)\n\s*""",'
def fix_multiline_content(match):
    inner_content = match.group(1)
    # 保留内部内容，但确保格式正确
    return f'"content": """{inner_content}""",'

content = re.sub(pattern, fix_multiline_content, content, flags=re.DOTALL | re.MULTILINE)

with open('/home/azureuser/code/AI-Agent-Dream-of-the-Red-Chamber/test_scoring_v2.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("文件修复完成")