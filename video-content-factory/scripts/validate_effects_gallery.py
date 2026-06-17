#!/usr/bin/env python3
"""验证特效库界面、示例特效与示例工程的一致性。

用法：
    python3 scripts/validate_effects_gallery.py
    python3 scripts/validate_effects_gallery.py --effects-dir assets/effects_library
    python3 scripts/validate_effects_gallery.py --project-dir examples/demo-project
    python3 scripts/validate_effects_gallery.py --browser-check

说明：
    --browser-check 会启动本地 HTTP 服务器，并用 Playwright 打开
    assets/effects_library/index.html，验证其能正确读取 registry.json
    并渲染特效卡片。若未安装 playwright，则给出安装提示。
"""

from __future__ import annotations

import argparse
import http.server
import json
import re
import socketserver
import sys
import threading
import time
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent

REQUIRED_REGISTRY_FIELDS = {
    "id",
    "name",
    "category",
    "desc",
    "anim",
    "params",
    "path",
    "accent",
    "since",
}
VALID_CATEGORIES = {
    "skeleton",
    "container",
    "beat",
    "transition",
    "util",
    "outro",
    "product",
}


def load_json(path: Path) -> Any:
    """读取 JSON 文件，失败时抛出 ValueError。"""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON 解析失败 {path}: {exc}") from exc


def load_registry(effects_dir: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """读取并校验 registry.json。

    返回：(effects 列表, 问题列表)
    """
    registry = effects_dir / "registry.json"
    issues: list[str] = []
    if not registry.exists():
        raise FileNotFoundError(f"缺少 registry.json: {registry}")

    data = load_json(registry)
    if not isinstance(data, dict):
        raise ValueError("registry.json 根节点必须是对象")

    effects = data.get("effects")
    if not isinstance(effects, list):
        raise ValueError("registry.json 必须包含 effects 数组")

    seen_ids: set[str] = set()
    for idx, record in enumerate(effects):
        if not isinstance(record, dict):
            issues.append(f"registry[{idx}]: 记录必须是对象")
            continue

        missing = REQUIRED_REGISTRY_FIELDS - set(record.keys())
        if missing:
            issues.append(
                f"{record.get('id', f'record[{idx}]')}: 缺少字段 {', '.join(sorted(missing))}"
            )

        effect_id = record.get("id")
        if not effect_id:
            issues.append(f"record[{idx}]: 缺少 id")
            continue

        if effect_id in seen_ids:
            issues.append(f"{effect_id}: id 重复")
        seen_ids.add(effect_id)

        category = record.get("category")
        if category and category not in VALID_CATEGORIES:
            issues.append(
                f"{effect_id}: 未知分类 '{category}'，有效值为 {', '.join(sorted(VALID_CATEGORIES))}"
            )

        path_val = record.get("path")
        if path_val and not str(path_val).startswith("snippets/"):
            issues.append(
                f"{effect_id}: path 建议以 snippets/ 开头，当前为 {path_val}"
            )

    return effects, issues


def validate_snippets(
    effects: list[dict[str, Any]], effects_dir: Path
) -> tuple[list[str], list[str]]:
    """校验 snippet 文件存在且包含必要 GSAP 代码。

    返回：(错误列表, 警告列表)
    """
    errors: list[str] = []
    warnings: list[str] = []
    snippets_dir = effects_dir / "snippets"

    for record in effects:
        effect_id = record.get("id")
        if not effect_id:
            continue

        snippet_path = snippets_dir / f"{effect_id}.html"
        if not snippet_path.exists():
            errors.append(f"{effect_id}: 缺少 snippet 文件 {snippet_path}")
            continue

        text = snippet_path.read_text(encoding="utf-8").lower()

        # 检查是否引入 GSAP
        if "gsap" not in text:
            errors.append(f"{effect_id}: snippet 中未引用 GSAP")

        # 检查是否包含时间轴或动画调用
        has_timeline = "gsap.timeline" in text or "gsap.to" in text or "gsap.from" in text
        if not has_timeline:
            errors.append(f"{effect_id}: snippet 中未找到 GSAP 动画调用")

        # 检查是否禁止无限循环
        if "repeat: -1" in text or "repeat:-1" in text:
            warnings.append(f"{effect_id}: snippet 使用了 repeat: -1 无限循环")

        # 检查是否有 PLAY / BEAT 时长变量（规范推荐）
        if "const play" not in text and "const beat" not in text:
            warnings.append(f"{effect_id}: snippet 建议声明 PLAY / BEAT 时长变量")

    return errors, warnings


def validate_previews(
    effects: list[dict[str, Any]], effects_dir: Path
) -> tuple[list[str], list[str]]:
    """校验 preview 文件存在且正确引用 snippet。"""
    errors: list[str] = []
    warnings: list[str] = []
    previews_dir = effects_dir / "previews"

    for record in effects:
        effect_id = record.get("id")
        if not effect_id:
            continue

        preview_path = previews_dir / f"{effect_id}.html"
        if not preview_path.exists():
            errors.append(f"{effect_id}: 缺少 preview 文件 {preview_path}")
            continue

        text = preview_path.read_text(encoding="utf-8")
        expected_src = f"../snippets/{effect_id}.html"
        if expected_src not in text:
            warnings.append(
                f"{effect_id}: preview 未按预期引用 {expected_src}"
            )

    return errors, warnings


def find_storyboard_effect_ids(project_dir: Path) -> set[str]:
    """从 STORYBOARD.md 中提取绑定的特效 ID。"""
    storyboard = project_dir / "STORYBOARD.md"
    if not storyboard.exists():
        raise FileNotFoundError(f"示例工程缺少 STORYBOARD.md: {storyboard}")

    text = storyboard.read_text(encoding="utf-8")
    ids: set[str] = set()

    # 匹配 ``stamp-hook``、stamp-hook（反引号内）或表格单元格中的 id
    for match in re.finditer(r"`([a-z0-9-]+)`", text):
        ids.add(match.group(1))

    # 同时匹配「已绑定特效模式」清单
    for match in re.finditer(r"`([a-z0-9-]+)`\s*（[^）]+）", text):
        ids.add(match.group(1))

    return ids


def validate_demo_project(project_dir: Path, effects: list[dict[str, Any]]) -> list[str]:
    """校验示例工程的完整性。"""
    issues: list[str] = []
    required_files = [
        "BRIEF.md",
        "SCRIPT.md",
        "STORYBOARD.md",
        "research.md",
        "topic-brief.md",
        "transcript.json",
    ]

    for name in required_files:
        if not (project_dir / name).exists():
            issues.append(f"示例工程缺少文件: {name}")

    registry_ids = {r.get("id") for r in effects if r.get("id")}
    try:
        storyboard_ids = find_storyboard_effect_ids(project_dir)
    except FileNotFoundError as exc:
        issues.append(str(exc))
        return issues

    for effect_id in sorted(storyboard_ids):
        if effect_id not in registry_ids:
            issues.append(
                f"STORYBOARD.md 引用的特效 ID '{effect_id}' 未在 registry.json 中注册"
            )

    return issues


class QuietHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """静默 HTTP 请求处理器。"""

    def __init__(self, *args: Any, directory: str | None = None, **kwargs: Any):
        super().__init__(*args, directory=directory, **kwargs)

    def log_message(self, format: str, *args: Any) -> None:
        pass


def start_local_server(effects_dir: Path, port: int = 0) -> tuple[socketserver.TCPServer, int]:
    """启动本地 HTTP 服务器并指定根目录，返回 (server, port)。"""
    handler = lambda *args, **kwargs: QuietHTTPRequestHandler(
        *args, directory=str(effects_dir), **kwargs
    )
    server = socketserver.TCPServer(("127.0.0.1", port), handler)
    server.allow_reuse_address = True
    port = server.server_address[1]

    def serve() -> None:
        server.serve_forever()

    threading.Thread(target=serve, daemon=True).start()
    # 等待服务器启动
    time.sleep(0.3)
    return server, port


def browser_check(effects_dir: Path) -> list[str]:
    """用 Playwright 打开 index.html 并验证卡片渲染。"""
    issues: list[str] = []

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        issues.append(
            "未安装 playwright，无法执行浏览器验证。"
            "可运行 `pip install playwright && playwright install chromium` 安装。"
        )
        return issues

    index_html = effects_dir / "index.html"
    if not index_html.exists():
        issues.append(f"缺少管理界面: {index_html}")
        return issues

    server, port = start_local_server(effects_dir)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900})

            page.on("pageerror", lambda exc: issues.append(f"页面 JS 错误: {exc}"))

            def _on_request_failed(req):
                failure = req.failure()
                error_text = failure.get("errorText", "unknown") if failure else "unknown"
                issues.append(f"请求失败: {req.url} -> {error_text}")

            page.on("requestfailed", _on_request_failed)

            url = f"http://127.0.0.1:{port}/index.html"
            page.goto(url, wait_until="networkidle", timeout=15000)

            # 等待卡片渲染
            try:
                page.wait_for_selector(".card", timeout=10000)
            except Exception as exc:
                issues.append(f"页面未在 10 秒内渲染出 .card 卡片: {exc}")
                browser.close()
                return issues

            cards = page.query_selector_all(".card")
            if not cards:
                issues.append("管理界面未渲染任何特效卡片")
            else:
                print(f"浏览器验证：共渲染 {len(cards)} 张卡片")

            # 验证每张卡片包含必要信息
            for card in cards:
                name_el = card.query_selector(".name")
                pid_el = card.query_selector(".pid")
                copy_btn = card.query_selector(".copy")
                if not name_el or not name_el.text_content().strip():
                    issues.append("卡片缺少名称")
                if not pid_el or not pid_el.text_content().strip():
                    issues.append("卡片缺少 id")
                if not copy_btn:
                    issues.append("卡片缺少复制按钮")

            # 验证分类导航按钮存在
            nav_buttons = page.query_selector_all("#nav button")
            if not nav_buttons:
                issues.append("分类导航按钮未渲染")
            else:
                print(f"浏览器验证：共渲染 {len(nav_buttons)} 个分类导航按钮")

            # 验证缓存信息已加载
            cache_el = page.query_selector("#cache")
            if cache_el:
                cache_text = cache_el.text_content() or ""
                print(f"浏览器验证：缓存信息 -> {cache_text.strip()}")

            browser.close()
    finally:
        server.shutdown()

    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="验证特效库界面、示例特效与示例工程的一致性。"
    )
    parser.add_argument(
        "--effects-dir",
        type=Path,
        default=SKILL_DIR / "assets" / "effects_library",
        help="特效库目录，默认: assets/effects_library",
    )
    parser.add_argument(
        "--project-dir",
        type=Path,
        default=SKILL_DIR / "examples" / "demo-project",
        help="示例工程目录，默认: examples/demo-project",
    )
    parser.add_argument(
        "--browser-check",
        action="store_true",
        help="启动本地 HTTP 服务器并用 Playwright 验证 index.html 渲染",
    )
    args = parser.parse_args(argv)

    effects_dir = args.effects_dir.resolve()
    project_dir = args.project_dir.resolve()

    exit_code = 0

    try:
        effects, registry_issues = load_registry(effects_dir)
        print(f"registry.json：共 {len(effects)} 个特效")
    except (FileNotFoundError, ValueError) as exc:
        print(f"[error] registry.json 读取失败: {exc}", file=sys.stderr)
        return 1

    for issue in registry_issues:
        print(f"[registry 问题] {issue}")
        exit_code = 1

    snippet_errors, snippet_warnings = validate_snippets(effects, effects_dir)
    for issue in snippet_errors:
        print(f"[snippet 错误] {issue}")
        exit_code = 1
    for issue in snippet_warnings:
        print(f"[snippet 警告] {issue}")

    preview_errors, preview_warnings = validate_previews(effects, effects_dir)
    for issue in preview_errors:
        print(f"[preview 错误] {issue}")
        exit_code = 1
    for issue in preview_warnings:
        print(f"[preview 警告] {issue}")

    demo_issues = validate_demo_project(project_dir, effects)
    for issue in demo_issues:
        print(f"[demo-project 问题] {issue}")
        exit_code = 1

    if not demo_issues:
        print("示例工程校验通过：STORYBOARD.md 中所有特效 ID 均存在于 registry.json")

    if args.browser_check:
        print("\n启动本地 HTTP 服务器进行浏览器渲染验证…")
        browser_issues = browser_check(effects_dir)
        for issue in browser_issues:
            print(f"[browser 问题] {issue}")
            exit_code = 1
        if not browser_issues:
            print("浏览器渲染验证通过")

    if exit_code == 0:
        print("\n所有校验通过。")
    else:
        print("\n存在校验问题，请查看上方输出。", file=sys.stderr)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
