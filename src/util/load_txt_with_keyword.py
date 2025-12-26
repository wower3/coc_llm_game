import os
import re
import json
from typing import Dict, List, Any, Optional, Union

class TxtContentLoader:
    """
    加载和解析包含关键字的txt文件内容
    """

    def __init__(self, encoding_preferences=None):
        """
        初始化加载器

        参数:
            encoding_preferences: 编码偏好列表，默认为['utf-8', 'gbk', 'gb2312', 'big5']
        """
        if encoding_preferences is None:
            encoding_preferences = ['utf-8', 'gbk', 'gb2312', 'big5']
        self.encoding_preferences = encoding_preferences

    def read_txt_file(self, file_path: str) -> Optional[str]:
        """
        读取txt文件，尝试多种编码

        参数:
            file_path: txt文件路径

        返回:
            文件内容字符串，如果读取失败则返回None
        """
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
        """
        读取txt文件为行列表

        参数:
            file_path: txt文件路径

        返回:
            文件行列表，如果读取失败则返回None
        """
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
        """
        从内容中提取包含关键字的部分及上下文

        参数:
            content: 文本内容
            keyword: 查找的关键字
            context_before: 关键字前的上下文行数
            context_after: 关键字后的上下文行数

        返回:
            匹配结果列表，每个结果包含行号、关键字和上下文
        """
        lines = content.split('\n')
        results = []

        for i, line in enumerate(lines):
            if keyword in line:
                # 计算上下文范围
                start_line = max(0, i - context_before)
                end_line = min(len(lines), i + context_after + 1)

                # 提取上下文
                context_lines = lines[start_line:end_line]
                context = '\n'.join(context_lines)

                # 获取段落（空行分隔）
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
        """
        提取包含指定行的段落（以空行分隔）

        参数:
            lines: 所有行列表
            line_index: 目标行索引

        返回:
            段落字符串
        """
        # 向前查找段落开始
        start_idx = line_index
        while start_idx > 0 and lines[start_idx - 1].strip() != '':
            start_idx -= 1

        # 向后查找段落结束
        end_idx = line_index
        while end_idx < len(lines) - 1 and lines[end_idx + 1].strip() != '':
            end_idx += 1

        # 提取段落
        paragraph_lines = lines[start_idx:end_idx + 1]
        return '\n'.join(paragraph_lines).strip()

    def extract_metadata(self, content: str) -> Dict[str, Any]:
        """
        尝试从文本中提取元数据（标题、作者、场景等）

        参数:
            content: 文本内容

        返回:
            元数据字典
        """
        metadata = {}
        lines = content.split('\n')[:20]  # 只检查前20行

        # 提取可能的标题（第一行非空行）
        for line in lines:
            if line.strip() and not metadata.get('title'):
                metadata['title'] = line.strip()
                break

        # 查找常见元数据格式
        for line in lines:
            line_lower = line.lower()

            # 作者信息
            if '作者：' in line or 'author:' in line or '作者:' in line:
                metadata['author'] = line.split('：')[-1].strip() if '：' in line else line.split(':')[-1].strip()

            # 场景编号
            if '场景' in line or 'scene' in line_lower:
                if '场景' in line:
                    metadata['scene'] = line.split('场景')[-1].strip()
                elif 'scene' in line_lower:
                    metadata['scene'] = line_lower.split('scene')[-1].strip()

            # 日期
            date_pattern = r'(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}日?)'
            date_match = re.search(date_pattern, line)
            if date_match:
                metadata['date'] = date_match.group(0)

        # 统计信息
        metadata['total_lines'] = len(content.split('\n'))
        metadata['total_chars'] = len(content)
        metadata['total_words'] = len(content.split())

        return metadata

    def analyze_scene_structure(self, content: str) -> Dict[str, Any]:
        """
        分析场景结构（对话、描述、指令等）

        参数:
            content: 文本内容

        返回:
            结构分析结果
        """
        lines = content.split('\n')
        analysis = {
            'dialogue_lines': 0,
            'description_lines': 0,
            'instruction_lines': 0,
            'speakers': set(),
            'dialogue_patterns': []
        }

        # 对话模式正则表达式
        dialogue_patterns = [
            r'^(.*?)：',           # 中文冒号
            r'^(.*?):',            # 英文冒号
            r'^(.*?)「',           # 中文引号
            r'^(.*?)"',            # 英文引号
        ]

        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue

            # 检查是否为对话
            is_dialogue = False
            for pattern in dialogue_patterns:
                match = re.match(pattern, line_stripped)
                if match:
                    speaker = match.group(1).strip()
                    analysis['speakers'].add(speaker)
                    analysis['dialogue_lines'] += 1
                    is_dialogue = True

                    # 记录对话模式
                    analysis['dialogue_patterns'].append({
                        'speaker': speaker,
                        'content': line_stripped[len(speaker) + 1:].strip(),
                        'pattern': pattern
                    })
                    break

            if not is_dialogue:
                # 检查是否为指令（以特殊符号开头）
                if line_stripped.startswith('【') or line_stripped.startswith('[') or \
                   line_stripped.startswith('*') or line_stripped.startswith('-') or \
                   line_stripped.lower().startswith('提示') or \
                   line_stripped.lower().startswith('note') or \
                   line_stripped.lower().startswith('注意'):
                    analysis['instruction_lines'] += 1
                else:
                    analysis['description_lines'] += 1

        analysis['speakers'] = list(analysis['speakers'])
        analysis['total_lines'] = len(lines)

        return analysis


class TxtKeywordSearch:
    """
    搜索包含关键字的txt文件并加载内容
    """

    def __init__(self, folder_path: str, loader=None):
        """
        初始化搜索器

        参数:
            folder_path: 搜索的文件夹路径
            loader: TxtContentLoader实例
        """
        self.folder_path = folder_path
        self.loader = loader if loader else TxtContentLoader()

    def search_files(self, keyword: str, recursive: bool = True) -> List[Dict[str, Any]]:
        """
        搜索包含关键字的txt文件

        参数:
            keyword: 查找的关键字
            recursive: 是否递归搜索子文件夹

        返回:
            搜索结果列表，包含文件信息和匹配内容
        """
        results = []

        # 检查文件夹是否存在
        if not os.path.exists(self.folder_path):
            print(f"错误: 文件夹 '{self.folder_path}' 不存在")
            return results

        # 遍历文件
        if recursive:
            for root, dirs, files in os.walk(self.folder_path):
                for file in files:
                    if file.endswith('.txt'):
                        self._process_file(os.path.join(root, file), keyword, results)
        else:
            for file in os.listdir(self.folder_path):
                if file.endswith('.txt'):
                    self._process_file(os.path.join(self.folder_path, file), keyword, results)

        return results

    def _process_file(self, file_path: str, keyword: str, results: List[Dict[str, Any]]):
        """
        处理单个文件

        参数:
            file_path: 文件路径
            keyword: 关键字
            results: 结果列表（会直接修改）
        """
        content = self.loader.read_txt_file(file_path)
        if content is None:
            return

        if keyword in content:
            # 提取匹配信息
            matches = self.loader.extract_content_by_keyword(content, keyword)

            if matches:
                # 提取元数据
                metadata = self.loader.extract_metadata(content)

                # 分析结构
                structure = self.loader.analyze_scene_structure(content)

                # 构建结果
                result = {
                    'file_path': file_path,
                    'file_name': os.path.basename(file_path),
                    'file_dir': os.path.dirname(file_path),
                    'keyword': keyword,
                    'matches': matches,
                    'metadata': metadata,
                    'structure': structure,
                    'full_content': content  # 包含完整内容
                }

                results.append(result)

                # 打印摘要
                self._print_summary(result)

    def _print_summary(self, result: Dict[str, Any]):
        """
        打印结果摘要

        参数:
            result: 搜索结果
        """
        print(f"\n{'='*60}")
        print(f"文件: {result['file_name']}")
        print(f"路径: {result['file_path']}")

        if result['metadata'].get('title'):
            print(f"标题: {result['metadata']['title']}")

        print(f"包含关键字 '{result['keyword']}' {len(result['matches'])} 处")

        for i, match in enumerate(result['matches'], 1):
            print(f"\n匹配 {i} (第 {match['line_number']} 行):")
            print(f"内容: {match['line_content']}")
            print(f"上下文:")
            print("-" * 40)
            print(match['context'])
            print("-" * 40)

        # 打印结构信息
        if result['structure']['speakers']:
            print(f"\n场景对话参与者: {', '.join(result['structure']['speakers'])}")

        print(f"\n统计:")
        print(f"  总行数: {result['metadata']['total_lines']}")
        print(f"  对话行: {result['structure']['dialogue_lines']}")
        print(f"  描述行: {result['structure']['description_lines']}")
        print(f"  指令行: {result['structure']['instruction_lines']}")
        print('='*60)

    def save_results(self, results: List[Dict[str, Any]], output_path: str):
        """
        将搜索结果保存为JSON文件

        参数:
            results: 搜索结果列表
            output_path: 输出文件路径
        """
        # 转换set为list以便JSON序列化
        for result in results:
            if isinstance(result.get('structure', {}).get('speakers'), set):
                result['structure']['speakers'] = list(result['structure']['speakers'])

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"\n结果已保存到: {output_path}")

    def export_to_markdown(self, results: List[Dict[str, Any]], output_path: str):
        """
        将搜索结果导出为Markdown文档

        参数:
            results: 搜索结果列表
            output_path: 输出文件路径
        """
        markdown_content = f"# 搜索结果报告\n\n"
        markdown_content += f"**搜索关键字**: {results[0]['keyword'] if results else 'N/A'}\n\n"
        markdown_content += f"**搜索文件夹**: {self.folder_path}\n\n"
        markdown_content += f"**找到文件数**: {len(results)}\n\n"

        for result in results:
            markdown_content += f"## {result['file_name']}\n\n"
            markdown_content += f"**路径**: `{result['file_path']}`\n\n"

            if result['metadata'].get('title'):
                markdown_content += f"**标题**: {result['metadata']['title']}\n\n"

            markdown_content += f"**包含关键字 '{result['keyword']}' {len(result['matches'])} 处**\n\n"

            for i, match in enumerate(result['matches'], 1):
                markdown_content += f"### 匹配 {i} (第 {match['line_number']} 行)\n\n"
                markdown_content += f"**内容**: `{match['line_content']}`\n\n"
                markdown_content += f"**上下文**:\n\n```\n{match['context']}\n```\n\n"

            markdown_content += f"**段落内容**:\n\n```\n{result['matches'][0]['paragraph'] if result['matches'] else 'N/A'}\n```\n\n"

            markdown_content += f"**结构分析**:\n\n"
            markdown_content += f"- 总行数: {result['metadata']['total_lines']}\n"
            markdown_content += f"- 对话行: {result['structure']['dialogue_lines']}\n"
            markdown_content += f"- 描述行: {result['structure']['description_lines']}\n"
            markdown_content += f"- 指令行: {result['structure']['instruction_lines']}\n"

            if result['structure']['speakers']:
                markdown_content += f"- 参与者: {', '.join(result['structure']['speakers'])}\n"

            markdown_content += "\n---\n\n"

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        print(f"\nMarkdown报告已保存到: {output_path}")


def main():
    """主函数示例"""
    # 设置文件夹路径和关键字 - 使用项目根目录下的scenes文件夹
    import os
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    folder_path = os.path.join(project_root, "scenes")
    keyword = "询问居民"

    print(f"正在加载文件夹 '{folder_path}' 中包含关键字 '{keyword}' 的txt文件...")
    print("=" * 80)

    # 创建搜索器
    search = TxtKeywordSearch(folder_path)

    # 搜索文件
    results = search.search_files(keyword, recursive=True)

    if results:
        print(f"\n{'='*80}")
        print(f"搜索完成！找到 {len(results)} 个包含关键字 '{keyword}' 的文件")

        # 保存结果到JSON
        search.save_results(results, "search_results.json")

        # 导出为Markdown
        search.export_to_markdown(results, "search_report.md")

        # 示例：访问第一个文件的完整内容
        if results:
            first_result = results[0]
            print(f"\n示例：第一个文件 '{first_result['file_name']}' 的完整内容:")
            print("-" * 40)
            print(first_result['full_content'][:500] + "..." if len(first_result['full_content']) > 500 else first_result['full_content'])
            print("-" * 40)

            # 示例：访问元数据
            print(f"\n文件元数据:")
            for key, value in first_result['metadata'].items():
                print(f"  {key}: {value}")
    else:
        print(f"\n未找到包含关键字 '{keyword}' 的txt文件")


# 快速使用函数
def quick_search(folder_path, keyword, output_json=None, output_md=None):
    """
    快速搜索功能

    参数:
        folder_path: 文件夹路径
        keyword: 关键字
        output_json: 输出JSON文件路径（可选）
        output_md: 输出Markdown文件路径（可选）

    返回:
        搜索结果列表
    """
    search = TxtKeywordSearch(folder_path)
    results = search.search_files(keyword, recursive=True)

    if results:
        print(f"找到 {len(results)} 个包含关键字 '{keyword}' 的文件")

        if output_json:
            search.save_results(results, output_json)

        if output_md:
            search.export_to_markdown(results, output_md)

    return results


if __name__ == "__main__":
    main()