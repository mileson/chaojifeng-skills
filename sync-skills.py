#!/usr/bin/env python3
"""
同步脚本：将本地 skills 复制到公共仓库结构

使用方法：
    python sync-skills.py              # 同步发布清单中的 skills
    python sync-skills.py --list       # 列出所有可发布的 skills
    python sync-skills.py --add <skill> [说明]  # 添加 skill 到发布清单
    python sync-skills.py --check <skill>       # 检查 skill 是否可以发布
"""

import os
import shutil
import argparse
import fnmatch
import yaml
from pathlib import Path
from datetime import datetime

# 源目录和目标目录
SOURCE_DIR = Path("/Users/chaojifeng/.claude/skills")
TARGET_DIR = Path(__file__).parent  # 仓库根目录
PUBLISH_LIST = Path(__file__).parent / "publish-list.yaml"

# Skills 分类映射
CATEGORIES = {
    "ios": ["ios-*", "xcode-*", "kmp-*"],
    "content": [
        "content-*", "markdown-*", "topic-*", "article-*",
        "jike-*", "xhs-content-creator", "xhs-note-*"
    ],
    "ai": ["ai-*", "agent-*"],
    "docs": ["docx", "pdf", "xlsx", "excalidraw-*"],
    "devtools": [
        "code-review", "security-review", "skill-*",
        "file-manual", "folder-manual", "test-case-*"
    ],
    "media": [
        "gif-*", "ffmpeg-*", "screenshot-*", "imagemagick-*",
        "ai-image-generator"
    ],
    "workflow": [
        "plan", "ralph", "autopilot", "ultrawork", "team",
        "task-handoff", "daily-review"
    ],
    "other": ["*"],
}

# 需要清理的文件/目录
CLEAN_PATTERNS = [
    "__pycache__",
    "*.pyc",
    ".DS_Store",
    "*.zip",
    "node_modules",
    "data/*.yaml",
    "data/*.json",
]


def load_publish_list():
    """加载发布清单"""
    if not PUBLISH_LIST.exists():
        return {"publish": {}, "exclude": {}, "exclude_patterns": [], "published": {}}

    with open(PUBLISH_LIST, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_publish_list(data):
    """保存发布清单"""
    with open(PUBLISH_LIST, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False)


def get_all_skills():
    """获取所有可同步的 skills"""
    skills = []
    for item in SOURCE_DIR.iterdir():
        if item.is_dir() and not item.name.startswith("."):
            skill_md = item / "SKILL.md"
            if skill_md.exists():
                skills.append(item.name)
    return sorted(skills)


def match_patterns(name, patterns):
    """检查名称是否匹配任一模式"""
    for pattern in patterns:
        if fnmatch.fnmatch(name, pattern):
            return True
    return False


def get_category(skill_name):
    """获取 skill 所属分类"""
    for category, patterns in CATEGORIES.items():
        if match_patterns(skill_name, patterns):
            return category
    return "other"


def is_excluded(skill_name, publish_list):
    """检查 skill 是否被排除"""
    # 检查显式排除
    if skill_name in publish_list.get("exclude", {}):
        return True, publish_list["exclude"][skill_name]

    # 检查模式排除
    for pattern in publish_list.get("exclude_patterns", []):
        if fnmatch.fnmatch(skill_name, pattern):
            return True, f"匹配排除模式: {pattern}"

    return False, None


def clean_directory(path):
    """清理目标目录中的临时文件"""
    for pattern in CLEAN_PATTERNS:
        for item in path.rglob(pattern):
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)


def copy_skill(skill_name, target_dir):
    """复制单个 skill 到目标目录"""
    source = SOURCE_DIR / skill_name
    target = target_dir / skill_name

    if target.exists():
        shutil.rmtree(target)

    shutil.copytree(source, target)
    clean_directory(target)
    return True


def add_to_publish_list(skill_name, description=""):
    """添加 skill 到发布清单"""
    publish_list = load_publish_list()

    # 检查 skill 是否存在
    skill_path = SOURCE_DIR / skill_name
    if not skill_path.exists() or not (skill_path / "SKILL.md").exists():
        print(f"  [错误] Skill '{skill_name}' 不存在或缺少 SKILL.md")
        return False

    # 检查是否被排除
    excluded, reason = is_excluded(skill_name, publish_list)
    if excluded:
        print(f"  [警告] 此 skill 在排除列表中: {reason}")
        print(f"  [提示] 如需发布，请先从 publish-list.yaml 的 exclude 中移除")
        return False

    # 添加到发布清单
    publish_list.setdefault("publish", {})[skill_name] = description or f"发布于 {datetime.now().strftime('%Y-%m-%d')}"
    save_publish_list(publish_list)

    print(f"  [OK] 已添加到发布清单: {skill_name}")
    if description:
        print(f"       说明: {description}")
    return True


def check_skill(skill_name):
    """检查 skill 是否可以发布"""
    publish_list = load_publish_list()

    # 检查是否存在
    skill_path = SOURCE_DIR / skill_name
    if not skill_path.exists():
        print(f"  [错误] Skill '{skill_name}' 不存在")
        return False

    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        print(f"  [错误] Skill '{skill_name}' 缺少 SKILL.md")
        return False

    print(f"  [OK] Skill 存在")

    # 检查是否被排除
    excluded, reason = is_excluded(skill_name, publish_list)
    if excluded:
        print(f"  [警告] 在排除列表中: {reason}")
        print(f"  [提示] 需要从 publish-list.yaml 的 exclude 中移除才能发布")
        return False

    # 检查是否在发布清单中
    if skill_name in publish_list.get("publish", {}):
        print(f"  [OK] 已在发布清单中")
    else:
        print(f"  [提示] 尚未添加到发布清单，使用 --add 添加")

    # 检查可能的敏感信息
    sensitive_files = [
        "credentials.json", ".secrets", "secret.yaml",
        "data/vault.yaml", "config/credentials.json"
    ]
    for sf in sensitive_files:
        if (skill_path / sf).exists():
            print(f"  [警告] 发现可能的敏感文件: {sf}")

    return True


def list_publishable():
    """列出所有可发布的 skills"""
    publish_list = load_publish_list()
    all_skills = get_all_skills()

    print(f"\n📋 可发布的 Skills ({len(all_skills)} 个)\n")
    print("=" * 60)

    # 分类显示
    by_category = {}
    for skill in all_skills:
        category = get_category(skill)
        by_category.setdefault(category, []).append(skill)

    for category in sorted(by_category.keys()):
        print(f"\n【{category.upper()}】")
        for skill in sorted(by_category[category]):
            # 检查状态
            excluded, reason = is_excluded(skill, publish_list)
            in_publish = skill in (publish_list.get("publish") or {})
            published = skill in (publish_list.get("published") or {})

            status = "   "
            if published:
                status = "[已发布]"
            elif in_publish:
                status = "[待发布]"
            elif excluded:
                status = "[已排除]"

            print(f"  {status:12} {skill}")
            if excluded:
                print(f"              └─ {reason}")

    print("\n" + "=" * 60)

    # 统计
    publish_count = len(publish_list.get("publish", {}))
    published_count = len(publish_list.get("published", {}))
    exclude_count = len(publish_list.get("exclude", {}))

    print(f"\n📊 统计:")
    print(f"  待发布: {publish_count}")
    print(f"  已发布: {published_count}")
    print(f"  已排除: {exclude_count}")


def main():
    parser = argparse.ArgumentParser(
        description="同步 skills 到公共仓库",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python sync-skills.py              # 同步发布清单中的 skills
  python sync-skills.py --list       # 列出所有可发布的 skills
  python sync-skills.py --add ios-mvvm-refactor "iOS MVVM 重构工具"
  python sync-skills.py --check ios-mvvm-refactor
        """
    )
    parser.add_argument("skills", nargs="*", help="要同步的 skills（直接指定时覆盖清单）")
    parser.add_argument("--list", action="store_true", help="列出所有可发布的 skills")
    parser.add_argument("--add", nargs="+", metavar=("SKILL", "DESCRIPTION"),
                        help="添加 skill 到发布清单")
    parser.add_argument("--check", metavar="SKILL", help="检查 skill 是否可以发布")
    args = parser.parse_args()

    if args.list:
        list_publishable()
        return

    if args.add:
        skill_name = args.add[0]
        description = " ".join(args.add[1:]) if len(args.add) > 1 else ""
        add_to_publish_list(skill_name, description)
        return

    if args.check:
        check_skill(args.check)
        return

    # 同步模式：只同步发布清单中的 skills
    publish_list = load_publish_list()
    to_publish = list(publish_list.get("publish", {}).keys())

    if not to_publish:
        print("发布清单为空")
        print("使用 --add <skill> [说明] 添加要发布的 skill")
        print("使用 --list 查看所有可发布的 skills")
        return

    print(f"开始同步 {len(to_publish)} 个 skills...\n")

    for skill_name in to_publish:
        source = SOURCE_DIR / skill_name
        if not source.exists():
            print(f"  [SKIP] {skill_name} 不存在")
            continue

        # 确定分类（仅用于显示）
        category = get_category(skill_name)

        # 直接复制到仓库根目录
        if copy_skill(skill_name, TARGET_DIR):
            print(f"  [OK] [{category}] {skill_name}")

            # 更新状态
            if publish_list.get("published") is None:
                publish_list["published"] = {}
            publish_list["published"][skill_name] = datetime.now().strftime("%Y-%m-%d")
            if publish_list.get("publish"):
                publish_list["publish"].pop(skill_name, None)

    # 保存更新后的清单
    save_publish_list(publish_list)

    print(f"\n完成！")
    print(f"  目标目录: {TARGET_DIR}")
    print(f"  已发布: {len(publish_list.get('published', {}))} 个")


if __name__ == "__main__":
    main()
