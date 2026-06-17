#!/usr/bin/env python3
"""video-content-factory 自动剪辑脚本。

输入带词级时间戳的转录 JSON，依据 references/clip-edit-rules.md 与
 data/config.yaml 的 clip_edit 配置，输出 edit_decisions.json 与 kept_segments.json。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
DEFAULT_CONFIG = SKILL_DIR / "data" / "config.yaml"

# 常见填充词/短语（按词拆分）。可按项目扩展。
FILLER_PATTERNS: list[list[str]] = [
    ["嗯"],
    ["啊"],
    ["呃"],
    ["那个"],
    ["这个"],
    ["就是"],
    ["然后"],
    ["那么"],
    ["对吧"],
    ["嗯哼"],
    ["的话"],
    ["好像"],
    # 重复型填充
    ["那个", "那个"],
    ["这个", "这个"],
    ["就是", "就是"],
    ["然后", "然后"],
    ["嗯", "那个"],
    ["呃", "那个"],
]

# 文本归一化：去除常见标点和首尾空白，用于比较
_PUNCT_RE = re.compile(r"[\s.。,，!！?？:：;；\"\'\"'`~—–\-\\/\\(\\)\\[\\]\\{\\}]+|")


def _normalize(text: str) -> str:
    return _PUNCT_RE.sub("", text).strip().lower()


def _load_yaml(path: Path | None) -> dict[str, Any]:
    """加载 YAML 配置，失败时返回空字典。"""
    if not path or not path.exists():
        return {}
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover
        print(f"错误：缺少 PyYAML，无法读取配置 {path}: {exc}", file=sys.stderr)
        print("提示：运行 `pip install pyyaml` 或省略 --config 使用内置默认值。", file=sys.stderr)
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data if isinstance(data, dict) else {}
    except Exception as exc:
        print(f"警告：读取配置 {path} 失败：{exc}", file=sys.stderr)
        return {}


def _load_transcript(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _flatten_words(transcript: dict[str, Any]) -> list[dict[str, Any]]:
    """把 segments[].words[] 展平并按 start 排序。"""
    words: list[dict[str, Any]] = []
    for seg in transcript.get("segments", []):
        for w in seg.get("words", []):
            if not isinstance(w, dict):
                continue
            if "start" not in w or "end" not in w:
                continue
            words.append(w)
    words.sort(key=lambda x: (x["start"], x.get("end", x["start"])))
    return words


class EditRules:
    """根据攻击性级别解析出的剪辑参数。"""

    def __init__(self, aggression: str, config: dict[str, Any]) -> None:
        self.aggression = aggression
        clip = config.get("clip_edit", {}) if isinstance(config, dict) else {}

        self.first_guard_ms = int(clip.get("protect_first_word_guard_ms", 120))
        self.last_guard_ms = int(clip.get("protect_last_word_guard_ms", 180))
        self.max_silence_ms = int(clip.get("max_silence_to_cut_ms", 300))

        if aggression == "conservative":
            self.silence_threshold_ms = max(self.max_silence_ms, 1200)
            self.min_adjacent_repeat = 4
            self.filler_enabled = False
            self.false_start_enabled = False
            self.false_start_min_lcp = 999
            self.false_start_max_gap_words = 0
            self.false_start_max_duration_ms = 0
            self.false_start_max_extra_words = 0
        elif aggression == "aggressive":
            self.silence_threshold_ms = max(self.max_silence_ms - 300, 300)
            self.min_adjacent_repeat = 2
            self.filler_enabled = True
            self.false_start_enabled = True
            self.false_start_min_lcp = 3
            self.false_start_max_gap_words = 8
            self.false_start_max_duration_ms = 4000
            self.false_start_max_extra_words = 3
        else:  # standard
            self.silence_threshold_ms = self.max_silence_ms
            self.min_adjacent_repeat = 2
            self.filler_enabled = True
            self.false_start_enabled = True
            self.false_start_min_lcp = 4
            self.false_start_max_gap_words = 6
            self.false_start_max_duration_ms = 3000
            self.false_start_max_extra_words = 2


def _detect_silence_cuts(words: list[dict[str, Any]], rules: EditRules) -> list[tuple[int, int, str]]:
    """检测相邻词之间的过长静音并返回删除区间（毫秒）。"""
    cuts: list[tuple[int, int, str]] = []
    for i in range(len(words) - 1):
        prev_end = int(words[i]["end"] * 1000)
        next_start = int(words[i + 1]["start"] * 1000)
        gap = next_start - prev_end
        if gap > rules.silence_threshold_ms:
            cuts.append((prev_end, next_start, f"长静音 {gap / 1000:.2f}s"))
    return cuts


def _detect_adjacent_repeat_cuts(words: list[dict[str, Any]], rules: EditRules) -> list[tuple[int, int, str]]:
    """检测相邻重复词/短语并删除较早出现。"""
    if rules.min_adjacent_repeat <= 0:
        return []
    cuts: list[tuple[int, int, str]] = []
    n = len(words)
    max_n = min(n // 2, 6)
    # 从较长重复序列优先检测
    for length in range(max_n, rules.min_adjacent_repeat - 1, -1):
        i = 0
        while i + 2 * length <= n:
            texts_a = [_normalize(words[i + k]["word"]) for k in range(length)]
            texts_b = [_normalize(words[i + length + k]["word"]) for k in range(length)]
            if texts_a and texts_a == texts_b and all(texts_a):
                start_ms = int(words[i]["start"] * 1000)
                end_ms = int(words[i + length]["start"] * 1000)
                cuts.append((start_ms, end_ms, f"重复口误（连续 {length} 词）"))
                i += 2 * length  # 跳过已处理区域
            else:
                i += 1
    return cuts


def _detect_false_start_cuts(words: list[dict[str, Any]], rules: EditRules) -> list[tuple[int, int, str]]:
    """检测非紧邻的立即重述（false start）：短片段后被更完整表达重复。"""
    if not rules.false_start_enabled:
        return []
    cuts: list[tuple[int, int, str]] = []
    n = len(words)
    max_lcp = 12
    for i in range(n):
        max_j = min(n, i + rules.false_start_max_gap_words + 1)
        for j in range(i + 1, max_j):
            lcp = 0
            while (
                lcp < max_lcp
                and i + lcp < n
                and j + lcp < n
                and _normalize(words[i + lcp]["word"])
                and _normalize(words[i + lcp]["word"]) == _normalize(words[j + lcp]["word"])
            ):
                lcp += 1
            if lcp < rules.false_start_min_lcp:
                continue
            first_segment_words = j - i
            extra_words = first_segment_words - lcp
            if extra_words > rules.false_start_max_extra_words:
                continue
            duration_ms = int(words[j]["start"] * 1000) - int(words[i]["start"] * 1000)
            if duration_ms > rules.false_start_max_duration_ms:
                continue
            start_ms = int(words[i]["start"] * 1000)
            end_ms = int(words[j]["start"] * 1000)
            cuts.append((start_ms, end_ms, "立即重述口误"))
            break  # 每个 i 只取最靠前的匹配，避免过度删除
    return cuts


def _detect_filler_cuts(words: list[dict[str, Any]], rules: EditRules) -> list[tuple[int, int, str]]:
    """检测填充词/短语。"""
    if not rules.filler_enabled:
        return []
    cuts: list[tuple[int, int, str]] = []
    n = len(words)
    i = 0
    while i < n:
        matched = False
        for pattern in FILLER_PATTERNS:
            if i + len(pattern) > n:
                continue
            if all(
                _normalize(words[i + k]["word"]) == _normalize(pattern[k])
                for k in range(len(pattern))
            ):
                start_ms = int(words[i]["start"] * 1000)
                end_ms = int(words[i + len(pattern) - 1]["end"] * 1000)
                cuts.append((start_ms, end_ms, f"填充词：{''.join(pattern)}"))
                i += len(pattern)
                matched = True
                break
        if not matched:
            i += 1
    return cuts


def _merge_intervals(intervals: list[tuple[int, int, str]], min_gap_ms: int = 50) -> list[tuple[int, int, str]]:
    """合并重叠或相邻（间隔小于 min_gap_ms）的区间，原因合并为第一条。"""
    if not intervals:
        return []
    sorted_intervals = sorted(intervals, key=lambda x: (x[0], x[1]))
    merged: list[tuple[int, int, str]] = [sorted_intervals[0]]
    for start, end, reason in sorted_intervals[1:]:
        last_start, last_end, last_reason = merged[-1]
        if start <= last_end + min_gap_ms:
            new_reason = last_reason if last_reason == reason else f"{last_reason}; {reason}"
            merged[-1] = (last_start, max(last_end, end), new_reason)
        else:
            merged.append((start, end, reason))
    return merged


def _intervals_to_keep_segments(
    words: list[dict[str, Any]],
    cut_intervals: list[tuple[int, int, str]],
    rules: EditRules,
    source_duration_ms: int,
) -> list[dict[str, Any]]:
    """根据删除区间生成保留区间，并应用边界保护。"""
    # 初始保留区间 = 删除区间之外的部分
    keep: list[dict[str, Any]] = []
    current_start = 0
    for cut_start, cut_end, _reason in cut_intervals:
        if current_start < cut_start:
            keep.append({"start_ms": current_start, "end_ms": cut_start})
        current_start = max(current_start, cut_end)
    if current_start < source_duration_ms:
        keep.append({"start_ms": current_start, "end_ms": source_duration_ms})

    # 应用边界保护
    guarded: list[dict[str, Any]] = []
    for idx, seg in enumerate(keep):
        start_ms = seg["start_ms"]
        end_ms = seg["end_ms"]

        # 句首保护：如果前面是删除段或视频起点
        if idx == 0:
            new_start = max(0, start_ms - rules.first_guard_ms)
        else:
            new_start = max(keep[idx - 1]["end_ms"], start_ms - rules.first_guard_ms)
        # 句尾保护：如果后面是删除段或视频终点
        if idx == len(keep) - 1:
            new_end = min(source_duration_ms, end_ms + rules.last_guard_ms)
        else:
            new_end = min(keep[idx + 1]["start_ms"], end_ms + rules.last_guard_ms)

        guarded.append({"start_ms": new_start, "end_ms": new_end})

    # 合并可能因保护而重叠的保留段
    merged: list[dict[str, Any]] = []
    for seg in guarded:
        if merged and seg["start_ms"] <= merged[-1]["end_ms"]:
            merged[-1]["end_ms"] = max(merged[-1]["end_ms"], seg["end_ms"])
        else:
            merged.append(seg.copy())

    # 合并相邻保留段之间的微小间隙（<250ms），避免跳切和黑场
    MIN_KEEP_GAP_MS = 250
    compact: list[dict[str, Any]] = []
    for seg in sorted(merged, key=lambda x: x["start_ms"]):
        if compact and seg["start_ms"] - compact[-1]["end_ms"] < MIN_KEEP_GAP_MS:
            compact[-1]["end_ms"] = max(compact[-1]["end_ms"], seg["end_ms"])
        else:
            compact.append(seg.copy())
    merged = compact

    # 收集每个保留段包含的词与文本
    for seg in merged:
        seg_words = [
            w for w in words
            if int(w["end"] * 1000) > seg["start_ms"] and int(w["start"] * 1000) < seg["end_ms"]
        ]
        seg["words"] = seg_words
        seg["text"] = "".join(w.get("word", "") for w in seg_words)

    return merged


def _build_decisions(
    cut_intervals: list[tuple[int, int, str]],
    keep_segments: list[dict[str, Any]],
    source_duration_ms: int,
) -> list[dict[str, Any]]:
    """把删除段与保留段合并成按时间排序的决策列表。"""
    events: list[dict[str, Any]] = []
    for start, end, reason in cut_intervals:
        events.append({
            "type": "cut",
            "source_start_ms": start,
            "source_end_ms": end,
            "reason": reason,
        })
    output_ms = 0
    for seg in keep_segments:
        duration = seg["end_ms"] - seg["start_ms"]
        events.append({
            "type": "keep",
            "source_start_ms": seg["start_ms"],
            "source_end_ms": seg["end_ms"],
            "output_start_ms": output_ms,
            "output_end_ms": output_ms + duration,
            "text": seg.get("text", ""),
            "reason": "保留",
        })
        output_ms += duration

    events.sort(key=lambda x: (x["source_start_ms"], 0 if x["type"] == "cut" else 1))

    # 验证覆盖完整时间轴
    last_end = 0
    for ev in events:
        if ev["source_start_ms"] != last_end:
            # 填充微小缝隙（通常由毫秒取整造成）
            events.append({
                "type": "keep",
                "source_start_ms": last_end,
                "source_end_ms": ev["source_start_ms"],
                "output_start_ms": output_ms,
                "output_end_ms": output_ms,
                "text": "",
                "reason": "保留（缝隙填充）",
            })
        last_end = ev["source_end_ms"]
    if last_end < source_duration_ms:
        events.append({
            "type": "keep",
            "source_start_ms": last_end,
            "source_end_ms": source_duration_ms,
            "output_start_ms": output_ms,
            "output_end_ms": output_ms,
            "text": "",
            "reason": "保留（缝隙填充）",
        })

    events.sort(key=lambda x: (x["source_start_ms"], 0 if x["type"] == "cut" else 1))
    return events


def _build_mapping(decisions: list[dict[str, Any]]) -> list[dict[str, int]]:
    """生成原片时间到成片时间的映射关键点。"""
    mapping: list[dict[str, int]] = []
    for d in decisions:
        if d["type"] == "keep":
            mapping.append({
                "source_ms": d["source_start_ms"],
                "output_ms": d["output_start_ms"],
            })
            mapping.append({
                "source_ms": d["source_end_ms"],
                "output_ms": d["output_end_ms"],
            })
    # 去重并排序
    seen = set()
    unique = []
    for m in mapping:
        key = (m["source_ms"], m["output_ms"])
        if key not in seen:
            seen.add(key)
            unique.append(m)
    unique.sort(key=lambda x: x["source_ms"])
    return unique


def auto_edit(
    transcript: dict[str, Any],
    config: dict[str, Any],
    aggression: str,
    video_duration_ms: int | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """执行自动剪辑，返回 (edit_decisions, kept_segments)。"""
    rules = EditRules(aggression, config)
    words = _flatten_words(transcript)

    if video_duration_ms is None:
        video_duration_ms = int(transcript.get("duration", 0) * 1000)
    if not video_duration_ms and words:
        video_duration_ms = int(words[-1]["end"] * 1000)
    if video_duration_ms <= 0:
        raise ValueError("无法确定视频时长，请提供 --video-duration 或在转录 JSON 中包含 duration。")

    # 收集各类删除区间
    cuts: list[tuple[int, int, str]] = []
    cuts.extend(_detect_silence_cuts(words, rules))
    cuts.extend(_detect_adjacent_repeat_cuts(words, rules))
    cuts.extend(_detect_false_start_cuts(words, rules))
    cuts.extend(_detect_filler_cuts(words, rules))

    cut_intervals = _merge_intervals(cuts)

    # 裁剪删除区间不超出视频边界
    cut_intervals = [
        (max(0, s), min(video_duration_ms, e), r) for s, e, r in cut_intervals
    ]
    cut_intervals = [c for c in cut_intervals if c[0] < c[1]]

    keep_segments = _intervals_to_keep_segments(words, cut_intervals, rules, video_duration_ms)

    decisions = _build_decisions(cut_intervals, keep_segments, video_duration_ms)
    mapping = _build_mapping(decisions)

    edit_decisions = {
        "source_duration_ms": video_duration_ms,
        "aggression": aggression,
        "rules_version": "1.0",
        "decisions": decisions,
        "source_to_output_mapping": mapping,
    }

    kept_segments = {
        "source_duration_ms": video_duration_ms,
        "aggression": aggression,
        "segments": [
            {
                "start_ms": seg["start_ms"],
                "end_ms": seg["end_ms"],
                "text": seg.get("text", ""),
                "words": seg.get("words", []),
            }
            for seg in keep_segments
        ],
    }

    return edit_decisions, kept_segments


def main() -> int:
    parser = argparse.ArgumentParser(
        description="video-content-factory 自动剪辑：从转录 JSON 生成剪辑决策与保留段。"
    )
    parser.add_argument(
        "--input", "-i",
        type=Path,
        required=True,
        help="输入转录 JSON 路径（包含 segments[].words[]）。",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=Path("edit_decisions.json"),
        help="输出 edit_decisions.json 路径（默认：./edit_decisions.json）。",
    )
    parser.add_argument(
        "--kept", "-k",
        type=Path,
        default=Path("kept_segments.json"),
        help="输出 kept_segments.json 路径（默认：./kept_segments.json）。",
    )
    parser.add_argument(
        "--aggression", "-a",
        choices=["conservative", "standard", "aggressive"],
        default=None,
        help="剪辑攻击性级别（默认从 config.yaml 读取，否则 standard）。",
    )
    parser.add_argument(
        "--config", "-c",
        type=Path,
        default=DEFAULT_CONFIG,
        help="配置文件路径（默认：data/config.yaml）。",
    )
    parser.add_argument(
        "--video-duration", "-d",
        type=float,
        default=None,
        help="视频总时长（秒），覆盖转录 JSON 中的 duration。",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="以缩进格式输出 JSON。",
    )

    args = parser.parse_args()

    if not args.input.exists():
        print(f"错误：输入文件不存在：{args.input}", file=sys.stderr)
        return 1

    config = _load_yaml(args.config)
    clip_config = config.get("clip_edit", {}) if isinstance(config, dict) else {}

    aggression = args.aggression or clip_config.get("default_aggression") or "standard"
    if aggression not in ("conservative", "standard", "aggressive"):
        print(f"警告：未知的攻击性级别 '{aggression}'，回退到 standard。", file=sys.stderr)
        aggression = "standard"

    try:
        transcript = _load_transcript(args.input)
    except json.JSONDecodeError as exc:
        print(f"错误：无法解析转录 JSON：{exc}", file=sys.stderr)
        return 1

    video_duration_ms = None
    if args.video_duration is not None:
        video_duration_ms = int(args.video_duration * 1000)

    try:
        edit_decisions, kept_segments = auto_edit(
            transcript, config, aggression, video_duration_ms=video_duration_ms
        )
    except ValueError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1

    indent = 2 if args.pretty else None
    args.output.write_text(json.dumps(edit_decisions, ensure_ascii=False, indent=indent), encoding="utf-8")
    args.kept.write_text(json.dumps(kept_segments, ensure_ascii=False, indent=indent), encoding="utf-8")

    kept_count = len(kept_segments["segments"])
    cut_count = sum(1 for d in edit_decisions["decisions"] if d["type"] == "cut")
    print(f"剪辑完成：aggression={aggression}")
    print(f"  保留段：{kept_count} 个")
    print(f"  删除段：{cut_count} 个")
    print(f"  输出：{args.output}")
    print(f"  输出：{args.kept}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
