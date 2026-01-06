#!/bin/bash

echo "========================================"
echo "      Log Archive Script (Bash)"
echo "========================================"
echo

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 获取今天的日期
TODAY=$(date +%Y%m%d)

echo "Today: $TODAY"
echo "Archiving logs from before today..."
echo

# 创建 history 目录
mkdir -p "history"

# 查找需要归档的文件夹
declare -a FOLDERS_TO_ARCHIVE
COUNT=0

for dir in */; do
    # 移除末尾的斜杠
    FOLDER_NAME="${dir%/}"

    # 跳过 history 目录
    if [[ "$FOLDER_NAME" == "history" ]]; then
        continue
    fi

    # 获取文件夹名的前8个字符
    FOLDER_DATE="${FOLDER_NAME:0:8}"

    # 检查是否匹配日志文件夹格式（8位数字开头）
    if [[ "$FOLDER_DATE" =~ ^[0-9]{8}$ ]]; then
        # 只归档今天之前的日志
        if [[ "$FOLDER_DATE" < "$TODAY" ]]; then
            FOLDERS_TO_ARCHIVE+=("$FOLDER_NAME")
            ((COUNT++))
            echo "  - $FOLDER_NAME ($FOLDER_DATE)"
        fi
    fi
done

echo
echo "Found $COUNT folders to archive"
echo

if [[ $COUNT -eq 0 ]]; then
    echo "No log folders found to archive"
    exit 0
fi

echo "Starting archive..."
echo

# 归档处理
SUCCESS=0
FAILED=0

for FOLDER_NAME in "${FOLDERS_TO_ARCHIVE[@]}"; do
    FOLDER_DATE="${FOLDER_NAME:0:8}"

    # 创建按日期分类的目录
    HISTORY_DIR="history/$FOLDER_DATE"
    mkdir -p "$HISTORY_DIR"

    # 压缩为 zip 文件
    ZIP_FILE="$HISTORY_DIR/$FOLDER_NAME.zip"

    echo "Compressing: $FOLDER_NAME"

    # 使用 zip 命令压缩
    if command -v zip &> /dev/null; then
        zip -rq "$ZIP_FILE" "$FOLDER_NAME" 2>/dev/null
    else
        # 如果没有 zip，尝试使用 tar + gzip
        tar -czf "${ZIP_FILE%.zip}.tar.gz" "$FOLDER_NAME" 2>/dev/null
        ZIP_FILE="${ZIP_FILE%.zip}.tar.gz"
    fi

    # 检查压缩文件是否存在且大小大于 100 字节
    if [[ -f "$ZIP_FILE" ]]; then
        ZIP_SIZE=$(stat -c%s "$ZIP_FILE" 2>/dev/null || stat -f%z "$ZIP_FILE" 2>/dev/null)
        if [[ $ZIP_SIZE -gt 100 ]]; then
            # 删除源文件夹
            rm -rf "$FOLDER_NAME"
            echo "  Done - Created zip"
            ((SUCCESS++))
        else
            echo "  Failed - Invalid zip file"
            ((FAILED++))
        fi
    else
        echo "  Failed - Zip not created"
        ((FAILED++))
    fi
done

echo
echo "========================================"
echo "      Archive Complete!"
echo "========================================"
echo
echo "Statistics:"
echo "  Success: $SUCCESS folders"
echo "  Failed: $FAILED folders"
echo
echo "History logs saved in: history/"
echo
