#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mermaid 图表渲染脚本 - Skill Creator 专用

使用 Kroki API 渲染 Mermaid 图表为 PNG 图片。

依赖: Python 3.6+
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path
import urllib.request
import base64
import zlib
import ssl

# 默认输出目录
DEFAULT_OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "mermaid-imgs"
)

# 创建禁用 SSL 验证的上下文（解决 macOS 证书问题）
SSL_CONTEXT = ssl._create_unverified_context()


def render_with_kroki(mermaid_code: str, output_path: str) -> bool:
    """
    使用 Kroki API 渲染 Mermaid 图表

    Kroki 使用 deflate + base64 编码，正确处理 UTF-8 中文字符。
    编码算法: UTF-8 bytes → zlib.compress(level 9) → URL-safe base64

    Args:
        mermaid_code: Mermaid 图表代码
        output_path: 输出 PNG 文件路径

    Returns:
        成功返回 True，失败返回 False
    """
    try:
        # Kroki 编码: UTF-8 → deflate (level 9) → URL-safe base64
        compressed = zlib.compress(mermaid_code.encode('utf-8'), 9)
        encoded = base64.urlsafe_b64encode(compressed).decode().rstrip('=')
        url = f"https://kroki.io/mermaid/png/{encoded}"

        # 创建 opener，禁用代理和 SSL 验证
        opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({}),
            urllib.request.HTTPSHandler(context=SSL_CONTEXT)
        )

        request = urllib.request.Request(url)
        request.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)')

        with opener.open(request, timeout=30) as response:
            with open(output_path, 'wb') as f:
                f.write(response.read())

        return True

    except Exception as e:
        print(f"Kroki 渲染失败: {e}", file=sys.stderr)
        return False


def generate_sequential_filename(output_dir: str, skill_desc: str) -> str:
    """
    生成带序号的文件名，自动递增避免冲突

    Args:
        output_dir: 输出目录
        skill_desc: Skill 的一句话描述

    Returns:
        完整的文件路径（带序号）
    """
    os.makedirs(output_dir, exist_ok=True)

    pattern = f"skill-{skill_desc}_*.png"
    existing_files = list(Path(output_dir).glob(pattern))

    max_seq = 0
    for file in existing_files:
        try:
            seq_str = file.stem.split('_')[-1]
            seq = int(seq_str)
            max_seq = max(max_seq, seq)
        except (ValueError, IndexError):
            continue

    new_seq = max_seq + 1
    filename = f"skill-{skill_desc}_{new_seq:03d}.png"

    return os.path.join(output_dir, filename)


def open_preview(file_path: str) -> None:
    """打开图片预览"""
    try:
        if sys.platform == "darwin":
            subprocess.run(["open", file_path])
        elif sys.platform.startswith("linux"):
            subprocess.run(["xdg-open", file_path])
        elif sys.platform == "win32":
            os.startfile(file_path)
    except Exception as e:
        print(f"无法打开预览: {e}", file=sys.stderr)


def render_mermaid(
    mermaid_code: str,
    output_path: str = None,
    auto_open: bool = True,
    output_dir: str = None,
    skill_desc: str = None
) -> str:
    """
    渲染 Mermaid 代码为 PNG 图片

    Args:
        mermaid_code: Mermaid 图表代码
        output_path: 输出文件路径
        auto_open: 是否自动打开预览
        output_dir: 输出目录
        skill_desc: Skill 的一句话描述

    Returns:
        生成的图片文件路径
    """
    if output_dir is None:
        output_dir = DEFAULT_OUTPUT_DIR

    os.makedirs(output_dir, exist_ok=True)

    if output_path is None:
        if not skill_desc:
            print("错误: 必须提供 --skill-desc 参数", file=sys.stderr)
            sys.exit(1)
        output_path = generate_sequential_filename(output_dir, skill_desc)

    output_path = os.path.expanduser(output_path)
    output_path = os.path.abspath(output_path)

    print("正在使用 Kroki API 渲染...", file=sys.stderr)

    if render_with_kroki(mermaid_code, output_path):
        print(f"✓ Mermaid 图表已生成: {output_path}")
        if auto_open:
            open_preview(output_path)
        return output_path

    print("渲染失败，请检查网络连接", file=sys.stderr)
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="渲染 Mermaid 图表为 PNG 图片 (使用 Kroki API)"
    )
    parser.add_argument("-c", "--code", help="Mermaid 代码（内联）")
    parser.add_argument("-f", "--file", help="包含 Mermaid 代码的文件路径")
    parser.add_argument("-o", "--output", help="输出文件路径")
    parser.add_argument("-d", "--output-dir", help="输出目录")
    parser.add_argument("--skill-desc", help="Skill 描述，用于生成文件名")
    parser.add_argument("--no-open", action="store_true", help="不自动打开预览")

    args = parser.parse_args()

    if args.code:
        mermaid_code = args.code
    elif args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            mermaid_code = f.read()
    else:
        mermaid_code = sys.stdin.read()

    if not mermaid_code.strip():
        print("错误: 未提供 Mermaid 代码", file=sys.stderr)
        sys.exit(1)

    render_mermaid(
        mermaid_code,
        output_path=args.output,
        auto_open=not args.no_open,
        output_dir=args.output_dir,
        skill_desc=args.skill_desc
    )


if __name__ == "__main__":
    main()
