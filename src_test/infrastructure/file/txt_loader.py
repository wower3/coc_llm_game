"""
文本文件加载器
从原 util/load_txt_with_keyword.py 提取
"""

import os
import re
import json
from typing import Dict, List, Any, Optional


class TxtContentLoader:
    """加载和解析包含关键字的txt文件内容"""

    def __init__(self, encoding_preferences=None):
        if encoding_preferences is None:
            encoding_preferences = ['utf-8', 'gbk', 'gb2312', 'big5']
        self.encoding_preferences = encoding_preferences

    def read_txt_file(self, file_path: str) -> Optional[str]:
        """读取txt文件，尝试多种编码"""
        for encoding in self.encoding_preferences:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
            except Exception as e:
                print(f"读取文件 {file_path} 失败 ({encoding}): {e}")
                continue
        print(f"无法用任何编码读取文件: {file_path}")
        return None

    def read_txt_file_lines(self, file_path: str) -> Optional[List[str]]:
        """读取txt文件为行列表"""
        for encoding in self.encoding_preferences:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.readlines()
            except UnicodeDecodeError:
                continue
            except Exception as e:
                print(f"读取文件 {file_path} 失败 ({encoding}): {e}")
                continue
        print(f"无法用任何编码读取文件: {file_path}")
        return None

    def extract_content_by_keyword(self, content: str, keyword: str,
                                   context_before: int = 3,
                                   context_after: int = 3) -> List[Dict[str, Any]]:
        """从内容中提取包含关键字的部分及上下文"""
        lines = content.split('\n')
        results = []

        for i, line in enumerate(lines):
            if keyword in line:
                start_line = max(0, i - context_before)
                end_line = min(len(lines), i + context_after + 1)
                context_lines = lines[start_line:end_line]
                context = '\n'.join(context_lines)
                paragraph = self.extract_paragraph(lines, i)

                results.append({
                    'line_number': i + 1,
                    'line_content': line,
                    'context': context,
                    'paragraph': paragraph,
                    'context_range': {
                        'start_line': start_line + 1,
                        'end_line': end_line + 1
                    }
                })
        return results

    def extract_paragraph(self, lines: List[str], line_index: int) -> str:
        """提取包含指定行的段落"""
        start_idx = line_index
        while start_idx > 0 and lines[start_idx - 1].strip() != '':
            start_idx -= 1
        end_idx = line_index
        while end_idx < len(lines) - 1 and lines[end_idx + 1].strip() != '':
            end_idx += 1
        return '\n'.join(lines[start_idx:end_idx + 1]).strip()

    def extract_metadata(self, content: str) -> Dict[str, Any]:
        """尝试从文本中提取元数据"""
        metadata = {}
        lines = content.split('\n')[:20]
        for line in lines:
            if line.strip() and not metadata.get('title'):
                metadata['title'] = line.strip()
                break
        metadata['total_lines'] = len(content.split('\n'))
        metadata['total_chars'] = len(content)
        return metadata


class TxtKeywordSearch:
    """搜索包含关键字的txt文件"""

    def __init__(self, folder_path: str, loader=None):
        self.folder_path = folder_path
        self.loader = loader if loader else TxtContentLoader()

    def search_files(self, keyword: str, recursive: bool = True) -> List[Dict[str, Any]]:
        """搜索包含关键字的txt文件"""
        results = []
        if not os.path.exists(self.folder_path):
            return results
        if recursive:
            for root, dirs, files in os.walk(self.folder_path):
                for file in files:
                    if file.endswith('.txt'):
                        self._process_file(os.path.join(root, file), keyword, results)
        return results

    def _process_file(self, file_path: str, keyword: str, results: List[Dict[str, Any]]):
        """处理单个文件"""
        content = self.loader.read_txt_file(file_path)
        if content is None:
            return
        if keyword in content:
            matches = self.loader.extract_content_by_keyword(content, keyword)
            if matches:
                metadata = self.loader.extract_metadata(content)
                results.append({
                    'file_path': file_path,
                    'file_name': os.path.basename(file_path),
                    'keyword': keyword,
                    'matches': matches,
                    'metadata': metadata,
                    'full_content': content
                })
