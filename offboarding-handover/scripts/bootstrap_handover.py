#!/usr/bin/env python3
"""
Bootstrap and build an offboarding handover package.

Capabilities:
- create scaffold directories and default config
- prompt first-run profile values and write them back to config
- scan a messy folder and classify files into default domains
- filter for handover relevance before staging
- stage included copies into the generated handover tree
- render a richer HTML site from the manifest
- export the staged output as a zip package
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
import shutil
import sys
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET


DEFAULT_CONFIG = {
    "version": "1",
    "profile": {
        "employee_name": "",
        "department": "",
        "role": "",
        "industry": "internet",
        "last_working_day": "",
        "handover_owner": "",
        "handover_coordinator": "",
        "successor": "",
    },
    "features": {
        "projects": True,
        "clients": False,
        "assets": True,
        "accounts": True,
        "legal": False,
        "relevance_filtering": True,
        "version_dedupe": True,
        "fold_generated_assets": True,
        "zip_export": True,
        "prune_empty_dirs": True,
    },
    "gates": {
        "source_dir_confirmed": False,
        "role_confirmed": False,
        "successor_view_confirmed": False,
        "deep_review_complete": False,
    },
    "relevance": {
        "mode": "balanced",
        "owner_aliases": [],
        "exclude_other_people": True,
        "exclude_public_reference": True,
        "dedupe_versions": True,
        "fold_generated_assets": True,
    },
    "taxonomy": {
        "presentation_modules": ["交接信息", "交接总览", "专项交接", "未完事项与状态"],
        "content_domains": [
            "工作事项",
            "关系人",
            "文档知识",
            "指标口径",
            "风险遗留",
            "资产权限",
            "合规结算",
            "交接状态",
        ],
    },
    "labels": {
        "scope": ["org", "role", "project", "legal", "design", "historical"],
        "doctype": [
            "docx",
            "pptx",
            "xlsx",
            "pdf",
            "kb",
            "minutes",
            "sop",
            "template",
            "contract",
            "asset",
            "link",
        ],
        "status": ["draft", "review", "final", "historical"],
        "sensitivity": ["public", "internal", "restricted", "confidential"],
    },
    "output": {
        "root_dir": "离职交接包",
        "site_dir": "离职交接包/site",
        "site_title": "离职交接入口",
        "site_style": "tech-portal",
        "zip_name": "离职交接包.zip",
    },
}


DEFAULT_ANSWERS = {
    "profile": {
        "employee_name": "",
        "owner_aliases": "",
        "last_working_day": "",
        "handover_owner": "",
        "handover_coordinator": "",
        "successor": "",
    },
    "routing": {
        "work_type": "",
        "has_client_projects": "",
        "has_inflight": "",
        "has_assets_or_sensitive": "",
    },
    "checks": {
        "work_wechat": "",
        "paper_notes": "",
        "otp_binding": "",
        "oral_rules": "",
        "reimbursement": "",
        "group_owner": "",
        "customer_transfer": "",
    },
    "policies": {
        "other_person_materials": "",
        "version_dedupe": "",
        "filename_normalization": "",
    },
    "updated_at": "",
}


OUTPUT_DIRS = [
    "离职交接包/00-说明与导航",
    "离职交接包/01-交接信息",
    "离职交接包/02-交接总览",
    "离职交接包/03-专项交接/10-工作事项",
    "离职交接包/03-专项交接/20-关系人与协作方",
    "离职交接包/03-专项交接/30-文档与知识资产",
    "离职交接包/03-专项交接/40-指标与口径",
    "离职交接包/03-专项交接/50-风险与遗留事项",
    "离职交接包/03-专项交接/60-资产与权限",
    "离职交接包/03-专项交接/70-合规与结算",
    "离职交接包/04-未完事项与状态",
    "离职交接包/site",
]


PROFILE_PROMPTS = [
    ("employee_name", "交接人姓名"),
    ("department", "所属部门"),
    ("role", "当前岗位"),
    ("industry", "行业模板", "internet"),
    ("last_working_day", "最后工作日"),
    ("handover_coordinator", "交接负责人/确认人"),
    ("successor", "接手人"),
]


MISSED_ITEM_ROWS = [
    {"index": 1, "item": "单位经办人/专办员身份", "content": "公积金、税务、社保、银行、报销系统经办身份", "archive_to": "合规结算"},
    {"index": 2, "item": "工作微信/企微/客户群/运营账号", "content": "工作微信号、企微外部联系人、客户群、公众号、小程序、视频号、社媒后台", "archive_to": "资产权限 / 合规结算"},
    {"index": 3, "item": "税务 UKey / 网银 U盾 / 支付凭证", "content": "税控 UKey、U盾、付款 token、开票权限", "archive_to": "合规结算"},
    {"index": 4, "item": "印章 / 营业执照 / 证照袋", "content": "公章、财务章、法人章、电子印章、营业执照原件/复印件", "archive_to": "合规结算 / 交接状态"},
    {"index": 5, "item": "涉密载体 / 纸质材料", "content": "U 盘、硬盘、纸质合同、报价单、会议材料、手写记录", "archive_to": "交接状态"},
    {"index": 6, "item": "公积金封存/转移后续责任", "content": "谁封存、谁转移、何时办、需要什么材料", "archive_to": "合规结算"},
    {"index": 7, "item": "手机号绑定与验证码链路", "content": "个人手机号、邮箱、OTP、短信验证码、验证器 App 绑定", "archive_to": "资产权限"},
    {"index": 8, "item": "个人工作台资产", "content": "本地脚本、书签、SQL、Postman、宏、模板、笔记库、个人云盘工作资料", "archive_to": "资产权限 / 文档知识"},
    {"index": 9, "item": "口头约定 / 非书面规则", "content": "聊天线程、会议口头结论、默认规则、客户暗约定", "archive_to": "文档知识 / 风险遗留"},
    {"index": 10, "item": "责任边界 / 未完事项", "content": "已完成、未完成、已提醒风险、后续责任人", "archive_to": "风险遗留"},
    {"index": 11, "item": "备用金 / 借款 / 未核销报销", "content": "差旅借款、备用金、垫付款、未核销报销单", "archive_to": "合规结算"},
    {"index": 12, "item": "发票开票权限 / 发票专用章", "content": "开票后台、税控设备、发票章、发票领用责任", "archive_to": "合规结算"},
    {"index": 13, "item": "纸质档案移交目录", "content": "档案清点表、卷宗目录、交接目录、涉密目录", "archive_to": "交接状态"},
    {"index": 14, "item": "涉密文件分类移交或销毁", "content": "密级文档、附件、纸质副本、载体销毁记录", "archive_to": "交接状态 / 合规结算"},
    {"index": 15, "item": "群主责任 / 内容监管责任", "content": "微信群/社群群主、运营人、审核责任人", "archive_to": "资产权限 / 合规结算"},
    {"index": 16, "item": "客户资源与聊天沉淀可用性", "content": "历史聊天、客户标签、支付记录、能否继续登录和查看", "archive_to": "关系人 / 资产权限"},
    {"index": 17, "item": "证照原件/复印件的实际保管", "content": "营业执照、资质证照、复印件、扫描件保管位置", "archive_to": "交接状态 / 合规结算"},
    {"index": 18, "item": "应收款 / 催收中的尾项", "content": "谁欠款、催收到哪一步、谁继续跟进", "archive_to": "合规结算 / 关系人"},
]


DOMAIN_TO_STAGE_DIR = {
    "工作事项": "03-专项交接/10-工作事项",
    "关系人": "03-专项交接/20-关系人与协作方",
    "文档知识": "03-专项交接/30-文档与知识资产",
    "指标口径": "03-专项交接/40-指标与口径",
    "风险遗留": "03-专项交接/50-风险与遗留事项",
    "资产权限": "03-专项交接/60-资产与权限",
    "合规结算": "03-专项交接/70-合规与结算",
    "交接状态": "04-未完事项与状态",
}


PRODUCT_DELIVERY_STAGE_DIR = {
    "工作事项": "03-专项交接/10-客户项目与需求",
    "文档知识": "03-专项交接/20-产品方案与知识库",
    "指标口径": "03-专项交接/30-数据报表与测算",
    "关系人": "03-专项交接/40-客户与协作关系",
    "风险遗留": "04-未完事项与状态/10-待跟进问题",
    "资产权限": "03-专项交接/60-账号权限与资产",
    "合规结算": "03-专项交接/70-合同对账与合规",
    "交接状态": "03-专项交接/80-历史归档参考",
}


DOMAIN_SHORT_LABELS = {
    "工作事项": "工作事项",
    "关系人": "协作关系",
    "文档知识": "知识文档",
    "指标口径": "指标口径",
    "风险遗留": "风险遗留",
    "资产权限": "资产权限",
    "合规结算": "合规结算",
    "交接状态": "交接状态",
}


DOCTYPE_LABELS = {
    "docx": "文档",
    "pptx": "演示材料",
    "xlsx": "表格",
    "pdf": "PDF",
    "kb": "知识库",
    "minutes": "纪要",
    "sop": "操作手册",
    "template": "模板",
    "contract": "合同",
    "asset": "资产",
    "link": "链接",
}


STATUS_DIR = "04-未完事项与状态"
INFLIGHT_SUMMARY_NAME = "00-进行中事项总表.md"
MISSED_ITEMS_NAME = "01-高遗漏检查清单.md"
CONCLUSION_NAME = "02-交接结论说明.md"
FILTER_REPORT_NAME = "02-筛选与排除报告.md"


EXT_TO_DOCTYPE = {
    ".doc": "docx",
    ".docx": "docx",
    ".ppt": "pptx",
    ".pptx": "pptx",
    ".xls": "xlsx",
    ".xlsx": "xlsx",
    ".csv": "xlsx",
    ".pdf": "pdf",
    ".md": "kb",
    ".txt": "minutes",
    ".rtf": "docx",
    ".drawio": "asset",
    ".vsdx": "asset",
    ".fig": "asset",
    ".sketch": "asset",
    ".png": "asset",
    ".jpg": "asset",
    ".jpeg": "asset",
    ".svg": "asset",
    ".zip": "asset",
    ".json": "asset",
    ".url": "link",
    ".webloc": "link",
}


KEYWORD_GROUPS = {
    "资产权限": [
        "账号", "权限", "资产", "设备", "电脑", "手机", "门禁", "vpn", "邮箱", "git",
        "github", "gitlab", "repo", "服务器", "数据库", "域名", "token", "ssh", "密钥",
        "key", "password", "密码", "网盘", "企业微信", "飞书",
    ],
    "合规结算": [
        "合同", "竞业", "保密", "薪资", "工资", "报销", "社保", "公积金", "离职", "证明",
        "法务", "发票", "回款", "结算", "盖章", "审批",
    ],
    "关系人": [
        "客户", "供应商", "合作方", "联系人", "通讯录", "stakeholder", "vendor",
        "partner", "client", "crm",
    ],
    "指标口径": [
        "kpi", "okr", "指标", "口径", "报表", "dashboard", "数据", "分析", "台账", "预算",
        "forecast", "roi",
    ],
    "风险遗留": [
        "风险", "遗留", "问题", "issue", "bug", "blocker", "阻塞", "待解决", "followup",
        "todo", "待办", "缺陷",
    ],
    "工作事项": [
        "项目", "计划", "里程碑", "roadmap", "需求池", "排期", "任务", "实施", "交付",
        "上线", "推进", "milestone", "project", "sprint",
    ],
    "文档知识": [
        "prd", "brd", "sop", "faq", "调研", "竞品", "培训", "说明书", "方案", "纪要",
        "流程", "原型", "知识库", "复盘", "手册", "蓝图",
    ],
    "交接状态": [
        "归档", "历史", "archive", "签收", "确认", "receipt",
    ],
}


SCOPE_KEYWORDS = {
    "legal": ["合同", "法务", "竞业", "保密", "证明", "社保", "公积金"],
    "design": ["设计", "原型", "figma", "sketch", "素材", "banner"],
    "project": ["项目", "里程碑", "milestone", "roadmap", "排期", "交付"],
    "org": ["制度", "模板", "流程", "规范", "培训", "知识库", "faq"],
    "historical": ["历史", "归档", "archive"],
}


STATUS_KEYWORDS = {
    "final": ["最终", "final", "正式版", "定稿", "发布版"],
    "review": ["评审", "review", "待确认"],
    "draft": ["草稿", "draft", "v0", "初稿"],
    "historical": ["归档", "archive", "历史"],
}


SENSITIVITY_KEYWORDS = {
    "confidential": ["薪资", "工资", "合同", "竞业", "保密", "身份证", "手机号", "邮箱账号"],
    "restricted": ["客户", "供应商", "回款", "发票", "服务器", "数据库", "密钥"],
    "internal": ["内部", "培训", "纪要", "方案", "需求"],
}


MEANINGFUL_DOCTYPES = {"docx", "pptx", "xlsx", "pdf", "kb", "minutes", "sop", "contract", "link"}
ARCHIVE_SUFFIXES = {".zip", ".rar", ".7z"}
GENERATED_ASSET_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".js",
    ".css",
    ".html",
    ".htm",
    ".cur",
    ".eot",
    ".ttf",
    ".woff",
    ".woff2",
}
PROTOTYPE_SOURCE_SUFFIXES = {".rp", ".rpteam", ".fig", ".sketch", ".drawio", ".vsdx", ".xmind"}
GENERATED_ASSET_PATH_KEYWORDS = [
    "demo",
    "images",
    "resources",
    "files",
    "原型",
    "ui设计",
    "应用图标",
    "axure",
    "static",
]
PUBLIC_REFERENCE_KEYWORDS = [
    "公共",
    "通用",
    "模板",
    "制度",
    "规范",
    "参考案例",
    "参考",
    "案例",
    "岗位说明书",
    "管理办法",
    "通知",
]
HANDOVER_VALUE_KEYWORDS = [
    "客户",
    "项目",
    "汇报",
    "培训",
    "沟通记录",
    "需求",
    "方案",
    "蓝图",
    "操作手册",
    "说明书",
    "计划",
    "推进",
    "上线",
    "会议",
    "复盘",
    "风险",
    "遗留",
    "待办",
    "权限",
    "账号",
    "合同",
    "回款",
    "发票",
    "指标",
    "报表",
]
OTHER_PERSONAL_MARKERS = [
    "个人工作述职",
    "个人述职",
    "个人总结",
    "述职",
    "岗位说明书",
    "人才盘点",
]
PERSON_TOKEN_STOPWORDS = {
    "大北农",
    "农信",
    "数智",
    "客户",
    "项目",
    "产品",
    "产品部",
    "负责人",
    "供应链",
    "销售",
    "业务",
    "系统",
    "平台",
    "模板",
    "制度",
    "规范",
    "方案",
    "需求",
    "汇报",
    "培训",
    "岗位",
    "说明书",
    "团队",
    "公司",
    "部门",
    "客户部",
}


SKIP_DIR_NAMES = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    "__pycache__",
    ".idea",
    ".vscode",
    ".offboarding-handover",
}


PREVIEWABLE_TEXT_SUFFIXES = {".md", ".txt"}
PREVIEWABLE_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}
PREVIEWABLE_OFFICE_SUFFIXES = {".docx", ".pptx", ".xlsx"}
PREVIEWABLE_TABLE_SUFFIXES = {".csv"}


def deep_copy(data: dict[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(data))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def write_text(path: Path, content: str) -> None:
    path.write_text(content.rstrip() + "\n")


def slugify(value: str) -> str:
    normalized = re.sub(r"[^\w\u4e00-\u9fff.-]+", "-", value, flags=re.UNICODE)
    normalized = re.sub(r"-{2,}", "-", normalized).strip("-")
    return normalized or "file"


def clean_text_key(value: str) -> str:
    return re.sub(r"[\s_\-—–·.（）()\[\]【】:：/\\]+", "", value).lower()


def handover_coordinator_value(config: dict[str, Any]) -> str:
    profile = config.get("profile", {})
    return str(profile.get("handover_coordinator") or profile.get("handover_owner") or "").strip()


def split_alias_text(value: str) -> list[str]:
    return [
        item.strip()
        for item in re.split(r"[,，、;/；\s]+", value)
        if item.strip()
    ]


def timestamp_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_config(target: Path) -> tuple[dict[str, Any], Path]:
    hidden_dir = target / ".offboarding-handover"
    hidden_dir.mkdir(exist_ok=True)
    hidden_config = hidden_dir / "offboarding.config.json"
    legacy_root_config = target / "offboarding.config.json"

    if hidden_config.exists():
        return merge_config_defaults(json.loads(hidden_config.read_text())), hidden_config
    if legacy_root_config.exists():
        data = merge_config_defaults(json.loads(legacy_root_config.read_text()))
        write_json(hidden_config, data)
        try:
            legacy_root_config.unlink()
        except OSError:
            pass
        return data, hidden_config
    return deep_copy(DEFAULT_CONFIG), hidden_config


def merge_config_defaults(config: dict[str, Any]) -> dict[str, Any]:
    merged = deep_copy(DEFAULT_CONFIG)
    for key, value in config.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key].update(value)
        else:
            merged[key] = value
    return merged


def merge_answers_defaults(answers: dict[str, Any]) -> dict[str, Any]:
    merged = deep_copy(DEFAULT_ANSWERS)
    for key, value in answers.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key].update(value)
        else:
            merged[key] = value
    return merged


def load_answers(target: Path) -> tuple[dict[str, Any], Path]:
    hidden_dir = target / ".offboarding-handover"
    hidden_dir.mkdir(exist_ok=True)
    answers_path = hidden_dir / "handover.answers.json"
    if answers_path.exists():
        return merge_answers_defaults(json.loads(answers_path.read_text())), answers_path
    return deep_copy(DEFAULT_ANSWERS), answers_path


def load_manifest(target: Path) -> tuple[dict[str, Any] | None, Path]:
    manifest_path = target / ".offboarding-handover" / "handover.manifest.json"
    if manifest_path.exists():
        return json.loads(manifest_path.read_text()), manifest_path
    return None, manifest_path


def ensure_output_tree(target: Path, output_root: str) -> None:
    target.mkdir(parents=True, exist_ok=True)
    for relative in OUTPUT_DIRS:
        adjusted = relative.replace("离职交接包", output_root, 1)
        (target / adjusted).mkdir(parents=True, exist_ok=True)


def prompt_profile(profile: dict[str, Any], interactive: bool) -> tuple[dict[str, Any], list[str]]:
    assumptions: list[str] = []
    if not interactive or not sys.stdin.isatty():
        for key, _, *default in PROFILE_PROMPTS:
            if not profile.get(key):
                if default:
                    profile[key] = default[0]
                    assumptions.append(f"{key} 默认设置为 {default[0]}")
        return profile, assumptions

    for key, label, *default in PROFILE_PROMPTS:
        current = profile.get(key, "")
        seed = current or (default[0] if default else "")
        prompt = f"{label}"
        if seed:
            prompt += f" [{seed}]"
        prompt += "："
        entered = input(prompt).strip()
        if entered:
            profile[key] = entered
        elif seed:
            profile[key] = seed
            if not current:
                assumptions.append(f"{key} 默认设置为 {seed}")
    role = profile.get("role", "").strip()
    if role:
        entered = input(f"确认按“{role}”对应的岗位视角整理目录吗？[是]：").strip()
        if entered and entered not in {"是", "确认", "对", "yes", "y", "Y", "YES"}:
            profile["role"] = entered
            assumptions.append(f"岗位视角由用户改为 {entered}")
    return profile, assumptions


def merge_answers_into_config(config: dict[str, Any], answers: dict[str, Any]) -> None:
    for key in ("employee_name", "last_working_day", "handover_owner", "handover_coordinator", "successor"):
        value = answers.get("profile", {}).get(key)
        if value:
            config["profile"][key] = value
    alias_text = str(answers.get("profile", {}).get("owner_aliases") or "").strip()
    if alias_text:
        configured = config.setdefault("relevance", {}).setdefault("owner_aliases", [])
        aliases = configured if isinstance(configured, list) else []
        for alias in split_alias_text(alias_text):
            if alias not in aliases:
                aliases.append(alias)
        config["relevance"]["owner_aliases"] = aliases


def prompt_handover_answers(
    answers: dict[str, Any],
    interactive: bool,
    refresh_mode: bool = False,
) -> tuple[dict[str, Any], list[str]]:
    assumptions: list[str] = []
    if not interactive or not sys.stdin.isatty():
        return answers, assumptions

    routing_questions = [
        ("work_type", "这批资料最接近你哪类工作", "产品/需求/方案"),
        ("has_client_projects", "这里面是否包含客户/项目资料", "内部和客户/项目资料都有"),
        ("has_inflight", "有没有还在推进、还没收尾的事", "还不确定"),
        ("has_assets_or_sensitive", "有没有账号、权限、设备或敏感资料需要交接", "还不确定"),
    ]
    if not refresh_mode:
        for key, label, seed in routing_questions:
            current = answers["routing"].get(key, "")
            prompt = f"{label}"
            if current or seed:
                prompt += f" [{current or seed}]"
            prompt += "："
            entered = input(prompt).strip()
            if entered:
                answers["routing"][key] = entered
            elif not current and seed:
                answers["routing"][key] = seed
                assumptions.append(f"{key} 默认设置为 {seed}")

    answer_questions = [
        ("employee_name", "这批资料的交接人是谁", "", "profile"),
        ("owner_aliases", "文件里常见的交接人简称/英文名/花名", "", "profile"),
        ("last_working_day", "最后工作日", "", "profile"),
        ("handover_coordinator", "交接负责人或确认人", "", "profile"),
        ("successor", "接手人", "", "profile"),
        ("work_wechat", "工作微信/企微/客户群/运营账号情况", "", "checks"),
        ("paper_notes", "是否有纸质材料或手写笔记需要交接", "", "checks"),
        ("otp_binding", "是否有手机号绑定或验证码链路", "", "checks"),
        ("oral_rules", "是否存在口头约定或非书面规则", "", "checks"),
        ("reimbursement", "是否有备用金/借款/未核销报销", "", "checks"),
        ("group_owner", "是否有群主责任或内容监管责任", "", "checks"),
        ("customer_transfer", "客户关系或对接人是否已明确移交", "", "checks"),
    ]
    for key, label, seed, group in answer_questions:
        current = answers[group].get(key, "")
        if refresh_mode and current:
            continue
        prompt = f"{label}"
        if current or seed:
            prompt += f" [{current or seed}]"
        prompt += "："
        entered = input(prompt).strip()
        if entered:
            answers[group][key] = entered
        elif not current and seed:
            answers[group][key] = seed
            assumptions.append(f"{key} 默认设置为 {seed}")

    policy_questions = [
        (
            "other_person_materials",
            "其他同事个人材料是否默认不放进核心交接包",
            "是，个人材料排除，项目共用材料先待确认",
        ),
        (
            "version_dedupe",
            "同一文档多个版本是否默认只保留最终版/最新版本",
            "是，旧版本写入排除说明",
        ),
        (
            "filename_normalization",
            "复制进交接包的文件名是否按标准格式重命名",
            "是，并保留原路径映射",
        ),
    ]
    for key, label, seed in policy_questions:
        current = answers.setdefault("policies", {}).get(key, "")
        if refresh_mode and current:
            continue
        prompt = f"{label}"
        if current or seed:
            prompt += f" [{current or seed}]"
        prompt += "："
        entered = input(prompt).strip()
        if entered:
            answers["policies"][key] = entered
        elif not current and seed:
            answers["policies"][key] = seed
            assumptions.append(f"{key} 默认设置为 {seed}")

    answers["updated_at"] = timestamp_now()
    return answers, assumptions


def status_from_answer(value: str) -> str:
    text = (value or "").strip().lower()
    if not text:
        return "待补充"
    if any(token in text for token in ["无", "不涉及", "无需", "没有"]):
        return "无需交接"
    if any(token in text for token in ["已", "完成", "移交", "交接", "确认"]):
        return "已交接"
    return "已补充"


def make_overview_markdown(config: dict[str, Any], stats: dict[str, Any] | None = None) -> str:
    role = config["profile"]["role"] or "待补充"
    dept = config["profile"]["department"] or "待补充"
    lines = [
        "# 交接总览",
        "",
        "## 基本信息",
        "",
        f"- 交接人：{config['profile'].get('employee_name') or '待补充'}",
        f"- 部门：{dept}",
        f"- 岗位：{role}",
        f"- 行业模板：{config['profile']['industry']}",
        f"- 最后工作日：{config['profile'].get('last_working_day') or '待补充'}",
        f"- 交接负责人/确认人：{handover_coordinator_value(config) or '待补充'}",
        f"- 接手人：{config['profile'].get('successor') or '待补充'}",
        "",
        "## 建议阅读顺序",
        "",
        "1. `01-交接信息`",
        "2. `02-交接总览`",
        "3. `03-专项交接`",
        "4. `04-未完事项与状态`",
        "",
        "## 说明",
        "",
        "- 当前输出优先采用分阶段复制，不会直接移动原始文件。",
        "- 请先核对专项交接下的分类结果，再决定是否做原地整理或打包交付。",
    ]
    if stats:
        lines.extend(
            [
                "",
                "## 本次扫描",
                "",
                f"- 扫描文件数：{stats['scanned_files']}",
                f"- 已纳入交接包：{stats['classified_files']}",
                f"- 需要确认文件数：{stats.get('review_files', 0)}",
                f"- 未纳入文件数：{stats.get('excluded_files', 0)}",
            ]
        )
    return "\n".join(lines)


def make_handover_info_markdown(config: dict[str, Any], answers: dict[str, Any], assumptions: list[str]) -> str:
    profile = config["profile"]
    routing = answers.get("routing", {})
    lines = [
        "# 交接信息",
        "",
        "## 基本信息",
        "",
        f"- 交接人：{profile.get('employee_name') or '待补充'}",
        f"- 部门：{profile.get('department') or '待补充'}",
        f"- 岗位：{profile.get('role') or '待补充'}",
        f"- 行业：{profile.get('industry') or '待补充'}",
        f"- 最后工作日：{profile.get('last_working_day') or '待补充'}",
        f"- 交接负责人/确认人：{handover_coordinator_value(config) or '待补充'}",
        f"- 接手人：{profile.get('successor') or '待补充'}",
        "",
        "## 首轮判断",
        "",
        f"- 这批资料最接近的工作类型：{routing.get('work_type') or '待补充'}",
        f"- 是否包含客户/项目资料：{routing.get('has_client_projects') or '待补充'}",
        f"- 是否存在未完事项：{routing.get('has_inflight') or '待补充'}",
        f"- 是否包含账号/权限/敏感资料：{routing.get('has_assets_or_sensitive') or '待补充'}",
        "",
        "## 当前说明",
        "",
        "- 这一部分用于说明“这是谁的交接、交给谁、主要是什么类型的材料”。",
        "- 如果后续用户补充了接手人、最后工作日或职责边界，这里应同步刷新。",
    ]
    if assumptions:
        lines.extend(["", "## 当前推断与假设", ""])
        lines.extend([f"- {item}" for item in assumptions])
    return "\n".join(lines)


def make_summary_markdown(config: dict[str, Any], manifest: dict[str, Any]) -> str:
    stats = manifest["stats"]
    modules = manifest["modules"]
    lines = [
        "# 交接总览",
        "",
        "## 模块概览",
        "",
        "| 模块 | 文件数 | 示例 |",
        "| --- | --- | --- |",
    ]
    for module in modules:
        sample = "；".join(module["sample_files"][:3]) if module["sample_files"] else "暂无"
        lines.append(f"| {module['name']} | {module['count']} | {sample} |")
    lines.extend(
        [
            "",
            "## 统计",
            "",
            f"- 扫描文件数：{stats['scanned_files']}",
            f"- 已纳入交接包：{stats['classified_files']}",
            f"- 需要确认文件数：{stats.get('review_files', 0)}",
            f"- 未纳入文件数：{stats.get('excluded_files', 0)}",
            f"- 纳入文件总体积：{bytes_to_human(stats['total_bytes'])}",
            "",
            "## 高风险提醒",
            "",
            f"- 高风险条目数：{len(manifest.get('high_risk_items', []))}",
            "- 建议先核对资产权限、合规结算、客户资料与历史遗留事项。",
        ]
    )
    return "\n".join(lines)


def make_filter_report_markdown(config: dict[str, Any], manifest: dict[str, Any]) -> str:
    stats = manifest["stats"]
    retention = manifest.get("retention_stats", {})
    review_items = manifest.get("review_items", [])
    excluded_items = manifest.get("excluded_items", [])
    lines = [
        "# 筛选与排除报告",
        "",
        "## 筛选结论",
        "",
        f"- 本次扫描文件数：{stats.get('scanned_files', 0)}",
        f"- 已纳入交接包：{retention.get('include', 0)}",
        f"- 需要确认：{retention.get('review', 0)}",
        f"- 未纳入：{retention.get('exclude', 0)}",
        "",
        "## 筛选原则",
        "",
        "- 交接人姓名是强信号，但不是纳入门槛。",
        "- 没有姓名但属于岗位、项目、客户、风险或后续推进的资料，仍可纳入。",
        "- 明确属于他人、公司公共资料、旧版本或生成资产的文件，默认不复制进交接包。",
        "- 不确定是否需要接手的文件，放入“需要确认”。",
    ]

    review_reason_counts = manifest.get("review_reason_counts", {})
    if review_reason_counts:
        lines.extend(["", "## 需要确认的原因", "", "| 原因 | 数量 |", "| --- | --- |"])
        for reason, count in review_reason_counts.items():
            lines.append(f"| {reason} | {count} |")

    excluded_reason_counts = manifest.get("excluded_reason_counts", {})
    if excluded_reason_counts:
        lines.extend(["", "## 未纳入的原因", "", "| 原因 | 数量 |", "| --- | --- |"])
        for reason, count in excluded_reason_counts.items():
            lines.append(f"| {reason} | {count} |")

    lines.extend(["", "## 需要确认的文件示例", "", "| 文件 | 原因 |", "| --- | --- |"])
    if review_items:
        for item in review_items[:80]:
            reasons = "、".join(item.get("retain_reasons", []))
            lines.append(f"| `{item['relative_path']}` | {reasons or '待确认'} |")
    else:
        lines.append("| 暂无 |  |")

    lines.extend(["", "## 未纳入的文件示例", "", "| 文件 | 原因 | 保留版本 |", "| --- | --- | --- |"])
    if excluded_items:
        for item in excluded_items[:120]:
            reasons = "、".join(item.get("retain_reasons", []))
            kept = item.get("superseded_by", "")
            lines.append(f"| `{item['relative_path']}` | {reasons or '未纳入'} | `{kept}` |")
    else:
        lines.append("| 暂无 |  |  |")

    filename_mapping = manifest.get("filename_mapping", [])
    lines.extend(["", "## 文件名映射", "", "| 原始文件 | 交接包文件名 | 说明 |", "| --- | --- | --- |"])
    if filename_mapping:
        for item in filename_mapping[:160]:
            original = item.get("original_path") or item.get("original_name") or ""
            staged = item.get("staged_path") or item.get("staged_name") or ""
            reason = item.get("rename_reason", "")
            lines.append(f"| `{original}` | `{staged}` | {reason or '保持原名'} |")
    else:
        lines.append("| 暂无 |  |  |")

    return "\n".join(lines)


def infer_inflight_items(records: list[dict[str, Any]]) -> list[dict[str, str]]:
    keywords = [
        "进行中", "待办", "待处理", "待跟进", "跟进", "issue", "todo", "backlog",
        "roadmap", "risk", "风险", "遗留", "未完", "排期", "计划", "推进",
    ]
    items: list[dict[str, str]] = []
    for record in records:
        haystack = " ".join(
            [
                record.get("relative_path", ""),
                record.get("staged_path", ""),
                record.get("domain", ""),
                " ".join(record.get("reasons", [])),
            ]
        ).lower()
        if any(keyword.lower() in haystack for keyword in keywords):
            items.append(
                {
                    "item": Path(record["relative_path"]).stem,
                    "module": record["domain"],
                    "status": "待确认",
                    "next_step": "请补充下一步动作",
                    "owner": "待指定",
                    "risk": "请补充风险提醒",
                    "link": record.get("staged_path") or record["relative_path"],
                }
            )
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in items:
        if item["link"] in seen:
            continue
        seen.add(item["link"])
        result.append(item)
    return result[:20]


def make_inflight_summary_markdown(config: dict[str, Any], records: list[dict[str, Any]]) -> str:
    profile = config["profile"]
    rows = infer_inflight_items(records)
    lines = [
        "# 进行中事项总表",
        "",
        "## 使用说明",
        "",
        "- 这里只放仍需要接手人继续推进的事项，保证唯一入口。",
        "- 详细资料放在 `03-专项交接`，这里不要重复写大段内容，只保留摘要和链接。",
        "- 每一项至少补齐：当前状态、下一步、责任人、风险提醒。",
        "",
        "## 基本信息",
        "",
        f"- 交接人：{profile.get('employee_name') or '待补充'}",
        f"- 接手人：{profile.get('successor') or '待补充'}",
        f"- 最后工作日：{profile.get('last_working_day') or '待补充'}",
        "",
        "## 总表",
        "",
        "| 事项 | 所属模块 | 当前状态 | 下一步 | 接手人/责任人 | 风险提醒 | 资料链接 |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    if rows:
        for row in rows:
            lines.append(
                f"| {row['item']} | {row['module']} | {row['status']} | {row['next_step']} | {row['owner']} | {row['risk']} | `{row['link']}` |"
            )
    else:
        lines.append("| 待补充 | 待补充 | 待确认 | 请补充下一步动作 | 待指定 | 请补充风险提醒 | 待补充 |")
    return "\n".join(lines)


def make_missed_items_markdown(config: dict[str, Any], answers: dict[str, Any]) -> str:
    profile = config["profile"]
    header = [
        "# 高遗漏检查清单",
        "",
        "## 基本信息",
        "",
        f"- 交接人：{profile.get('employee_name') or '待补充'}",
        f"- 部门：{profile.get('department') or '待补充'}",
        f"- 岗位：{profile.get('role') or '待补充'}",
        f"- 交接负责人/确认人：{handover_coordinator_value(config) or '待补充'}",
        f"- 接手人：{profile.get('successor') or '待补充'}",
        "",
        "## 使用说明",
        "",
        "请逐项标记为 `已确认无需交接`、`已交接` 或 `待补充`。",
        "",
        "## 检查表",
        "",
        "| 序号 | 检查项 | 典型内容 | 建议放置位置 | 状态 | 当前持有人/责任人 | 接手人 | 补充说明 |",
        "|---|---|---|---|---|---|---|---|",
    ]
    rows = [
        f"| {row['index']} | {row['item']} | {row['content']} | {row['archive_to']} | 待补充 |  |  |  |"
        for row in MISSED_ITEM_ROWS
    ]
    overrides = {
        "工作微信/企微/客户群/运营账号": answers["checks"].get("work_wechat", ""),
        "涉密载体 / 纸质材料": answers["checks"].get("paper_notes", ""),
        "手机号绑定与验证码链路": answers["checks"].get("otp_binding", ""),
        "口头约定 / 非书面规则": answers["checks"].get("oral_rules", ""),
        "备用金 / 借款 / 未核销报销": answers["checks"].get("reimbursement", ""),
        "群主责任 / 内容监管责任": answers["checks"].get("group_owner", ""),
        "客户资源与聊天沉淀可用性": answers["checks"].get("customer_transfer", ""),
    }
    rows = []
    for row in MISSED_ITEM_ROWS:
        note = overrides.get(row["item"], "")
        rows.append(
            f"| {row['index']} | {row['item']} | {row['content']} | {row['archive_to']} | {status_from_answer(note)} |  |  | {note or '待补充'} |"
        )
    footer = [
        "",
        "## 备注",
        "",
        "- 如果某项已经在正式交接文档中体现，也建议在此处标记，避免遗漏。",
        "- 若涉及纸质材料、印章、UKey、涉密载体，建议补一条线下交接备注。",
    ]
    return "\n".join(header + rows + footer)


def make_conclusion_markdown(config: dict[str, Any], manifest: dict[str, Any], records: list[dict[str, Any]], answers: dict[str, Any]) -> str:
    profile = config["profile"]
    stats = manifest["stats"]
    inflight_count = len(infer_inflight_items(records))
    pending_checks = sum(1 for value in answers.get("checks", {}).values() if not value.strip())
    lines = [
        "# 交接结论说明",
        "",
        "## 一句话结论",
        "",
        "本次交接材料已按模块整理，接手人优先从 `00-交接总览.md` 和 `04-未完事项与状态/00-进行中事项总表.md` 开始阅读。",
        "",
        "## 本次交接范围",
        "",
        f"- 交接人：{profile.get('employee_name') or '待补充'}",
        f"- 岗位：{profile.get('role') or '待补充'}",
        f"- 部门：{profile.get('department') or '待补充'}",
        f"- 最后工作日：{profile.get('last_working_day') or '待补充'}",
        f"- 本次扫描文件数：{stats['scanned_files']}",
        f"- 已归入交接包文件数：{stats['classified_files']}",
        f"- 需要确认文件数：{stats.get('review_files', 0)}",
        f"- 未纳入文件数：{stats.get('excluded_files', 0)}",
        f"- 识别出的进行中事项：{inflight_count}",
        f"- 仍待补充的高遗漏检查项：{pending_checks}",
        "",
        "## 需要接手人特别注意",
        "",
        "1. 先看 `00-进行中事项总表.md`，确认哪些事还在推进中。",
        "2. 再按模块查看 `03-专项交接` 中的对应资料。",
        "3. 高风险条目请对照 `01-高遗漏检查清单.md` 再核一遍。",
        "",
        "## 离职人已完成的责任",
        "",
        "- 尽量把资料交代清楚。",
        "- 尽量把现有文件交出去。",
        "- 尽量把未完事项和风险说透。",
        "",
        "## 仍需补充或线下完成",
        "",
        "- 如有口头约定、系统权限回收、实物归还，请在线下按公司流程补完。",
        "- 如有无法在文件中完整表达的背景，请在总表对应事项里补一条摘要。",
    ]
    return "\n".join(lines)


def infer_doctype(path: Path) -> str:
    return EXT_TO_DOCTYPE.get(path.suffix.lower(), "asset")


def infer_scope(text: str) -> str:
    lowered = text.lower()
    for scope, keywords in SCOPE_KEYWORDS.items():
        if any(keyword.lower() in lowered for keyword in keywords):
            return scope
    return "role"


def infer_status(text: str) -> str:
    lowered = text.lower()
    for status, keywords in STATUS_KEYWORDS.items():
        if any(keyword.lower() in lowered for keyword in keywords):
            return status
    return "final" if "说明书" in text or "手册" in text else "draft"


def infer_sensitivity(text: str) -> str:
    lowered = text.lower()
    for level, keywords in SENSITIVITY_KEYWORDS.items():
        if any(keyword.lower() in lowered for keyword in keywords):
            return level
    return "internal"


def infer_domain(text: str, doctype: str) -> tuple[str, list[str]]:
    lowered = text.lower()
    reasons: list[str] = []
    scores: Counter[str] = Counter()
    for domain, keywords in KEYWORD_GROUPS.items():
        for keyword in keywords:
            if keyword.lower() in lowered:
                scores[domain] += 1
                reasons.append(f"keyword:{keyword}")

    if doctype in {"xlsx"}:
        scores["指标口径"] += 1
    if doctype in {"contract"}:
        scores["合规结算"] += 2
    if doctype in {"kb", "docx", "pptx"}:
        scores["文档知识"] += 1
    if doctype in {"link"}:
        scores["文档知识"] += 1

    if not scores:
        return "文档知识", ["default:doctype-fallback"]
    return scores.most_common(1)[0][0], reasons


def is_product_delivery_role(config: dict[str, Any]) -> bool:
    role_text = " ".join(
        [
            str(config.get("profile", {}).get("role") or ""),
            str(config.get("profile", {}).get("department") or ""),
            str(config.get("profile", {}).get("industry") or ""),
        ]
    )
    return any(token in role_text for token in ["产品", "需求", "项目", "交付", "实施", "客户", "售前"])


def stage_dir_for_record(config: dict[str, Any], record: dict[str, Any]) -> str:
    if is_product_delivery_role(config):
        return PRODUCT_DELIVERY_STAGE_DIR.get(
            record["domain"],
            "03-专项交接/20-产品方案与知识库",
        )
    return DOMAIN_TO_STAGE_DIR.get(record["domain"], "03-专项交接/30-文档与知识资产")


def owner_aliases_from_config(config: dict[str, Any]) -> list[str]:
    aliases: list[str] = []
    configured = config.get("relevance", {}).get("owner_aliases", [])
    if isinstance(configured, list):
        aliases.extend(str(item).strip() for item in configured if str(item).strip())
    employee_name = str(config.get("profile", {}).get("employee_name") or "").strip()
    if employee_name:
        aliases.append(employee_name)
        compact = clean_text_key(employee_name)
        if compact and compact != employee_name:
            aliases.append(compact)
        if len(employee_name) >= 3 and re.fullmatch(r"[\u4e00-\u9fff]+", employee_name):
            aliases.append(employee_name[1:])
    result: list[str] = []
    seen: set[str] = set()
    for alias in aliases:
        cleaned = alias.strip()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            result.append(cleaned)
    return result


def contains_owner_alias(text: str, aliases: list[str]) -> bool:
    compact = clean_text_key(text)
    lowered = text.lower()
    for alias in aliases:
        if alias.lower() in lowered or clean_text_key(alias) in compact:
            return True
    return False


def looks_like_generated_asset(path: Path, relative_text: str) -> bool:
    lowered = relative_text.lower()
    suffix = path.suffix.lower()
    if suffix not in GENERATED_ASSET_SUFFIXES:
        return False
    return any(keyword.lower() in lowered for keyword in GENERATED_ASSET_PATH_KEYWORDS)


def looks_like_public_reference(text: str) -> bool:
    lowered = text.lower()
    return any(keyword.lower() in lowered for keyword in PUBLIC_REFERENCE_KEYWORDS)


def looks_handover_valuable(text: str, record: dict[str, Any]) -> bool:
    lowered = text.lower()
    if record["domain"] in {"工作事项", "关系人", "指标口径", "风险遗留", "资产权限", "合规结算"}:
        return True
    if record["doctype"] in MEANINGFUL_DOCTYPES and any(keyword.lower() in lowered for keyword in HANDOVER_VALUE_KEYWORDS):
        return True
    if record["sensitivity"] in {"restricted", "confidential"}:
        return True
    return False


def likely_other_personal_material(text: str, aliases: list[str]) -> bool:
    if contains_owner_alias(text, aliases):
        return False
    if not any(marker in text for marker in OTHER_PERSONAL_MARKERS):
        return False
    name_tokens = re.split(r"[\s_\-—–·.（）()\[\]【】:：/\\+]+", text)
    for token in name_tokens:
        if not re.fullmatch(r"[\u4e00-\u9fff]{2,4}", token):
            continue
        if token in PERSON_TOKEN_STOPWORDS:
            continue
        if any(stopword in token for stopword in PERSON_TOKEN_STOPWORDS):
            continue
        return True
    return False


def initial_retain_decision(record: dict[str, Any], config: dict[str, Any], aliases: list[str]) -> tuple[str, list[str]]:
    relative_text = record["relative_path"]
    lowered = relative_text.lower()
    path = Path(record["source"])
    reasons: list[str] = []
    owner_match = contains_owner_alias(relative_text, aliases)

    if owner_match:
        reasons.append("owner-signal")

    if config.get("relevance", {}).get("exclude_other_people", True):
        if "工作交接-" in relative_text and not owner_match:
            return "exclude", ["other-person-handover-package"]
        if likely_other_personal_material(relative_text, aliases):
            return "exclude", ["other-person-personal-material"]

    if config.get("relevance", {}).get("fold_generated_assets", True) and looks_like_generated_asset(path, relative_text):
        if path.name.lower() in {"index.html", "start.html"}:
            return "review", ["prototype-entry-needs-confirmation"]
        return "exclude", ["generated-prototype-asset"]

    if config.get("relevance", {}).get("exclude_public_reference", True) and looks_like_public_reference(relative_text) and not owner_match:
        if looks_handover_valuable(relative_text, record) and ("客户" in relative_text or "项目" in relative_text):
            return "review", ["public-reference-in-project-context"]
        return "exclude", ["public-reference-or-template"]

    if path.suffix.lower() in ARCHIVE_SUFFIXES and not owner_match:
        return "review", ["archive-needs-confirmation"]

    if path.suffix.lower() in PROTOTYPE_SOURCE_SUFFIXES:
        reasons.append("prototype-source")

    if owner_match or looks_handover_valuable(relative_text, record):
        reasons.append("handover-value")
        return "include", reasons

    if record["doctype"] in MEANINGFUL_DOCTYPES:
        return "review", ["meaningful-document-needs-ownership-check"]

    return "exclude", ["low-handover-value"]


def extract_sortable_date(text: str) -> int:
    patterns = [
        r"(20\d{2})[._-]?([01]?\d)[._-]?([0-3]?\d)",
        r"(20\d{2})年([01]?\d)月([0-3]?\d)?日?",
        r"(?<!\d)(\d{2})([01]\d)([0-3]\d)(?!\d)",
    ]
    best = 0
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            groups = match.groups()
            if len(groups[0]) == 2:
                year = 2000 + int(groups[0])
            else:
                year = int(groups[0])
            month = int(groups[1] or 1)
            day = int(groups[2] or 1) if len(groups) > 2 else 1
            if 1 <= month <= 12 and 1 <= day <= 31:
                best = max(best, year * 10000 + month * 100 + day)
    return best


def normalize_version_group_key(record: dict[str, Any]) -> str:
    path = Path(record["relative_path"])
    stem = path.stem.lower()
    stem = re.sub(r"20\d{2}[._-]?[01]?\d[._-]?[0-3]?\d", "", stem)
    stem = re.sub(r"20\d{2}年[01]?\d月(?:[0-3]?\d日?)?", "", stem)
    stem = re.sub(r"(?<!\d)\d{6}(?!\d)", "", stem)
    stem = re.sub(r"v\d+(?:\.\d+)*", "", stem, flags=re.I)
    stem = re.sub(r"最终版|终版|最新版|正式版|定稿|发布版|初稿|草稿|修订|复核后|副本|copy", "", stem, flags=re.I)
    stem = re.sub(r"\(\d+\)|（\d+）", "", stem)
    stem = clean_text_key(stem)
    if len(stem) < 8:
        return ""
    parent = path.parent.as_posix()
    return f"{parent}::{stem}::{path.suffix.lower()}"


def version_rank(record: dict[str, Any]) -> tuple[int, int, float, int]:
    text = record["relative_path"]
    final_score = 1 if any(token in text.lower() for token in ["最终", "终版", "最新版", "正式版", "定稿", "发布版", "复核后", "final"]) else 0
    date_score = extract_sortable_date(text)
    mtime_score = Path(record["source"]).stat().st_mtime
    size_score = int(record.get("size", 0))
    return final_score, date_score, mtime_score, size_score


def clean_staged_part(value: str, max_len: int = 32) -> str:
    normalized = re.sub(r"[^\w\u4e00-\u9fff.-]+", "-", value, flags=re.UNICODE)
    normalized = re.sub(r"-{2,}", "-", normalized).strip("-._ ")
    if len(normalized) > max_len:
        normalized = normalized[:max_len].rstrip("-._ ")
    return normalized


def business_label_for_record(record: dict[str, Any]) -> str:
    generic = {"资料", "文档", "归档", "历史", "附件", "文件", "工作资料", "离职交接包"}
    relative = Path(record.get("relative_path") or record.get("original_path") or "")
    for part in reversed(relative.parts[:-1]):
        cleaned = clean_staged_part(part, 18)
        if cleaned and cleaned not in generic:
            return cleaned
    return DOMAIN_SHORT_LABELS.get(record.get("domain", ""), record.get("domain", "交接资料"))


def topic_label_for_record(record: dict[str, Any]) -> str:
    source_name = record.get("original_name") or Path(record.get("source", "file")).name
    stem = Path(source_name).stem
    stem = re.sub(r"20\d{2}[._-]?[01]?\d[._-]?[0-3]?\d", "", stem)
    stem = re.sub(r"20\d{2}年[01]?\d月(?:[0-3]?\d日?)?", "", stem)
    stem = re.sub(r"(?<!\d)\d{6}(?!\d)", "", stem)
    stem = re.sub(r"v\d+(?:\.\d+)*", "", stem, flags=re.I)
    stem = re.sub(r"最终版|终版|最新版|正式版|定稿|发布版|初稿|草稿|修订|复核后|副本|复制|copy", "", stem, flags=re.I)
    stem = re.sub(r"\(\d+\)|（\d+）", "", stem)
    return clean_staged_part(stem, 40) or "交接资料"


def date_label_for_record(record: dict[str, Any]) -> str:
    explicit = extract_sortable_date(record.get("relative_path", ""))
    if explicit:
        return f"{explicit:08d}"
    modified_at = str(record.get("modified_at") or "")
    if modified_at:
        try:
            return datetime.fromisoformat(modified_at).strftime("%Y%m%d")
        except ValueError:
            pass
    try:
        return datetime.fromtimestamp(Path(record["source"]).stat().st_mtime).strftime("%Y%m%d")
    except OSError:
        return ""


def version_label_for_record(record: dict[str, Any]) -> str:
    text = record.get("relative_path", "")
    lowered = text.lower()
    if any(token in lowered for token in ["最终", "终版", "最新版", "正式版", "定稿", "发布版", "复核后", "final"]):
        return "final"
    match = re.search(r"v\d+(?:\.\d+)*", text, flags=re.I)
    return match.group(0).lower() if match else ""


def build_staged_filename(record: dict[str, Any], index: int) -> str:
    source = Path(record["source"])
    parts = [
        f"{index:03d}",
        business_label_for_record(record),
        topic_label_for_record(record),
        DOCTYPE_LABELS.get(record.get("doctype", ""), record.get("doctype", "资料")),
        record.get("status", ""),
        date_label_for_record(record),
        version_label_for_record(record),
    ]
    cleaned_parts: list[str] = []
    seen: set[str] = set()
    for part in parts:
        cleaned = clean_staged_part(str(part), 40)
        key = clean_text_key(cleaned)
        if cleaned and key not in seen:
            seen.add(key)
            cleaned_parts.append(cleaned)
    return f"{'-'.join(cleaned_parts)}{source.suffix}"


def apply_relevance_filtering(records: list[dict[str, Any]], config: dict[str, Any]) -> list[dict[str, Any]]:
    if not config.get("features", {}).get("relevance_filtering", True):
        for record in records:
            record["retain_decision"] = "include"
            record["retain_reasons"] = ["filter-disabled"]
        return records

    aliases = owner_aliases_from_config(config)
    for record in records:
        decision, reasons = initial_retain_decision(record, config, aliases)
        record["retain_decision"] = decision
        record["retain_reasons"] = reasons
        if contains_owner_alias(record["relative_path"], aliases):
            record["owner_evidence"] = "owner-alias-in-path"
        if any(reason.startswith("other-person") for reason in reasons):
            record["other_person_signal"] = "path-or-name"
        if decision == "review":
            record["review_reason"] = "、".join(reasons)
        elif decision == "exclude":
            record["exclude_reason"] = "、".join(report_reasons(record))

    if not config.get("relevance", {}).get("dedupe_versions", True):
        return records

    groups: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        if record["retain_decision"] == "exclude":
            continue
        key = normalize_version_group_key(record)
        if key:
            record["version_group_key"] = key
            groups[key].append(record)

    for group in groups.values():
        if len(group) < 2:
            continue
        winner = max(group, key=version_rank)
        for record in group:
            if record is winner:
                record["retain_reasons"].append("version-representative")
                continue
            record["retain_decision"] = "exclude"
            record["retain_reasons"] = [*record.get("retain_reasons", []), "superseded-version"]
            record["superseded_by"] = winner["relative_path"]
            record["exclude_reason"] = "、".join(report_reasons(record))
    return records


def partition_records(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    included = [record for record in records if record.get("retain_decision") == "include"]
    review = [record for record in records if record.get("retain_decision") == "review"]
    excluded = [record for record in records if record.get("retain_decision") == "exclude"]
    return included, review, excluded


def should_skip(path: Path, target: Path, output_root: str) -> bool:
    parts = set(path.parts)
    if parts & SKIP_DIR_NAMES:
        return True
    if output_root in path.parts:
        return True
    if path.name in {"offboarding.config.json", "handover.manifest.json"}:
        return True
    if path.name.startswith("._"):
        return True
    if path.name.startswith("."):
        return True
    if path.suffix.lower() in {".pyc", ".tmp", ".ds_store"}:
        return True
    try:
        path.relative_to(target / output_root / "site")
        return True
    except ValueError:
        return False


def scan_files(target: Path, config: dict[str, Any]) -> list[dict[str, Any]]:
    output_root = config["output"]["root_dir"]
    records: list[dict[str, Any]] = []
    for path in target.rglob("*"):
        if not path.is_file():
            continue
        if should_skip(path, target, output_root):
            continue
        relative = path.relative_to(target)
        text = str(relative)
        doctype = infer_doctype(path)
        domain, reasons = infer_domain(text, doctype)
        record = {
            "source": str(path),
            "original_name": path.name,
            "original_path": str(relative),
            "relative_path": str(relative),
            "size": path.stat().st_size,
            "modified_at": datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(),
            "scope": infer_scope(text),
            "doctype": doctype,
            "status": infer_status(text),
            "sensitivity": infer_sensitivity(text),
            "domain": domain,
            "reasons": reasons,
        }
        records.append(record)
    return sorted(records, key=lambda item: item["relative_path"])


def stage_records(target: Path, config: dict[str, Any], records: list[dict[str, Any]], mode: str) -> list[dict[str, Any]]:
    if mode == "none":
        return records

    output_root = target / config["output"]["root_dir"]
    staged: list[dict[str, Any]] = []
    used_paths: set[Path] = set()
    for index, record in enumerate(records, start=1):
        stage_dir = output_root / stage_dir_for_record(config, record)
        source = Path(record["source"])
        staged_name = build_staged_filename(record, index)
        base_name = Path(staged_name).stem
        suffix = Path(staged_name).suffix or source.suffix
        candidate = stage_dir / staged_name
        counter = 1
        while candidate in used_paths or candidate.exists():
            candidate = stage_dir / f"{base_name}-{counter}{suffix}"
            counter += 1
        candidate.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, candidate)
        used_paths.add(candidate)
        cloned = dict(record)
        cloned["original_name"] = record.get("original_name") or source.name
        cloned["original_path"] = record.get("original_path") or record.get("relative_path", source.name)
        cloned["staged_name"] = candidate.name
        cloned["staged_path"] = str(candidate.relative_to(target))
        if cloned["staged_name"] != cloned["original_name"]:
            cloned["rename_reason"] = "standardized-for-successor-reading"
        if counter > 1:
            cloned["rename_reason"] = (cloned.get("rename_reason") or "standardized-for-successor-reading") + "; collision-suffix"
        staged.append(cloned)
    return staged


def collect_high_risk_items(records: list[dict[str, Any]]) -> list[dict[str, str]]:
    risky: list[dict[str, str]] = []
    for record in records:
        if record["domain"] in {"资产权限", "合规结算"} or record["sensitivity"] in {"restricted", "confidential"}:
            risky.append(
                {
                    "relative_path": record["relative_path"],
                    "domain": record["domain"],
                    "sensitivity": record["sensitivity"],
                }
            )
    return risky[:20]


def build_stats(
    records: list[dict[str, Any]],
    all_records: list[dict[str, Any]] | None = None,
    review_records: list[dict[str, Any]] | None = None,
    excluded_records: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    all_records = all_records if all_records is not None else records
    review_records = review_records or []
    excluded_records = excluded_records or []
    by_domain = Counter(record["domain"] for record in records)
    by_doctype = Counter(record["doctype"] for record in records)
    total_bytes = sum(record["size"] for record in records)
    scanned_total_bytes = sum(record["size"] for record in all_records)
    return {
        "scanned_files": len(all_records),
        "classified_files": len(records),
        "review_files": len(review_records),
        "excluded_files": len(excluded_records),
        "unclassified_files": len(review_records),
        "total_bytes": total_bytes,
        "scanned_total_bytes": scanned_total_bytes,
        "by_domain": dict(sorted(by_domain.items())),
        "by_doctype": dict(sorted(by_doctype.items())),
    }


def missing_polished_gates(config: dict[str, Any]) -> list[str]:
    gates = config.get("gates", {})
    profile = config.get("profile", {})
    missing: list[str] = []
    if not gates.get("source_dir_confirmed"):
        missing.append("material-folder-not-confirmed")
    if not gates.get("role_confirmed"):
        missing.append("role-not-confirmed")
    if not profile.get("employee_name"):
        missing.append("handover-person-missing")
    if not profile.get("role"):
        missing.append("role-missing")
    if not profile.get("successor"):
        missing.append("successor-missing")
    if not handover_coordinator_value(config):
        missing.append("handover-coordinator-missing")
    if not profile.get("last_working_day"):
        missing.append("last-working-day-missing")
    if not gates.get("successor_view_confirmed"):
        missing.append("successor-view-not-confirmed")
    if not gates.get("deep_review_complete"):
        missing.append("deep-review-not-complete")
    return missing


def delivery_status_from_gates(config: dict[str, Any]) -> dict[str, Any]:
    missing = missing_polished_gates(config)
    return {
        "status": "draft" if missing else "polished",
        "missing_gates": missing,
        "message": "仍需确认后才能作为正式交接包交付。" if missing else "已满足正式交付前置条件。",
    }


def compact_record_for_report(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "original_name": record.get("original_name", Path(record.get("source", "")).name),
        "original_path": record.get("original_path", record.get("relative_path", "")),
        "staged_name": record.get("staged_name", ""),
        "staged_path": record.get("staged_path", ""),
        "relative_path": record["relative_path"],
        "domain": record["domain"],
        "doctype": record["doctype"],
        "scope": record["scope"],
        "status": record["status"],
        "sensitivity": record["sensitivity"],
        "retain_decision": record.get("retain_decision", ""),
        "retain_reasons": report_reasons(record),
        "owner_evidence": record.get("owner_evidence", ""),
        "other_person_signal": record.get("other_person_signal", ""),
        "review_reason": record.get("review_reason", ""),
        "exclude_reason": record.get("exclude_reason", ""),
        "version_group_key": record.get("version_group_key", ""),
        "superseded_by": record.get("superseded_by", ""),
        "rename_reason": record.get("rename_reason", ""),
    }


def report_reasons(record: dict[str, Any]) -> list[str]:
    reasons = list(record.get("retain_reasons", []))
    if record.get("retain_decision") == "exclude":
        filtered = [
            reason
            for reason in reasons
            if reason not in {"owner-signal", "handover-value", "prototype-source", "version-representative"}
        ]
        return filtered or reasons
    return reasons


def build_filename_mapping(records: list[dict[str, Any]]) -> list[dict[str, str]]:
    mapping: list[dict[str, str]] = []
    for record in records:
        if not record.get("staged_path"):
            continue
        mapping.append(
            {
                "original_name": record.get("original_name", ""),
                "original_path": record.get("original_path", record.get("relative_path", "")),
                "staged_name": record.get("staged_name", Path(record.get("staged_path", "")).name),
                "staged_path": record.get("staged_path", ""),
                "rename_reason": record.get("rename_reason", ""),
                "version_group_key": record.get("version_group_key", ""),
                "superseded_by": record.get("superseded_by", ""),
            }
        )
    return mapping


def build_version_groups(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        key = record.get("version_group_key")
        if key:
            grouped[key].append(record)
    groups: list[dict[str, Any]] = []
    for key, items in grouped.items():
        if len(items) < 2:
            continue
        retained = next((item for item in items if item.get("retain_decision") != "exclude"), items[0])
        groups.append(
            {
                "version_group_key": key,
                "retained": retained.get("relative_path", ""),
                "items": [
                    {
                        "relative_path": item.get("relative_path", ""),
                        "retain_decision": item.get("retain_decision", ""),
                        "superseded_by": item.get("superseded_by", ""),
                    }
                    for item in items
                ],
            }
        )
    return groups


def build_manifest(
    target: Path,
    config: dict[str, Any],
    records: list[dict[str, Any]],
    assumptions: list[str],
    all_records: list[dict[str, Any]] | None = None,
    review_records: list[dict[str, Any]] | None = None,
    excluded_records: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    all_records = all_records if all_records is not None else records
    review_records = review_records or []
    excluded_records = excluded_records or []
    stats = build_stats(records, all_records, review_records, excluded_records)
    modules = []
    by_domain = defaultdict(list)
    for record in records:
        by_domain[record["domain"]].append(record)
    excluded_reason_counts = Counter(
        reason for record in excluded_records for reason in report_reasons(record)
    )
    review_reason_counts = Counter(
        reason for record in review_records for reason in record.get("retain_reasons", [])
    )
    for domain in config["taxonomy"]["content_domains"]:
        modules.append(
            {
                "name": domain,
                "count": len(by_domain.get(domain, [])),
                "sample_files": [item.get("staged_path", item["relative_path"]) for item in by_domain.get(domain, [])[:5]],
            }
        )
    return {
        "generated_at": timestamp_now(),
        "source_root": str(target),
        "output_root": str(target / config["output"]["root_dir"]),
        "site_entry": str(target / config["output"]["site_dir"] / "index.html"),
        "profile": config["profile"],
        "presentation_modules": config["taxonomy"]["presentation_modules"],
        "modules": modules,
        "stats": stats,
        "files": records,
        "filename_mapping": build_filename_mapping(records),
        "review_items": [compact_record_for_report(record) for record in review_records],
        "excluded_items": [compact_record_for_report(record) for record in excluded_records],
        "other_person_items": [
            compact_record_for_report(record)
            for record in [*records, *review_records, *excluded_records]
            if record.get("other_person_signal")
            or any(reason.startswith("other-person") for reason in record.get("retain_reasons", []))
        ],
        "version_groups": build_version_groups(all_records),
        "retention_stats": {
            "include": len(records),
            "review": len(review_records),
            "exclude": len(excluded_records),
            "scanned": len(all_records),
        },
        "delivery": delivery_status_from_gates(config),
        "excluded_reason_counts": dict(excluded_reason_counts.most_common()),
        "review_reason_counts": dict(review_reason_counts.most_common()),
        "high_risk_items": collect_high_risk_items(records),
        "missed_items_checklist": str(
            target / config["output"]["root_dir"] / STATUS_DIR / MISSED_ITEMS_NAME
        ),
        "assumptions": assumptions,
        "notes": [
            "自动分类采用关键词和文件类型启发式规则，并先进行交接价值筛选。",
            "输出目录只复制纳入交接包的文件，待确认和未纳入文件保留在原始目录。",
        ],
    }


def merge_assumptions(existing: list[str], new_items: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in [*existing, *new_items]:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result


def prune_empty_directories(root: Path) -> list[str]:
    removed: list[str] = []
    if not root.exists():
        return removed
    for directory in sorted((p for p in root.rglob("*") if p.is_dir()), key=lambda p: len(p.parts), reverse=True):
        try:
            next(directory.iterdir())
        except StopIteration:
            directory.rmdir()
            removed.append(str(directory))
    return removed


def bytes_to_human(size: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.1f}{unit}" if unit != "B" else f"{int(value)}B"
        value /= 1024
    return f"{size}B"


def make_site_href(config: dict[str, Any], staged_path: str | None) -> str:
    if not staged_path:
        return "#"
    output_root = config["output"]["root_dir"].strip("/").replace("\\", "/")
    normalized = staged_path.replace("\\", "/")
    if normalized.startswith(output_root + "/"):
        normalized = normalized[len(output_root) + 1:]
    return "../" + normalized


def markdown_to_simple_html(markdown_text: str) -> str:
    lines = markdown_text.splitlines()
    html_lines: list[str] = []
    in_ul = False
    in_table = False
    table_rows: list[list[str]] = []

    def close_ul() -> None:
        nonlocal in_ul
        if in_ul:
            html_lines.append("</ul>")
            in_ul = False

    def flush_table() -> None:
        nonlocal in_table, table_rows
        if not in_table or not table_rows:
            in_table = False
            table_rows = []
            return
        html_lines.append('<div class="md-table-wrap"><table class="md-table">')
        header = table_rows[0]
        html_lines.append("<thead><tr>" + "".join(f"<th>{html.escape(cell)}</th>" for cell in header) + "</tr></thead>")
        body_rows = table_rows[2:] if len(table_rows) > 1 and all(set(cell) <= {'-'} for cell in [c.replace(' ', '') for c in table_rows[1]]) else table_rows[1:]
        html_lines.append("<tbody>")
        for row in body_rows:
            html_lines.append("<tr>" + "".join(f"<td>{html.escape(cell)}</td>" for cell in row) + "</tr>")
        html_lines.append("</tbody></table></div>")
        in_table = False
        table_rows = []

    for raw_line in lines:
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            close_ul()
            flush_table()
            continue
        if stripped.startswith("|") and stripped.endswith("|"):
            close_ul()
            in_table = True
            table_rows.append([cell.strip() for cell in stripped.strip("|").split("|")])
            continue
        flush_table()
        if stripped.startswith("# "):
            close_ul()
            html_lines.append(f"<h1>{html.escape(stripped[2:])}</h1>")
        elif stripped.startswith("## "):
            close_ul()
            html_lines.append(f"<h2>{html.escape(stripped[3:])}</h2>")
        elif stripped.startswith("### "):
            close_ul()
            html_lines.append(f"<h3>{html.escape(stripped[4:])}</h3>")
        elif stripped.startswith("- "):
            if not in_ul:
                html_lines.append("<ul>")
                in_ul = True
            html_lines.append(f"<li>{html.escape(stripped[2:])}</li>")
        elif re.match(r"^\d+\.\s+", stripped):
            close_ul()
            content = re.sub(r"^\d+\.\s+", "", stripped)
            html_lines.append(f'<p class="md-numbered">{html.escape(content)}</p>')
        else:
            close_ul()
            html_lines.append(f"<p>{html.escape(stripped)}</p>")
    close_ul()
    flush_table()
    return "\n".join(html_lines)


def table_html_from_rows(rows: list[list[str]], max_rows: int = 18, max_cols: int = 8) -> str:
    clipped = [row[:max_cols] for row in rows[:max_rows] if row]
    if not clipped:
        return ""
    header = clipped[0]
    body = clipped[1:] if len(clipped) > 1 else []
    output = ['<div class="md-table-wrap"><table class="md-table">']
    output.append("<thead><tr>" + "".join(f"<th>{html.escape(cell)}</th>" for cell in header) + "</tr></thead>")
    output.append("<tbody>")
    for row in body:
        output.append("<tr>" + "".join(f"<td>{html.escape(cell)}</td>" for cell in row) + "</tr>")
    output.append("</tbody></table></div>")
    return "\n".join(output)


def xml_text_fragments(raw: bytes, limit: int = 80) -> list[str]:
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        return []
    fragments: list[str] = []
    for node in root.iter():
        if node.text and node.text.strip():
            text = re.sub(r"\s+", " ", node.text.strip())
            if text:
                fragments.append(text)
        if len(fragments) >= limit:
            break
    return fragments


def office_text_preview(path: Path, suffix: str) -> str:
    try:
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            fragments: list[str] = []
            if suffix == ".docx":
                candidates = ["word/document.xml"]
            elif suffix == ".pptx":
                candidates = sorted(name for name in names if name.startswith("ppt/slides/slide") and name.endswith(".xml"))[:12]
            else:
                candidates = ["xl/sharedStrings.xml"]
            for name in candidates:
                if name in names:
                    fragments.extend(xml_text_fragments(archive.read(name), limit=80))
                if len(fragments) >= 80:
                    break
    except (OSError, zipfile.BadZipFile, KeyError):
        fragments = []
    deduped: list[str] = []
    seen: set[str] = set()
    for item in fragments:
        if item in seen:
            continue
        seen.add(item)
        deduped.append(item)
        if len(deduped) >= 40:
            break
    if not deduped:
        return '<p class="empty-state">暂时无法生成预览，请打开原文件查看。</p>'
    return "<ul>" + "".join(f"<li>{html.escape(item)}</li>" for item in deduped) + "</ul>"


def file_preview_html(path: Path, href: str, doctype: str) -> str | None:
    suffix = path.suffix.lower()
    if suffix in PREVIEWABLE_IMAGE_SUFFIXES:
        return f'<img class="file-image-preview" src="{html.escape(href)}" alt="{html.escape(path.name)}">'
    if suffix == ".pdf":
        return f'<iframe class="file-frame-preview" src="{html.escape(href)}" title="{html.escape(path.name)}"></iframe>'
    if suffix in PREVIEWABLE_TABLE_SUFFIXES:
        try:
            with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
                rows = list(csv.reader(handle))
        except OSError:
            rows = []
        return table_html_from_rows(rows) or '<p class="empty-state">暂时无法生成表格预览，请打开原文件查看。</p>'
    if suffix in PREVIEWABLE_TEXT_SUFFIXES:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")[:6000]
        except OSError:
            text = ""
        return markdown_to_simple_html(text) if suffix == ".md" else f"<pre>{html.escape(text)}</pre>"
    if suffix in PREVIEWABLE_OFFICE_SUFFIXES:
        return office_text_preview(path, suffix)
    return None


def build_file_previews(config: dict[str, Any], manifest: dict[str, Any], max_items: int = 80) -> dict[str, dict[str, str]]:
    source_root = Path(manifest.get("source_root", ""))
    previews: dict[str, dict[str, str]] = {}
    for item in manifest.get("files", []):
        staged_path = item.get("staged_path")
        if not staged_path:
            continue
        href = make_site_href(config, staged_path)
        path = source_root / staged_path
        preview = file_preview_html(path, href, item.get("doctype", ""))
        if not preview:
            continue
        preview_id = f"file-preview-{len(previews)}"
        previews[staged_path.replace("\\", "/")] = {
            "id": preview_id,
            "title": item.get("relative_path", staged_path),
            "staged_path": staged_path,
            "html": preview,
        }
        if len(previews) >= max_items:
            break
    return previews


def build_core_markdown_previews(target: Path, config: dict[str, Any]) -> list[dict[str, str]]:
    output_root = target / config["output"]["root_dir"]
    preview_candidates = [
        ("入口总览", output_root / "00-说明与导航/00-交接总览.md"),
        ("阅读顺序", output_root / "00-说明与导航/01-阅读顺序.md"),
        ("筛选与排除报告", output_root / f"00-说明与导航/{FILTER_REPORT_NAME}"),
        ("交接信息", output_root / "01-交接信息/00-交接信息.md"),
        ("模块总览", output_root / "02-交接总览/00-交接总览.md"),
        ("进行中事项总表", output_root / f"{STATUS_DIR}/{INFLIGHT_SUMMARY_NAME}"),
        ("高遗漏检查清单", output_root / f"{STATUS_DIR}/{MISSED_ITEMS_NAME}"),
        ("交接结论说明", output_root / f"{STATUS_DIR}/{CONCLUSION_NAME}"),
    ]
    previews: list[dict[str, str]] = []
    for title, path in preview_candidates:
        if path.exists():
            previews.append(
                {
                    "title": title,
                    "path": str(path.relative_to(target)),
                    "html": markdown_to_simple_html(path.read_text()),
                }
            )
    return previews



def render_site(config: dict[str, Any], manifest: dict[str, Any], markdown_previews: list[dict[str, str]] | None = None) -> str:
    title = html.escape(config["output"]["site_title"])
    profile = manifest.get("profile", {})
    stats = manifest.get("stats", {})
    files = manifest.get("files", [])
    modules = manifest.get("modules", [])
    markdown_previews = markdown_previews or []
    preview_map = {item["path"].replace("\\", "/"): str(idx) for idx, item in enumerate(markdown_previews)}
    preview_title_to_idx = {item["title"]: str(idx) for idx, item in enumerate(markdown_previews)}
    file_previews = build_file_previews(config, manifest)
    delivery = manifest.get("delivery", {})
    delivery_status = delivery.get("status", "draft")
    delivery_label = "草稿待确认" if delivery_status == "draft" else "正式交接包"
    missing_gate_text = "、".join(delivery.get("missing_gates", [])) or "无"

    status_counts = Counter(item.get("status", "") for item in files)
    sensitivity_counts = Counter(item.get("sensitivity", "") for item in files)
    profile_summary_parts = [
        profile.get("department") or "",
        profile.get("role") or "",
        f"接手人：{profile.get('successor')}" if profile.get("successor") else "",
    ]
    profile_summary = " · ".join(part for part in profile_summary_parts if part) or "交接范围待补充"

    def option_items(values: list[str], counts: Counter[str] | None = None) -> str:
        items = []
        for value in values:
            label = value
            if counts is not None:
                label = f"{value} ({counts.get(value, 0)})"
            items.append(f'<option value="{html.escape(value)}">{html.escape(label)}</option>')
        return "".join(items)

    def doc_jump(title_key: str, label: str) -> str:
        preview_id = preview_title_to_idx.get(title_key)
        if preview_id is None:
            return f'<span class="doc-action disabled">{html.escape(label)}</span>'
        return f'<button type="button" class="doc-action" data-preview-jump="{html.escape(preview_id)}">{html.escape(label)}</button>'

    status_values = config.get("labels", {}).get("status", sorted(status_counts))
    sensitivity_values = config.get("labels", {}).get("sensitivity", sorted(sensitivity_counts))
    domain_options = "".join(
        f'<option value="{html.escape(module["name"])}">{html.escape(module["name"])}</option>'
        for module in modules
    )
    status_options = option_items(status_values, status_counts)
    sensitivity_options = option_items(sensitivity_values, sensitivity_counts)

    module_items = "\n".join(
        f"""
        <article class="module-item" data-domain="{html.escape(module['name'])}">
          <div>
            <h3>{html.escape(module['name'])}</h3>
            <p>{module['count']} 个文件</p>
          </div>
          <ul>{''.join(f"<li>{html.escape(item)}</li>" for item in module['sample_files'][:4]) or '<li>暂无文件</li>'}</ul>
          <button type="button" class="subtle-button" data-domain-jump="{html.escape(module['name'])}">查看文件</button>
        </article>
        """
        for module in modules
    )

    risky_items = "\n".join(
        f"""
        <li class="risk-item">
          <span class="risk-domain">{html.escape(item['domain'])}</span>
          <span class="risk-path">{html.escape(item['relative_path'])}</span>
          <span class="risk-level">{html.escape(item['sensitivity'])}</span>
        </li>
        """
        for item in manifest.get("high_risk_items", [])
    ) or '<li class="empty-state">未发现高风险条目。</li>'

    assumption_items = "\n".join(
        f"<li>{html.escape(item)}</li>" for item in manifest.get("assumptions", [])
    ) or "<li>暂无额外假设。</li>"
    review_items = manifest.get("review_items", [])
    excluded_items = manifest.get("excluded_items", [])
    retention_stats = manifest.get("retention_stats", {})
    review_rows = "\n".join(
        f"<tr><td>{html.escape(item['relative_path'])}</td><td>{html.escape('、'.join(item.get('retain_reasons', [])) or '待确认')}</td></tr>"
        for item in review_items[:30]
    ) or '<tr><td colspan="2">暂无需要确认的文件。</td></tr>'
    excluded_reason_rows = "\n".join(
        f"<tr><td>{html.escape(reason)}</td><td>{count}</td></tr>"
        for reason, count in manifest.get("excluded_reason_counts", {}).items()
    ) or '<tr><td colspan="2">暂无未纳入原因。</td></tr>'
    excluded_examples_rows = "\n".join(
        f"<tr><td>{html.escape(item['relative_path'])}</td><td>{html.escape('、'.join(item.get('retain_reasons', [])) or '未纳入')}</td></tr>"
        for item in excluded_items[:30]
    ) or '<tr><td colspan="2">暂无未纳入文件。</td></tr>'

    top_files = sorted(files, key=lambda item: item.get("size", 0), reverse=True)[:20]
    top_file_rows = "\n".join(
        f"<tr><td>{html.escape(item['domain'])}</td><td>{html.escape(item['relative_path'])}</td><td>{html.escape(item.get('staged_path', '-'))}</td><td>{bytes_to_human(item['size'])}</td></tr>"
        for item in top_files
    ) or '<tr><td colspan="4">暂无文件。</td></tr>'

    doc_cards = "\n".join(
        f"""
        <button type="button" class="doc-link" data-preview-jump="{idx}">
          <span>{html.escape(item["title"])}</span>
          <small>{html.escape(item["path"])}</small>
        </button>
        """
        for idx, item in enumerate(markdown_previews)
    ) or '<p class="empty-state">暂无核心文档预览。</p>'

    preview_buttons = "\n".join(
        f'<button type="button" class="preview-tab" data-preview="{idx}">{html.escape(item["title"])}</button>'
        for idx, item in enumerate(markdown_previews)
    ) or '<span class="meta">暂无可预览文档</span>'
    preview_panels = "\n".join(
        f'''<article class="preview-panel" data-preview="{idx}">
<div class="preview-source">来源：<code>{html.escape(item["path"])}</code></div>
<div class="md-preview">{item["html"]}</div>
</article>'''
        for idx, item in enumerate(markdown_previews)
    ) or '<p class="empty-state">当前没有可预览的核心 Markdown 文档。</p>'

    file_preview_tabs = "\n".join(
        f'<button type="button" class="file-preview-tab" data-file-preview="{html.escape(item["id"])}">{html.escape(Path(item["title"]).name)}</button>'
        for item in file_previews.values()
    ) or '<span class="meta">暂无可预览文件</span>'
    file_preview_panels = "\n".join(
        f'''<article class="file-preview-panel" data-file-preview="{html.escape(item["id"])}">
<div class="preview-source">文件：<code>{html.escape(item["staged_path"])}</code></div>
<div class="md-preview file-preview-body">{item["html"]}</div>
</article>'''
        for item in file_previews.values()
    ) or '<p class="empty-state">当前没有可预览的文件。可从文件表打开原文件。</p>'

    def status_pill(value: str) -> str:
        safe = html.escape(value)
        css = {
            "draft": "pill-warning",
            "review": "pill-warning",
            "final": "pill-success",
            "historical": "pill-muted",
        }.get(value, "pill-muted")
        return f'<span class="pill {css}">{safe}</span>'

    def sensitivity_pill(value: str) -> str:
        safe = html.escape(value)
        css = {
            "public": "pill-muted",
            "internal": "pill-info",
            "restricted": "pill-warning",
            "confidential": "pill-danger",
        }.get(value, "pill-muted")
        return f'<span class="pill {css}">{safe}</span>'

    file_rows: list[str] = []
    for item in files:
        href = make_site_href(config, item.get("staged_path"))
        display_target = item.get("staged_path", "")
        normalized_target = display_target.replace("\\", "/")
        preview_id = preview_map.get(normalized_target)
        if item.get("staged_path"):
            file_preview = file_previews.get(normalized_target)
            open_link = f'<a class="file-open-link" href="{html.escape(href)}" target="_blank" rel="noopener noreferrer">打开原文件</a>'
            target_cell = (
                f'<a href="#documents" class="md-preview-link" data-preview-target="{html.escape(preview_id)}">{html.escape(display_target)}</a>'
                if preview_id is not None
                else (
                    f'<div class="file-actions"><button type="button" class="file-preview-button" data-file-preview-jump="{html.escape(file_preview["id"])}">查看预览</button>{open_link}</div><small>{html.escape(display_target)}</small>'
                    if file_preview
                    else f'<div class="file-actions">{open_link}</div><small>{html.escape(display_target)}</small>'
                )
            )
        else:
            target_cell = '<span class="muted">未分发</span>'
        search_blob = " ".join(
            [
                item.get("domain", ""),
                item.get("original_name", ""),
                item.get("original_path", ""),
                item.get("relative_path", ""),
                item.get("staged_name", ""),
                item.get("staged_path", ""),
                item.get("doctype", ""),
                item.get("scope", ""),
                item.get("status", ""),
                item.get("sensitivity", ""),
            ]
        )
        file_rows.append(
            f"""<tr data-domain="{html.escape(item['domain'])}" data-status="{html.escape(item['status'])}" data-sensitivity="{html.escape(item['sensitivity'])}" data-search="{html.escape(search_blob.lower())}">
<td>{html.escape(item['domain'])}</td>
<td>{html.escape(item['relative_path'])}</td>
<td>{target_cell}</td>
<td>{html.escape(item['doctype'])}</td>
<td>{html.escape(item['scope'])}</td>
<td>{status_pill(item['status'])}</td>
<td>{sensitivity_pill(item['sensitivity'])}</td>
<td>{bytes_to_human(item['size'])}</td>
</tr>"""
        )
    file_rows_html = "\n".join(file_rows) or '<tr class="empty-table"><td colspan="8">暂无文件。</td></tr>'

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
    :root {{
      --page: #FBFCFE;
      --surface: #FFFFFF;
      --surface-alt: #F4F7FB;
      --ink: #172033;
      --muted: #667085;
      --line: #E6EBF2;
      --line-strong: #CBD5E1;
      --primary: #2563EB;
      --primary-ink: #1D4ED8;
      --cyan: #0891B2;
      --success: #0E9F6E;
      --warning: #B7791F;
      --danger: #C2410C;
      --shadow: 0 14px 36px rgba(23, 32, 51, 0.08);
    }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{
      margin: 0;
      color: var(--ink);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
      letter-spacing: 0;
      background: var(--page);
    }}
    a {{ color: var(--primary-ink); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    button, input, select {{ font: inherit; }}
    button:focus-visible, a:focus-visible, input:focus-visible, select:focus-visible {{
      outline: 3px solid rgba(37, 99, 235, 0.22);
      outline-offset: 2px;
    }}
    .app-header {{
      position: sticky;
      top: 0;
      z-index: 20;
      background: rgba(255, 255, 255, 0.96);
      border-bottom: 1px solid var(--line);
      backdrop-filter: blur(10px);
    }}
    .header-inner {{
      max-width: 1440px;
      margin: 0 auto;
      padding: 18px 28px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 18px;
    }}
    .eyebrow {{
      margin: 0 0 4px;
      color: var(--primary-ink);
      font-size: 12px;
      font-weight: 700;
    }}
    h1, h2, h3, p {{ margin-top: 0; }}
    h1 {{ margin-bottom: 4px; font-size: 24px; line-height: 1.25; }}
    h2 {{ margin-bottom: 8px; font-size: 20px; line-height: 1.35; }}
    h3 {{ margin-bottom: 6px; font-size: 15px; line-height: 1.4; }}
    p, li, td, th {{ line-height: 1.6; }}
    .header-copy, .muted, .meta {{ color: var(--muted); }}
    .header-copy {{ margin: 0; font-size: 14px; }}
    .header-actions {{ display: flex; gap: 10px; flex-wrap: wrap; justify-content: flex-end; }}
    .primary-button, .secondary-button, .subtle-button, .doc-action, .preview-tab, .doc-link, .file-preview-tab, .file-preview-button {{
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--surface);
      color: var(--ink);
      cursor: pointer;
    }}
    .primary-button {{
      border-color: var(--primary);
      background: var(--primary);
      color: #fff;
      padding: 10px 14px;
      font-weight: 700;
    }}
    .secondary-button {{
      padding: 10px 14px;
      font-weight: 600;
    }}
    .app-shell {{
      max-width: 1440px;
      margin: 0 auto;
      display: grid;
      grid-template-columns: 236px minmax(0, 1fr);
    }}
    .side-nav {{
      position: sticky;
      top: 73px;
      align-self: start;
      min-height: calc(100vh - 73px);
      padding: 24px 18px;
      border-right: 1px solid var(--line);
    }}
    .side-nav a {{
      display: block;
      padding: 9px 10px;
      border-radius: 8px;
      color: var(--muted);
      font-size: 14px;
      font-weight: 600;
    }}
    .side-nav a:hover {{
      background: var(--surface-alt);
      color: var(--primary-ink);
      text-decoration: none;
    }}
    main {{ min-width: 0; padding: 26px 32px 72px; }}
    .section {{
      padding: 28px 0;
      border-bottom: 1px solid var(--line);
      scroll-margin-top: 96px;
    }}
    .section:first-child {{ padding-top: 4px; }}
    .section-header {{
      display: flex;
      align-items: flex-end;
      justify-content: space-between;
      gap: 18px;
      margin-bottom: 16px;
    }}
    .section-header p {{ margin: 0; max-width: 760px; color: var(--muted); }}
    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 12px;
      margin-bottom: 16px;
    }}
    .kpi, .doc-link, .module-item, .preview-shell, .risk-panel, .table-panel {{
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 8px;
    }}
    .kpi {{ padding: 15px; }}
    .kpi strong {{ display: block; margin-bottom: 4px; font-size: 24px; line-height: 1.2; }}
    .kpi span {{ color: var(--muted); font-size: 13px; }}
    .profile-grid {{
      display: grid;
      grid-template-columns: repeat(4, minmax(160px, 1fr));
      gap: 1px;
      overflow: hidden;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--line);
    }}
    .profile-grid div {{ padding: 12px; background: var(--surface); }}
    .profile-grid dt {{ color: var(--muted); font-size: 12px; }}
    .profile-grid dd {{ margin: 4px 0 0; font-weight: 650; }}
    .path-list {{
      display: grid;
      grid-template-columns: repeat(4, minmax(180px, 1fr));
      gap: 12px;
      margin: 0;
      padding: 0;
      list-style: none;
    }}
    .path-list li {{
      min-height: 150px;
      padding: 16px;
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 8px;
    }}
    .step-no {{ display: inline-flex; margin-bottom: 12px; color: var(--primary-ink); font-weight: 800; }}
    .doc-action {{
      margin-top: 10px;
      padding: 7px 10px;
      color: var(--primary-ink);
      font-weight: 700;
    }}
    .doc-action.disabled {{ display: inline-block; color: var(--muted); cursor: default; }}
    .delivery-banner {{
      margin-bottom: 16px;
      padding: 12px 14px;
      border: 1px solid var(--line);
      border-left: 4px solid var(--warning);
      border-radius: 8px;
      background: #FFFDF7;
      color: var(--ink);
    }}
    .delivery-banner.polished {{
      border-left-color: var(--success);
      background: #F0FDF4;
    }}
    .delivery-banner strong {{ margin-right: 8px; }}
    .doc-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 10px;
    }}
    .doc-link {{
      min-height: 88px;
      padding: 13px;
      text-align: left;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      gap: 8px;
    }}
    .doc-link span {{ color: var(--ink); font-weight: 700; }}
    .doc-link small {{ color: var(--muted); overflow-wrap: anywhere; }}
    .module-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 12px;
    }}
    .module-item {{ padding: 15px; display: grid; gap: 12px; }}
    .module-item p {{ margin: 0; color: var(--muted); font-size: 13px; }}
    .module-item ul {{ margin: 0; padding-left: 18px; color: var(--muted); font-size: 13px; }}
    .subtle-button {{
      justify-self: start;
      padding: 7px 10px;
      color: var(--primary-ink);
      font-weight: 700;
    }}
    .risk-panel {{ padding: 16px; }}
    .risk-grid {{
      display: grid;
      grid-template-columns: minmax(0, 1.35fr) minmax(260px, .65fr);
      gap: 14px;
    }}
    .risk-list, .assumption-list {{ margin: 0; padding: 0; list-style: none; }}
    .risk-item {{
      display: grid;
      grid-template-columns: 96px minmax(0, 1fr) 110px;
      gap: 10px;
      align-items: start;
      padding: 10px 0;
      border-bottom: 1px solid var(--line);
    }}
    .risk-item:last-child {{ border-bottom: 0; }}
    .risk-domain, .risk-level {{
      font-size: 12px;
      font-weight: 800;
      color: var(--danger);
    }}
    .risk-path {{ overflow-wrap: anywhere; }}
    .assumption-list li {{
      padding: 9px 0;
      border-bottom: 1px solid var(--line);
      color: var(--muted);
    }}
    .assumption-list li:last-child {{ border-bottom: 0; }}
    .toolbar {{
      display: grid;
      grid-template-columns: minmax(220px, 1fr) repeat(3, minmax(150px, 190px)) auto;
      gap: 10px;
      margin-bottom: 12px;
    }}
    .toolbar input, .toolbar select {{
      width: 100%;
      min-height: 40px;
      padding: 9px 10px;
      border: 1px solid var(--line-strong);
      border-radius: 8px;
      background: var(--surface);
      color: var(--ink);
    }}
    .table-panel {{ overflow: hidden; }}
    .selection-examples {{ margin-top: 14px; }}
    .table-wrap {{ width: 100%; overflow-x: auto; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    th, td {{
      padding: 10px 12px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      vertical-align: top;
      white-space: nowrap;
    }}
    td:nth-child(2), td:nth-child(3) {{ white-space: normal; min-width: 220px; overflow-wrap: anywhere; }}
    th {{ background: var(--surface-alt); color: var(--muted); font-size: 12px; font-weight: 800; }}
    tbody tr:hover {{ background: #F8FAFC; }}
    .pill {{
      display: inline-flex;
      align-items: center;
      min-height: 22px;
      padding: 2px 8px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 800;
      border: 1px solid transparent;
    }}
    .pill-muted {{ background: #F1F5F9; color: #475569; border-color: #E2E8F0; }}
    .pill-info {{ background: #E0F2FE; color: #0369A1; border-color: #BAE6FD; }}
    .pill-success {{ background: #ECFDF5; color: #047857; border-color: #A7F3D0; }}
    .pill-warning {{ background: #FFF7ED; color: #B45309; border-color: #FED7AA; }}
    .pill-danger {{ background: #FEF2F2; color: #B91C1C; border-color: #FECACA; }}
    .preview-shell {{ padding: 16px; }}
    .document-preview {{ margin-top: 14px; }}
    .preview-tabs {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 14px; }}
    .preview-tab, .file-preview-tab {{ padding: 8px 11px; font-weight: 700; }}
    .preview-tab.active, .file-preview-tab.active {{ border-color: var(--primary); background: #EFF6FF; color: var(--primary-ink); }}
    .preview-panel, .file-preview-panel {{ display: none; border-top: 1px solid var(--line); padding-top: 14px; }}
    .preview-panel.active, .file-preview-panel.active {{ display: block; }}
    .preview-source {{ color: var(--muted); font-size: 13px; margin-bottom: 10px; }}
    .md-preview {{ max-width: 980px; }}
    .md-preview h1, .md-preview h2, .md-preview h3 {{ color: var(--ink); margin: 16px 0 10px; }}
    .md-preview h1 {{ font-size: 22px; }}
    .md-preview h2 {{ font-size: 18px; }}
    .md-preview h3 {{ font-size: 16px; }}
    .md-preview p, .md-preview li {{ margin: 8px 0; line-height: 1.7; }}
    .md-preview ul {{ padding-left: 20px; margin: 8px 0; }}
    .md-numbered {{ padding-left: 4px; }}
    .md-table-wrap {{ overflow-x: auto; margin: 12px 0; }}
    .md-table {{ min-width: 640px; }}
    .md-table th, .md-table td {{ border: 1px solid var(--line); padding: 8px 10px; white-space: normal; }}
    .file-actions {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 6px; }}
    .file-open-link, .file-preview-button {{
      display: inline-flex;
      align-items: center;
      min-height: 30px;
      padding: 5px 9px;
      border-radius: 8px;
      font-size: 12px;
      font-weight: 800;
    }}
    .file-open-link {{ border: 1px solid var(--line); background: var(--surface); }}
    .file-preview-button {{ color: var(--primary-ink); }}
    .file-image-preview {{ max-width: 100%; max-height: 640px; border: 1px solid var(--line); border-radius: 8px; }}
    .file-frame-preview {{ width: 100%; min-height: 640px; border: 1px solid var(--line); border-radius: 8px; background: var(--surface); }}
    .file-preview-body pre {{ white-space: pre-wrap; overflow-wrap: anywhere; background: var(--surface-alt); padding: 12px; border-radius: 8px; }}
    code {{
      background: #EEF4FF;
      border-radius: 6px;
      padding: 2px 6px;
      color: var(--primary-ink);
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    }}
    .empty-state, .empty-table td {{ color: var(--muted); }}
    #file-count {{ margin: 10px 0 0; color: var(--muted); font-size: 13px; }}
    @media (max-width: 980px) {{
      .app-shell {{ display: block; }}
      .side-nav {{
        position: static;
        min-height: 0;
        display: flex;
        gap: 8px;
        overflow-x: auto;
        padding: 12px 18px;
        border-right: 0;
        border-bottom: 1px solid var(--line);
      }}
      .side-nav a {{ white-space: nowrap; }}
      main {{ padding: 22px 18px 56px; }}
      .kpi-grid, .profile-grid, .path-list, .risk-grid {{ grid-template-columns: 1fr 1fr; }}
      .toolbar {{ grid-template-columns: 1fr 1fr; }}
      .header-inner {{ align-items: flex-start; flex-direction: column; }}
      .header-actions {{ justify-content: flex-start; }}
    }}
    @media (max-width: 640px) {{
      .kpi-grid, .profile-grid, .path-list, .risk-grid, .toolbar {{ grid-template-columns: 1fr; }}
      .risk-item {{ grid-template-columns: 1fr; }}
      h1 {{ font-size: 22px; }}
      main {{ padding-left: 14px; padding-right: 14px; }}
    }}
    @media print {{
      .app-header, .side-nav, .toolbar, .preview-tabs, .subtle-button, .doc-action {{ display: none !important; }}
      .app-shell {{ display: block; }}
      main {{ padding: 0; }}
      .section {{ break-inside: avoid; }}
      body {{ background: #fff; }}
    }}
  </style>
</head>
<body>
  <header class="app-header">
    <div class="header-inner">
      <div>
        <p class="eyebrow">交接工作台</p>
        <h1>{title}</h1>
        <p class="header-copy">{html.escape(profile_summary)}。先确认范围，再处理风险与未完事项。</p>
      </div>
      <div class="header-actions">
        <button type="button" class="secondary-button" id="focus-search">搜索文件</button>
        <a class="primary-button" href="#documents">查看核心文档</a>
      </div>
    </div>
  </header>
  <div class="app-shell">
    <nav class="side-nav" aria-label="交接导航">
      <a href="#overview">总览</a>
      <a href="#start">从这里开始</a>
      <a href="#documents">核心文档</a>
      <a href="#file-preview">文件预览</a>
      <a href="#modules">专项模块</a>
      <a href="#selection">筛选结果</a>
      <a href="#risks">风险与待确认</a>
      <a href="#large-files">重点文件</a>
      <a href="#files">已纳入文件</a>
    </nav>
    <main>
      <div class="delivery-banner {'polished' if delivery_status == 'polished' else 'draft'}">
        <strong>{html.escape(delivery_label)}</strong>
        <span>{html.escape(delivery.get('message', '仍需确认后才能作为正式交接包交付。'))}</span>
        <span class="meta"> 缺失项：{html.escape(missing_gate_text)}</span>
      </div>
      <section id="overview" class="section">
        <div class="section-header">
          <div>
            <h2>交接总览</h2>
            <p>这个页面是交接包入口，用来快速确认范围、风险、核心文档和全部文件位置。</p>
          </div>
        </div>
        <div class="kpi-grid" aria-label="扫描概览">
          <div class="kpi"><strong>{stats.get('scanned_files', 0)}</strong><span>扫描文件</span></div>
          <div class="kpi"><strong>{retention_stats.get('include', len(files))}</strong><span>已纳入</span></div>
          <div class="kpi"><strong>{retention_stats.get('review', 0)}</strong><span>需要确认</span></div>
          <div class="kpi"><strong>{retention_stats.get('exclude', 0)}</strong><span>未纳入</span></div>
          <div class="kpi"><strong>{len(manifest.get('high_risk_items', []))}</strong><span>高风险条目</span></div>
        </div>
        <dl class="profile-grid">
          <div><dt>交接人</dt><dd>{html.escape(profile.get('employee_name') or '待补充')}</dd></div>
          <div><dt>部门</dt><dd>{html.escape(profile.get('department') or '待补充')}</dd></div>
          <div><dt>岗位</dt><dd>{html.escape(profile.get('role') or '待补充')}</dd></div>
          <div><dt>最后工作日</dt><dd>{html.escape(profile.get('last_working_day') or '待补充')}</dd></div>
          <div><dt>交接负责人/确认人</dt><dd>{html.escape(handover_coordinator_value({'profile': profile}) or '待补充')}</dd></div>
          <div><dt>接手人</dt><dd>{html.escape(profile.get('successor') or '待补充')}</dd></div>
          <div><dt>行业模板</dt><dd>{html.escape(profile.get('industry') or 'internet')}</dd></div>
          <div><dt>交接包位置</dt><dd><code>{html.escape(manifest.get('output_root', '待补充'))}</code></dd></div>
        </dl>
      </section>

      <section id="start" class="section">
        <div class="section-header">
          <div>
            <h2>从这里开始</h2>
            <p>按这个顺序阅读，接手人可以先掌握范围，再处理仍需要跟进的事项。</p>
          </div>
        </div>
        <ol class="path-list">
          <li><span class="step-no">01</span><h3>确认交接范围</h3><p class="muted">先看入口总览和交接信息，确认人、部门、接手人和最后工作日。</p>{doc_jump('交接信息', '打开交接信息')}</li>
          <li><span class="step-no">02</span><h3>浏览模块总览</h3><p class="muted">看每个专项模块里有多少文件，先判断资料覆盖是否完整。</p>{doc_jump('模块总览', '打开模块总览')}</li>
          <li><span class="step-no">03</span><h3>处理未完事项</h3><p class="muted">把进行中事项、下一步、责任人和风险提醒补齐。</p>{doc_jump('进行中事项总表', '打开事项总表')}</li>
          <li><span class="step-no">04</span><h3>核对高遗漏项</h3><p class="muted">重点核对账号权限、纸质材料、证照、结算和客户关系。</p>{doc_jump('高遗漏检查清单', '打开检查清单')}</li>
        </ol>
      </section>

      <section id="documents" class="section">
        <div class="section-header">
          <div>
            <h2>核心文档</h2>
            <p>这些文档串起交接包的主线，点击后可在下方预览。</p>
          </div>
        </div>
        <div class="doc-grid">{doc_cards}</div>
        <div class="preview-shell document-preview">
          <div class="preview-tabs">{preview_buttons}</div>
          {preview_panels}
        </div>
      </section>

      <section id="file-preview" class="section">
        <div class="section-header">
          <div>
            <h2>文件预览</h2>
            <p>优先在这里快速看内容；需要编辑或查看完整格式时，再打开原文件。</p>
          </div>
        </div>
        <div class="preview-shell">
          <div class="preview-tabs">{file_preview_tabs}</div>
          {file_preview_panels}
        </div>
      </section>

      <section id="modules" class="section">
        <div class="section-header">
          <div>
            <h2>专项交接模块</h2>
            <p>模块用于组织交接内容，Word、PPT、Excel、PDF 只作为文件类型保留。</p>
          </div>
        </div>
        <div class="module-grid">{module_items}</div>
      </section>

      <section id="selection" class="section">
        <div class="section-header">
          <div>
            <h2>筛选结果</h2>
            <p>交接包只复制已纳入的文件；需要确认和未纳入的文件保留在原始目录，并在这里说明原因。</p>
          </div>
        </div>
        <div class="risk-grid">
          <div class="table-panel">
            <div class="table-wrap">
              <table>
                <thead><tr><th>需要确认的文件</th><th>原因</th></tr></thead>
                <tbody>{review_rows}</tbody>
              </table>
            </div>
          </div>
          <div class="table-panel">
            <div class="table-wrap">
              <table>
                <thead><tr><th>未纳入原因</th><th>数量</th></tr></thead>
                <tbody>{excluded_reason_rows}</tbody>
              </table>
            </div>
          </div>
        </div>
        <div class="table-panel selection-examples">
          <div class="table-wrap">
            <table>
              <thead><tr><th>未纳入文件示例</th><th>原因</th></tr></thead>
              <tbody>{excluded_examples_rows}</tbody>
            </table>
          </div>
        </div>
      </section>

      <section id="risks" class="section">
        <div class="section-header">
          <div>
            <h2>风险与待确认</h2>
            <p>先处理资产权限、合规结算、敏感资料和仍不确定的信息。</p>
          </div>
        </div>
        <div class="risk-grid">
          <div class="risk-panel">
            <h3>优先核对</h3>
            <ul class="risk-list">{risky_items}</ul>
          </div>
          <div class="risk-panel">
            <h3>当前假设</h3>
            <ul class="assumption-list">{assumption_items}</ul>
          </div>
        </div>
      </section>

      <section id="large-files" class="section">
        <div class="section-header">
          <div>
            <h2>大文件与重点文件</h2>
            <p>大文件通常承载方案、附件、素材或历史归档，建议优先确认是否需要接手。</p>
          </div>
        </div>
        <div class="table-panel">
          <div class="table-wrap">
            <table>
              <thead><tr><th>分类域</th><th>源文件</th><th>输出位置</th><th>大小</th></tr></thead>
              <tbody>{top_file_rows}</tbody>
            </table>
          </div>
        </div>
      </section>

      <section id="files" class="section">
        <div class="section-header">
          <div>
            <h2>已纳入文件</h2>
            <p>这里只展示已经复制到交接包的文件；需要确认和未纳入的文件请看筛选结果。</p>
          </div>
        </div>
        <div class="toolbar">
          <input id="file-search" type="search" placeholder="搜索文件名、类型、状态、敏感级别">
          <select id="domain-filter"><option value="">全部分类域</option>{domain_options}</select>
          <select id="status-filter"><option value="">全部状态</option>{status_options}</select>
          <select id="sensitivity-filter"><option value="">全部敏感级别</option>{sensitivity_options}</select>
          <button type="button" class="secondary-button" id="clear-filters">清除筛选</button>
        </div>
        <div class="table-panel">
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>分类域</th>
                  <th>源文件</th>
                  <th>输出位置</th>
                  <th>类型</th>
                  <th>范围</th>
                  <th>状态</th>
                  <th>敏感级别</th>
                  <th>大小</th>
                </tr>
              </thead>
              <tbody id="file-table-body">{file_rows_html}</tbody>
            </table>
          </div>
        </div>
        <p id="file-count"></p>
      </section>
    </main>
  </div>
  <script>
    (() => {{
      const searchInput = document.getElementById("file-search");
      const domainFilter = document.getElementById("domain-filter");
      const statusFilter = document.getElementById("status-filter");
      const sensitivityFilter = document.getElementById("sensitivity-filter");
      const clearFilters = document.getElementById("clear-filters");
      const focusSearch = document.getElementById("focus-search");
      const fileRows = Array.from(document.querySelectorAll("#file-table-body tr[data-search]"));
      const fileCount = document.getElementById("file-count");
      const previewTabs = Array.from(document.querySelectorAll(".preview-tab"));
      const previewPanels = Array.from(document.querySelectorAll(".preview-panel"));
      const previewLinks = Array.from(document.querySelectorAll(".md-preview-link"));
      const docJumps = Array.from(document.querySelectorAll("[data-preview-jump]"));
      const filePreviewTabs = Array.from(document.querySelectorAll(".file-preview-tab"));
      const filePreviewPanels = Array.from(document.querySelectorAll(".file-preview-panel"));
      const filePreviewJumps = Array.from(document.querySelectorAll("[data-file-preview-jump]"));
      const domainJumps = Array.from(document.querySelectorAll("[data-domain-jump]"));

      function syncFileRows() {{
        const selectedDomain = domainFilter.value;
        const selectedStatus = statusFilter.value;
        const selectedSensitivity = sensitivityFilter.value;
        const query = (searchInput.value || "").trim().toLowerCase();
        let visible = 0;
        fileRows.forEach((row) => {{
          const matchesDomain = !selectedDomain || row.dataset.domain === selectedDomain;
          const matchesStatus = !selectedStatus || row.dataset.status === selectedStatus;
          const matchesSensitivity = !selectedSensitivity || row.dataset.sensitivity === selectedSensitivity;
          const matchesQuery = !query || row.dataset.search.includes(query);
          const show = matchesDomain && matchesStatus && matchesSensitivity && matchesQuery;
          row.style.display = show ? "" : "none";
          if (show) visible += 1;
        }});
        fileCount.textContent = `当前展示 ${{visible}} / ${{fileRows.length}} 个文件`;
      }}

      function activatePreview(id) {{
        previewTabs.forEach((item) => item.classList.toggle("active", item.dataset.preview === id));
        previewPanels.forEach((panel) => panel.classList.toggle("active", panel.dataset.preview === id));
      }}

      function activateFilePreview(id) {{
        filePreviewTabs.forEach((item) => item.classList.toggle("active", item.dataset.filePreview === id));
        filePreviewPanels.forEach((panel) => panel.classList.toggle("active", panel.dataset.filePreview === id));
      }}

      [searchInput, domainFilter, statusFilter, sensitivityFilter].forEach((control) => {{
        control.addEventListener(control === searchInput ? "input" : "change", syncFileRows);
      }});
      clearFilters.addEventListener("click", () => {{
        searchInput.value = "";
        domainFilter.value = "";
        statusFilter.value = "";
        sensitivityFilter.value = "";
        syncFileRows();
      }});
      focusSearch.addEventListener("click", () => {{
        document.getElementById("files")?.scrollIntoView({{ behavior: "smooth", block: "start" }});
        setTimeout(() => searchInput.focus(), 240);
      }});
      previewTabs.forEach((tab) => {{
        tab.addEventListener("click", () => activatePreview(tab.dataset.preview));
      }});
      previewLinks.forEach((link) => {{
        link.addEventListener("click", (event) => {{
          event.preventDefault();
          activatePreview(link.dataset.previewTarget);
          document.getElementById("documents")?.scrollIntoView({{ behavior: "smooth", block: "start" }});
        }});
      }});
      filePreviewTabs.forEach((tab) => {{
        tab.addEventListener("click", () => activateFilePreview(tab.dataset.filePreview));
      }});
      filePreviewJumps.forEach((jump) => {{
        jump.addEventListener("click", () => {{
          activateFilePreview(jump.dataset.filePreviewJump);
          document.getElementById("file-preview")?.scrollIntoView({{ behavior: "smooth", block: "start" }});
        }});
      }});
      docJumps.forEach((jump) => {{
        jump.addEventListener("click", () => {{
          const id = jump.dataset.previewJump;
          if (id !== undefined) activatePreview(id);
          document.getElementById("documents")?.scrollIntoView({{ behavior: "smooth", block: "start" }});
        }});
      }});
      domainJumps.forEach((jump) => {{
        jump.addEventListener("click", () => {{
          domainFilter.value = jump.dataset.domainJump || "";
          syncFileRows();
          document.getElementById("files")?.scrollIntoView({{ behavior: "smooth", block: "start" }});
        }});
      }});
      if (previewTabs.length) activatePreview(previewTabs[0].dataset.preview);
      if (filePreviewTabs.length) activateFilePreview(filePreviewTabs[0].dataset.filePreview);
      syncFileRows();
    }})();
  </script>
</body>
</html>
"""


def export_zip(target: Path, config: dict[str, Any]) -> Path:
    zip_path = target / config["output"]["zip_name"]
    output_root = target / config["output"]["root_dir"]
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file_path in output_root.rglob("*"):
            if file_path.is_file():
                zf.write(file_path, arcname=str(file_path.relative_to(target)))
    return zip_path


def apply_cli_profile_overrides(config: dict[str, Any], args: argparse.Namespace) -> None:
    mapping = {
        "employee_name": args.employee_name,
        "department": args.department,
        "role": args.role,
        "industry": args.industry,
        "last_working_day": args.last_working_day,
        "handover_owner": args.handover_owner,
        "handover_coordinator": args.handover_coordinator,
        "successor": args.successor,
    }
    for key, value in mapping.items():
        if value:
            config["profile"][key] = value


def apply_cli_gate_overrides(config: dict[str, Any], args: argparse.Namespace) -> None:
    gates = config.setdefault("gates", {})
    gates["source_dir_confirmed"] = True
    if args.profile_confirmed:
        gates["role_confirmed"] = True
    if args.successor_view_confirmed:
        gates["successor_view_confirmed"] = True
    if args.deep_review_complete:
        gates["deep_review_complete"] = True


def bootstrap(target: Path, args: argparse.Namespace) -> dict[str, Any]:
    config, config_path = load_config(target)
    answers, answers_path = load_answers(target)
    existing_manifest, manifest_path = load_manifest(target)
    hidden_dir = target / ".offboarding-handover"
    hidden_dir.mkdir(exist_ok=True)
    apply_cli_profile_overrides(config, args)
    apply_cli_gate_overrides(config, args)
    is_first_run = not config_path.exists()
    config["profile"], assumptions = prompt_profile(config["profile"], args.interactive or is_first_run)
    if (args.interactive or is_first_run) and sys.stdin.isatty() and config["profile"].get("role"):
        config.setdefault("gates", {})["role_confirmed"] = True
    answers, answer_assumptions = prompt_handover_answers(
        answers,
        args.interactive or is_first_run,
        refresh_mode=args.refresh,
    )
    assumptions = merge_assumptions(assumptions, answer_assumptions)
    merge_answers_into_config(config, answers)
    if (
        (args.interactive or is_first_run)
        and sys.stdin.isatty()
        and config["profile"].get("successor")
        and handover_coordinator_value(config)
    ):
        config.setdefault("gates", {})["successor_view_confirmed"] = True
    ensure_output_tree(target, config["output"]["root_dir"])
    write_json(config_path, config)
    write_json(answers_path, answers)

    records: list[dict[str, Any]] = []
    all_records: list[dict[str, Any]] = []
    review_records: list[dict[str, Any]] = []
    excluded_records: list[dict[str, Any]] = []
    if args.refresh and args.no_scan and existing_manifest:
        records = existing_manifest.get("files", [])
        all_records = records
    elif not args.no_scan:
        all_records = apply_relevance_filtering(scan_files(target, config), config)
        included_records, review_records, excluded_records = partition_records(all_records)
        records = stage_records(target, config, included_records, args.stage_mode)

    manifest = build_manifest(target, config, records, assumptions, all_records, review_records, excluded_records)
    overview_path = target / config["output"]["root_dir"] / "00-说明与导航/00-交接总览.md"
    readme_path = target / config["output"]["root_dir"] / "00-说明与导航/01-阅读顺序.md"
    filter_report_path = target / config["output"]["root_dir"] / f"00-说明与导航/{FILTER_REPORT_NAME}"
    handover_info_path = target / config["output"]["root_dir"] / "01-交接信息/00-交接信息.md"
    summary_path = target / config["output"]["root_dir"] / "02-交接总览/00-交接总览.md"
    inflight_summary_path = target / config["output"]["root_dir"] / STATUS_DIR / INFLIGHT_SUMMARY_NAME
    missed_items_path = target / config["output"]["root_dir"] / STATUS_DIR / MISSED_ITEMS_NAME
    conclusion_path = target / config["output"]["root_dir"] / STATUS_DIR / CONCLUSION_NAME
    site_path = target / config["output"]["site_dir"] / "index.html"

    write_json(manifest_path, manifest)
    write_text(overview_path, make_overview_markdown(config, manifest["stats"]))
    write_text(filter_report_path, make_filter_report_markdown(config, manifest))
    write_text(handover_info_path, make_handover_info_markdown(config, answers, assumptions))
    write_text(summary_path, make_summary_markdown(config, manifest))
    write_text(
        readme_path,
        "# 阅读顺序\n\n1. 先读 `00-交接总览.md`\n2. 再看 `01-交接信息` 和 `02-交接总览`\n3. 之后进入 `03-专项交接`\n4. 最后查看 `04-未完事项与状态`\n",
    )
    write_text(inflight_summary_path, make_inflight_summary_markdown(config, records))
    write_text(missed_items_path, make_missed_items_markdown(config, answers))
    write_text(conclusion_path, make_conclusion_markdown(config, manifest, records, answers))
    markdown_previews = build_core_markdown_previews(target, config)
    write_text(site_path, render_site(config, manifest, markdown_previews))
    pruned_dirs: list[str] = []
    if config["features"].get("prune_empty_dirs", True):
        pruned_dirs = prune_empty_directories(target / config["output"]["root_dir"])

    result = {
        "config_path": str(config_path),
        "answers_path": str(answers_path),
        "manifest_path": str(manifest_path),
        "site_path": str(site_path),
        "scanned_files": manifest["stats"]["scanned_files"],
        "staged_files": len(records),
        "review_files": manifest["stats"].get("review_files", 0),
        "excluded_files": manifest["stats"].get("excluded_files", 0),
        "delivery_status": manifest.get("delivery", {}).get("status", "draft"),
        "missing_gates": manifest.get("delivery", {}).get("missing_gates", []),
        "pruned_empty_dirs": pruned_dirs,
    }
    can_export_zip = manifest.get("delivery", {}).get("status") == "polished" or args.allow_draft_zip
    if (args.zip_output or config["features"].get("zip_export")) and can_export_zip:
        result["zip_path"] = str(export_zip(target, config))
    elif args.zip_output or config["features"].get("zip_export"):
        result["zip_skipped_reason"] = "draft-output-needs-confirmation"
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bootstrap and build an offboarding handover scaffold.")
    parser.add_argument("target_dir", help="Directory to initialize")
    parser.add_argument("--interactive", action="store_true", help="Prompt profile fields on first run")
    parser.add_argument("--refresh", action="store_true", help="Refresh existing handover package from saved answers and new prompts")
    parser.add_argument("--no-scan", action="store_true", help="Create scaffold only, do not scan files")
    parser.add_argument(
        "--stage-mode",
        choices=("copy", "none"),
        default="copy",
        help="How to stage files into the output tree",
    )
    parser.add_argument("--zip-output", action="store_true", help="Force zip package export")
    parser.add_argument("--allow-draft-zip", action="store_true", help="Allow zip export even when the package is still a draft")
    parser.add_argument("--profile-confirmed", action="store_true", help="Mark role/profile direction as confirmed by the user")
    parser.add_argument("--successor-view-confirmed", action="store_true", help="Mark successor-facing information needs as confirmed")
    parser.add_argument("--deep-review-complete", action="store_true", help="Mark agent-led deep material review as complete")
    parser.add_argument("--employee-name")
    parser.add_argument("--department")
    parser.add_argument("--role")
    parser.add_argument("--industry")
    parser.add_argument("--last-working-day")
    parser.add_argument("--handover-owner")
    parser.add_argument("--handover-coordinator")
    parser.add_argument("--successor")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    target = Path(args.target_dir).expanduser().resolve()
    if not target.exists() or not target.is_dir():
        raise SystemExit(f"材料文件夹不存在或不是文件夹：{target}")
    result = bootstrap(target, args)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
