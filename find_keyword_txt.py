import os
import re

def find_txt_with_keyword(folder_path, keyword):
    """
    在指定文件夹中查找包含关键字的txt文件

    参数:
        folder_path: 文件夹路径
        keyword: 要查找的关键字

    返回:
        list: 包含关键字的文件路径列表
    """
    result_files = []

    # 检查文件夹是否存在
    if not os.path.exists(folder_path):
        print(f"错误: 文件夹 '{folder_path}' 不存在")
        return result_files

    # 遍历文件夹中的所有文件
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            # 只处理txt文件
            if file.endswith('.txt'):
                file_path = os.path.join(root, file)
                try:
                    # 读取文件内容并检查是否包含关键字
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if keyword in content:
                            result_files.append(file_path)
                            print(f"找到包含关键字 '{keyword}' 的文件: {file_path}")
                except UnicodeDecodeError:
                    # 如果utf-8编码失败，尝试其他编码
                    try:
                        with open(file_path, 'r', encoding='gbk') as f:
                            content = f.read()
                            if keyword in content:
                                result_files.append(file_path)
                                print(f"找到包含关键字 '{keyword}' 的文件: {file_path}")
                    except:
                        print(f"警告: 无法读取文件 {file_path} (编码问题)")
                except Exception as e:
                    print(f"警告: 读取文件 {file_path} 时出错: {e}")

    # 输出统计结果
    if result_files:
        print(f"\n总计找到 {len(result_files)} 个包含关键字 '{keyword}' 的文件")
    else:
        print(f"\n未找到包含关键字 '{keyword}' 的txt文件")

    return result_files

def find_txt_with_keyword_and_context(folder_path, keyword, context_lines=3):
    """
    在指定文件夹中查找包含关键字的txt文件，并显示上下文

    参数:
        folder_path: 文件夹路径
        keyword: 要查找的关键字
        context_lines: 显示上下文行数（默认3行）

    返回:
        dict: 文件名 -> 包含上下文的内容字典
    """
    result_dict = {}

    # 检查文件夹是否存在
    if not os.path.exists(folder_path):
        print(f"错误: 文件夹 '{folder_path}' 不存在")
        return result_dict

    # 遍历文件夹中的所有文件
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            # 只处理txt文件
            if file.endswith('.txt'):
                file_path = os.path.join(root, file)
                try:
                    # 读取文件内容
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()

                    # 检查每一行是否包含关键字
                    for i, line in enumerate(lines):
                        if keyword in line:
                            # 计算上下文行范围
                            start_line = max(0, i - context_lines)
                            end_line = min(len(lines), i + context_lines + 1)

                            # 获取上下文内容
                            context = ''.join(lines[start_line:end_line])

                            # 保存结果
                            if file_path not in result_dict:
                                result_dict[file_path] = []
                            result_dict[file_path].append({
                                'line_number': i + 1,
                                'context': context
                            })

                            print(f"\n在文件 {file_path} 中第 {i+1} 行找到关键字 '{keyword}':")
                            print("-" * 50)
                            print(context)
                            print("-" * 50)

                except UnicodeDecodeError:
                    # 如果utf-8编码失败，尝试其他编码
                    try:
                        with open(file_path, 'r', encoding='gbk') as f:
                            lines = f.readlines()

                        for i, line in enumerate(lines):
                            if keyword in line:
                                start_line = max(0, i - context_lines)
                                end_line = min(len(lines), i + context_lines + 1)
                                context = ''.join(lines[start_line:end_line])

                                if file_path not in result_dict:
                                    result_dict[file_path] = []
                                result_dict[file_path].append({
                                    'line_number': i + 1,
                                    'context': context
                                })

                                print(f"\n在文件 {file_path} 中第 {i+1} 行找到关键字 '{keyword}':")
                                print("-" * 50)
                                print(context)
                                print("-" * 50)
                    except:
                        print(f"警告: 无法读取文件 {file_path} (编码问题)")
                except Exception as e:
                    print(f"警告: 读取文件 {file_path} 时出错: {e}")

    # 输出统计结果
    if result_dict:
        total_matches = sum(len(matches) for matches in result_dict.values())
        print(f"\n总计在 {len(result_dict)} 个文件中找到 {total_matches} 处关键字 '{keyword}'")
    else:
        print(f"\n未找到包含关键字 '{keyword}' 的txt文件")

    return result_dict

def find_txt_with_regex(folder_path, pattern, case_sensitive=False):
    """
    使用正则表达式在txt文件中查找匹配的内容

    参数:
        folder_path: 文件夹路径
        pattern: 正则表达式模式
        case_sensitive: 是否区分大小写（默认不区分）

    返回:
        dict: 文件名 -> 匹配结果列表
    """
    result_dict = {}

    # 检查文件夹是否存在
    if not os.path.exists(folder_path):
        print(f"错误: 文件夹 '{folder_path}' 不存在")
        return result_dict

    # 编译正则表达式
    flags = 0 if case_sensitive else re.IGNORECASE
    regex = re.compile(pattern, flags)

    # 遍历文件夹中的所有文件
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith('.txt'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # 使用正则表达式查找所有匹配
                    matches = regex.findall(content)
                    if matches:
                        result_dict[file_path] = matches
                        print(f"在文件 {file_path} 中找到 {len(matches)} 处匹配:")
                        for match in matches:
                            print(f"  - {match}")

                except UnicodeDecodeError:
                    try:
                        with open(file_path, 'r', encoding='gbk') as f:
                            content = f.read()

                        matches = regex.findall(content)
                        if matches:
                            result_dict[file_path] = matches
                            print(f"在文件 {file_path} 中找到 {len(matches)} 处匹配:")
                            for match in matches:
                                print(f"  - {match}")
                    except:
                        print(f"警告: 无法读取文件 {file_path} (编码问题)")
                except Exception as e:
                    print(f"警告: 读取文件 {file_path} 时出错: {e}")

    return result_dict

def main():
    """主函数示例"""
    # 设置文件夹路径和关键字
    folder_path = r"./scenes/chapter1"  # 相对路径
    keyword = "询问居民"

    print(f"正在查找文件夹 '{folder_path}' 中包含关键字 '{keyword}' 的txt文件...")
    print("=" * 60)

    # 方法1: 简单查找包含关键字的文件
    print("方法1: 简单查找")
    print("-" * 60)
    result_files = find_txt_with_keyword(folder_path, keyword)

    print("\n" + "=" * 60)

    # 方法2: 查找并显示上下文
    print("方法2: 查找并显示上下文")
    print("-" * 60)
    result_dict = find_txt_with_keyword_and_context(folder_path, keyword, context_lines=2)

    print("\n" + "=" * 60)

    # 方法3: 使用正则表达式查找
    print("方法3: 使用正则表达式查找")
    print("-" * 60)
    # 查找包含"询问"和"居民"的文本（可以不连续）
    pattern = r"询问.*?居民"
    result_regex = find_txt_with_regex(folder_path, pattern, case_sensitive=False)

    return result_files, result_dict, result_regex

if __name__ == "__main__":
    main()