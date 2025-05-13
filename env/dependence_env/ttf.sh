#!/bin/bash

# 脚本名称: install_matplotlib_chinese_font.sh
# 功能：自动安装SimHei字体到Matplotlib并清理缓存

# 退出状态码
SUCCESS=0
ERROR_NO_FONT=1
ERROR_MATPLOTLIB_NOT_FOUND=2
ERROR_PERMISSION_DENIED=3

# ------------------------- 检查字体文件 -------------------------
FONT_FILE="SimHei.ttf"

if [ ! -f "$FONT_FILE" ]; then
    echo "错误：当前目录下未找到字体文件 $FONT_FILE"
    exit $ERROR_NO_FONT
fi

# ------------------------- 定位Matplotlib字体路径 -------------------------
# 通过Python命令获取Matplotlib安装路径
MATPLOTLIB_PATH=$(python3 -c "import matplotlib; print(matplotlib.__path__[0])" 2>/dev/null)

if [ $? -ne 0 ]; then
    echo "错误：未找到Matplotlib安装路径，请先安装Matplotlib"
    exit $ERROR_MATPLOTLIB_NOT_FOUND
fi

TARGET_FONT_DIR="$MATPLOTLIB_PATH/mpl-data/fonts/ttf"

# 创建目标目录（如果不存在）
mkdir -p "$TARGET_FONT_DIR" 2>/dev/null

# ------------------------- 复制字体文件 -------------------------
echo "正在安装字体到: $TARGET_FONT_DIR"

if ! cp -v "$FONT_FILE" "$TARGET_FONT_DIR/"; then
    echo "错误：权限不足，请使用sudo运行脚本或检查目录权限"
    exit $ERROR_PERMISSION_DENIED
fi

# ------------------------- 清理缓存 -------------------------
CACHE_DIR=$(python3 -c "import matplotlib as mpl; print(mpl.get_cachedir())" 2>/dev/null)

if [ -d "$CACHE_DIR" ]; then
    echo "正在清理缓存目录: $CACHE_DIR"
    rm -rfv "$CACHE_DIR"/*
else
    echo "警告：未找到Matplotlib缓存目录"
fi

echo "安装完成！请重启Python环境使更改生效"
exit $SUCCESS