#!/usr/bin/env python3
"""根据 registry 和 snippets 重建 previews，或刷新特效库界面缓存。

用法：
    python3 scripts/build_effects_gallery.py build [--force]
    python3 scripts/build_effects_gallery.py refresh
    python3 scripts/build_effects_gallery.py validate
    python3 scripts/build_effects_gallery.py --effects-dir <目录> build

说明：
    build     读取 registry.json，为每个特效生成/更新 previews/<id>.html。
              若 preview 已存在且非 --force，则跳过。
              预览页会把 snippet 的 style/body/script 内联进 1920x1080 stage，
              注入 GSAP、缩放、循环与素材兜底，实现 gallery 实时预览。
    refresh   重新生成 cache.json，供 index.html 显示刷新时间和特效数量，
              同时附带 build_epoch 用于清理 iframe 缓存。
    validate  检查 registry 中每条记录是否都存在对应 snippet 与 preview。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent

# 预览页模板：把 snippet 内容内联到 1920x1080 stage，注入 GSAP 与循环逻辑。
# 参考 video-studio/assets/style_library/scripts/build_previews.py 的实现。
PREVIEW_WRAPPER = """<!doctype html>
<html>
<head>
<meta charset="utf-8" />
<style>
  html, body {{ margin: 0; overflow: hidden; background: transparent; }}
  #stage {{ position: relative; width: 1920px; height: 1080px; transform-origin: 0 0; overflow: hidden;
    font-family: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
    background:
      radial-gradient(90% 70% at 70% 20%, rgba(62,158,255,.10), transparent 60%),
      radial-gradient(80% 60% at 20% 85%, rgba(77,208,225,.07), transparent 60%),
      linear-gradient(135deg, #161c2a 0%, #0e1320 100%); }}
  .img-fallback {{ background: linear-gradient(135deg, #2a3447, #1b2333) !important;
    display: flex; align-items: center; justify-content: center; }}
{styles}
{extra_css}
</style>
</head>
<body>
<div id="stage">
{body}
</div>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/SplitText.min.js"></script>
{ext_scripts}
<script>
  (function fit() {{
    var s = window.innerWidth / 1920;
    var st = document.getElementById("stage");
    st.style.transform = "scale(" + s + ")";
    document.body.style.height = (1080 * s) + "px";
    window.addEventListener("resize", fit);
  }})();
  // 缺失截图素材兜底为渐变占位（不影响真实 logo 等存在的资产）
  document.querySelectorAll("img").forEach(function (im) {{
    var ph = function () {{ im.classList.add("img-fallback"); im.removeAttribute("src"); }};
    im.addEventListener("error", ph);
    if (im.complete && im.naturalWidth === 0 && im.getAttribute("src")) ph();
  }});
  var tl = gsap.timeline({{ repeat: -1, repeatDelay: 0.5, defaults: {{ ease: "power3.out" }} }});
  var t0 = 0.4;
  var tEnd = 5.4;
  // snippet 通用上下文工具（工程里由 composition 提供，预览页内置）
  function countUp(sel, end, dur, at, decimals, suffix) {{
    var obj = {{ v: 0 }}, el = document.querySelector(sel);
    tl.to(obj, {{ v: end, duration: dur, ease: "power1.out",
      onUpdate: function () {{ el.textContent = obj.v.toFixed(decimals || 0) + (suffix || ""); }} }}, at);
  }}
  if (!window.attachMotionBlur) window.attachMotionBlur = function () {{}};
  try {{
{code}
{extra_js}
  }} catch (e) {{
    document.getElementById("stage").innerHTML =
      '<div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;color:#8b93a3;font-size:40px;font-weight:700">该模式需在工程内预览（' + e.message + '）</div>';
  }}
  // snippet 自带的顶层 timeline 统一循环：paused 的（shader 系）play 起来，
  // 一次性的（const b = gsap.timeline()）也续命循环，预览永不停在退场后的空白态
  gsap.globalTimeline.getChildren(false, false, true).forEach(function (t) {{
    if (t === tl || !t.repeat) return;
    t.repeat(-1); t.repeatDelay(0.8);
    if (t.vars && t.vars.paused) t.play(0);
    // 随机起始相位：避免网格里所有预览同相位循环（同一瞬间集体空白）
    if (t.duration() > 1) t.time(t.duration() * (0.15 + Math.random() * 0.5));
  }});
  // 预览 wrapper 主 timeline 也随机相位
  if (tl.duration() > 1) tl.time(tl.duration() * (0.15 + Math.random() * 0.5));
</script>
</body>
</html>
"""


def get_paths(effects_dir: Path) -> tuple[Path, Path, Path, Path, Path]:
    """返回 registry、snippets、previews、cache、registry_js 五个路径。"""
    registry = effects_dir / "registry.json"
    snippets_dir = effects_dir / "snippets"
    previews_dir = effects_dir / "previews"
    cache_file = effects_dir / "cache.json"
    registry_js = effects_dir / "registry.js"
    return registry, snippets_dir, previews_dir, cache_file, registry_js


def load_registry(registry: Path) -> list[dict]:
    """读取 registry.json 并返回 effects 数组。"""
    if not registry.exists():
        raise FileNotFoundError(f"未找到 registry 文件: {registry}")

    try:
        data = json.loads(registry.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"registry.json 解析失败: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("registry.json 根节点必须是对象")

    effects = data.get("effects")
    if not isinstance(effects, list):
        raise ValueError("registry.json 必须包含 effects 数组")

    return effects


def ensure_dirs(snippets_dir: Path, previews_dir: Path) -> None:
    """确保必要目录存在。"""
    snippets_dir.mkdir(parents=True, exist_ok=True)
    previews_dir.mkdir(parents=True, exist_ok=True)


def preview_for_record(record: dict, snippets_dir: Path, previews_dir: Path) -> Path | None:
    """返回该记录应生成的 preview 文件路径；若记录缺少 id 则返回 None。"""
    effect_id = record.get("id")
    if not effect_id:
        return None
    return previews_dir / f"{effect_id}.html"


def snippet_for_record(record: dict, snippets_dir: Path) -> Path | None:
    """返回该记录对应的 snippet 文件路径。"""
    effect_id = record.get("id")
    if not effect_id:
        return None
    return snippets_dir / f"{effect_id}.html"


def normalize_times(code: str) -> str:
    """把 snippet 内残留的工程绝对起点时间平移到 0.4s（保持多节拍相对间距）。"""
    starts = [float(x) for x in re.findall(r"var t0 = ([\d.]+)", code)]
    if not starts:
        return code
    delta = min(starts) - 0.4
    if delta <= 0:
        return code

    def shift(m):
        return f"{m.group(1)}{max(0.4, float(m.group(2)) - delta):g}"

    code = re.sub(r"(var t0 = )([\d.]+)", shift, code)
    code = re.sub(r"(tEnd = )([\d.]+)", shift, code)
    return code


def _demo_scene(sid: str, title: str, sub: str, grad: str = "linear-gradient(150deg,#2a3550 0%,#1a2238 55%,#10182a 100%)") -> str:
    """通用演示底片：给「叠在画面上才可见」的工具特效一个有内容的背景。"""
    return (
        f'<div id="{sid}" style="position:absolute;inset:0;background:{grad}">'
        '<div style="position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);text-align:center">'
        f"<div style=\"font:800 88px/1.3 'PingFang SC',sans-serif;color:#e8ecf4;letter-spacing:5px\">{title}</div>"
        f"<div style=\"margin-top:16px;font:500 32px/1 'PingFang SC',sans-serif;color:#9fb0c8;letter-spacing:10px\">{sub}</div>"
        "</div></div>"
    )


def _shader_scene(pid: str, bg: str, accent: str, kicker: str, title: str, sub: str) -> str:
    return f"""
  <div id="{pid}-scene" style="position:absolute;inset:0;background:{bg};opacity:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:30px">
    <div style="font:600 30px/1 'PingFang SC',sans-serif;color:{accent};letter-spacing:14px">{kicker}</div>
    <div style="font:800 110px/1.2 'PingFang SC',sans-serif;color:#ffffff;letter-spacing:6px">{title}</div>
    <div style="font:500 26px/1 'PingFang SC',sans-serif;color:#8b93a8;letter-spacing:10px">{sub}</div>
  </div>
  <canvas id="{pid}-canvas" width="1920" height="1080" style="position:absolute;inset:0;opacity:0;display:block"></canvas>"""


SHADER_DEMO_DOM = (
    '<div style="position:absolute;inset:0;background:#07080c"></div>'
    + _shader_scene("wp", "#0a1020", "#3e9eff", "CHAPTER · 01", "横甩切换", "WHIP PAN")
    + _shader_scene("ir", "#120e08", "#ffb224", "CHAPTER · 02", "金圈虹膜", "SDF IRIS")
    + _shader_scene("cz", "#0a1418", "#4dd0e1", "CHAPTER · 03", "变焦转场", "CINEMATIC ZOOM")
    + _shader_scene("fw", "#14101e", "#b388ff", "CHAPTER · 04", "闪白转场", "FLASH WHITE")
)


def _shader_seek(beat_start: float, beat_end: float) -> str:
    """master 是 4 节拍串联：预览只循环播放该 id 自己的节拍窗口。"""
    return (
        'var m = window.__timelines && window.__timelines["shader4"];'
        "if (m) { m.vars.paused = false; m.pause(); "
        f"gsap.fromTo(m, {{ time: {beat_start} }}, {{ time: {beat_end}, "
        f"duration: {beat_end - beat_start}, ease: 'none', repeat: -1, repeatDelay: 0.5 }}); }}"
    )


MBU_DEMO_DOM = (
    '<div id="mbu-demo" style="position:absolute;left:0;top:50%;width:560px;height:200px;'
    "margin-top:-100px;border-radius:24px;background:linear-gradient(135deg,#3e9eff,#4dd0e1);"
    "display:flex;align-items:center;justify-content:center;"
    "font:800 54px/1 'PingFang SC',sans-serif;color:#06121f;letter-spacing:8px\">MOTION BLUR</div>"
)
MBU_DEMO_JS = """
    gsap.set("#mbu-demo", { x: 140 });
    tl.to("#mbu-demo", { x: 1220, duration: 0.9, ease: "power3.inOut" }, 0.5);
    tl.to("#mbu-demo", { x: 140, duration: 0.9, ease: "power3.inOut" }, 2.0);
    tl.to({}, { duration: 0.6 }, 3.0);
    attachMotionBlur("#mbu-demo", tl, { axis: "x", blurMax: 26 });
"""

GRAIN_DEMO_DOM = (
    '<div style="position:absolute;inset:0;background:linear-gradient(160deg,#33415c 0%,#1d2638 60%,#141b2a 100%)"></div>'
    '<div style="position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);text-align:center">'
    "<div style=\"font:800 96px/1.3 'PingFang SC',sans-serif;color:#e8ecf4;letter-spacing:6px\">电影质感画面</div>"
    "<div style=\"margin-top:18px;font:500 34px/1 'PingFang SC',sans-serif;color:#9fb0c8;letter-spacing:12px\">FILM GRAIN + VIGNETTE</div>"
    "</div>"
)

LEAK_DEMO_DOM = (
    '<div style="position:absolute;inset:0;background:linear-gradient(150deg,#2a3550 0%,#1a2238 55%,#10182a 100%)"></div>'
    '<div style="position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);text-align:center">'
    "<div style=\"font:800 96px/1.3 'PingFang SC',sans-serif;color:#e8ecf4;letter-spacing:6px\">情绪回忆画面</div>"
    "<div style=\"margin-top:18px;font:500 34px/1 'PingFang SC',sans-serif;color:#9fb0c8;letter-spacing:12px\">LIGHT LEAK OVERLAY</div>"
    "</div>"
)

PBP_DEMO_DOM = (
    '<div style="position:absolute;inset:0;background:linear-gradient(150deg,#222b40 0%,#161d30 100%)"></div>'
    '<div style="position:absolute;left:620px;top:300px;font:800 44px/1 \'PingFang SC\',sans-serif;color:#e8ecf4">控制台 · API 设置</div>'
    '<div style="position:absolute;left:620px;top:392px;width:480px;height:62px;font:600 30px/62px \'SF Mono\',Menlo,monospace;color:#ffb224;padding-left:18px">sk-your-api-key-here</div>'
    '<div style="position:absolute;left:620px;top:532px;width:480px;height:54px;font:600 30px/54px \'PingFang SC\',sans-serif;color:#9fb0c8;padding-left:18px">user@example.com</div>'
)

_STAGE_FILL_JS = """
    (function () {{
      var st = document.querySelector("{sel}");
      st.innerHTML = '<div style="position:absolute;inset:0;background:linear-gradient(150deg,#26304a 0%,#161d30 100%)">'
        + '<div style="position:absolute;left:8%;top:10%;width:84%;height:80%;border-radius:24px;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.14)"></div>'
        + '<div style="position:absolute;left:50%;top:42%;transform:translate(-50%,-50%);font:800 80px/1.3 sans-serif;color:#e8ecf4;letter-spacing:4px">{label}</div>'
        + '<div style="position:absolute;left:64%;top:24%;padding:12px 28px;border-radius:12px;background:#3e9eff;color:#06121f;font:800 26px/1 sans-serif">目标按钮</div>'
        + '<div style="position:absolute;left:18%;top:66%;padding:14px 30px;border-radius:12px;background:rgba(70,211,144,.2);border:1px solid #46d390;color:#5fe0a8;font:700 24px/1 sans-serif">数据面板 · ¥0.2/次</div>'
        + '</div>';
    }})();
"""

OVERRIDES_SCENE = {
    "letterbox-cinema": _demo_scene("lbx-demo-bg", "情绪叙事画面", "LETTERBOX 2.35:1"),
    "color-wash-mood": _demo_scene("cwm-demo-bg", "底片画面", "COLOR WASH"),
    "spotlight-follow-mask": (
        '<div style="position:absolute;inset:0;background:linear-gradient(150deg,#26304a 0%,#161d30 100%)"></div>'
        '<div style="position:absolute;left:1310px;top:250px;padding:14px 34px;border-radius:14px;background:#3e9eff;color:#06121f;font:800 30px/1 sans-serif">主按钮</div>'
        '<div style="position:absolute;left:280px;top:620px;width:480px;height:270px;border-radius:20px;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.16);'
        'display:flex;align-items:center;justify-content:center;color:#9fb0c8;font:700 30px/1 sans-serif">设置面板</div>'
    ),
    "screen-flash-impact": _demo_scene("sfi-demo-bg", "结果揭晓瞬间", "FLASH IMPACT"),
    "speed-lines-radial": (
        '<div style="position:absolute;inset:0;background:linear-gradient(150deg,#1d2638 0%,#10182a 100%)"></div>'
        '<div style="position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);font:900 130px/1 sans-serif;color:#ffb224;letter-spacing:4px">快？！</div>'
    ),
    "confetti-burst": (
        '<div style="position:absolute;inset:0;background:linear-gradient(150deg,#1d2638 0%,#10182a 100%)"></div>'
        '<div style="position:absolute;left:50%;top:46%;transform:translate(-50%,-50%);padding:40px 90px;border-radius:26px;'
        'background:linear-gradient(135deg,#1c2742,#131a2c);border:2px solid #46d39088;color:#5fe0a8;font:900 72px/1 sans-serif;letter-spacing:4px">审核通过 🎉</div>'
    ),
    "arrow-scribble-pack": (
        '<div style="position:absolute;inset:0;background:linear-gradient(150deg,#222b40 0%,#161d30 100%)"></div>'
        '<div style="position:absolute;left:980px;top:380px;padding:14px 34px;border-radius:14px;background:#3e9eff;color:#06121f;font:800 28px/1 sans-serif">立即开通</div>'
        '<div style="position:absolute;left:1250px;top:280px;color:#e8ecf4;font:800 40px/1 sans-serif">¥0.2 / 次</div>'
        '<div style="position:absolute;left:560px;top:860px;color:#cdd6e6;font:700 34px/1 sans-serif">缓存命中后成本直接打一折</div>'
    ),
    "magnifier-loupe": _demo_scene("mlp-demo-bg", "账单明细页", "MAGNIFIER LOUPE",
                                   "linear-gradient(150deg,#202940 0%,#141b2e 100%)"),
    "marquee-keyword-belt": _demo_scene("mkb-demo-bg", "开场定调画面", "KEYWORD TICKER"),
}

OVERRIDES = {
    "shader-whip-pan": {"body_pre": SHADER_DEMO_DOM, "js": _shader_seek(0.5, 3.85)},
    "shader-sdf-iris": {"body_pre": SHADER_DEMO_DOM, "js": _shader_seek(4.5, 8.0)},
    "shader-cinematic-zoom": {"body_pre": SHADER_DEMO_DOM, "js": _shader_seek(8.5, 12.0)},
    "shader-flash-white": {"body_pre": SHADER_DEMO_DOM, "js": _shader_seek(12.5, 15.9)},
    "motion-blur-util": {"body_pre": MBU_DEMO_DOM, "js": MBU_DEMO_JS},
    "film-grain-vignette": {"body_pre": GRAIN_DEMO_DOM,
                            "css": "#fg-grain { opacity: .18 !important; }"},
    "light-leak-overlay": {"body_pre": LEAK_DEMO_DOM,
                           "css": ".llk-blob { filter: blur(60px) saturate(1.5) brightness(1.6) !important; }"
                                  " #llk-band { filter: blur(34px) brightness(1.5) !important; }"},
    "privacy-blur-patch": {"body_pre": PBP_DEMO_DOM},
    "zoom-punch-rig": {"js": _STAGE_FILL_JS.format(sel="#zpr-stage", label="录屏底片 · 推近强调")},
    "camera-shake-impact": {"js": _STAGE_FILL_JS.format(sel="#csk-stage", label="录屏底片 · 震屏冲击")},
}

for sid, dom in OVERRIDES_SCENE.items():
    OVERRIDES.setdefault(sid, {})["body_pre"] = dom


def extract_snippet_parts(html: str) -> tuple[str, str, str, str]:
    """从 snippet HTML 提取 styles、外部 scripts、inline code、body。"""
    html = re.sub(r"<!--[\s\S]*?-->", "", html)
    styles = "\n".join(re.findall(r"<style>([\s\S]*?)</style>", html))
    ext_scripts = "\n".join(
        f'<script src="{s}"></script>'
        for s in re.findall(r'<script\s+src="([^"]+)"></script>', html)
        if "gsap" not in s
    )
    code = "\n".join(re.findall(r"<script>([\s\S]*?)</script>", html))
    body = re.sub(r"<style>[\s\S]*?</style>|<script[^>]*>[\s\S]*?</script>", "", html).strip()
    return styles, ext_scripts, code, body


def build_previews(
    effects: list[dict],
    effects_dir: Path,
    snippets_dir: Path,
    previews_dir: Path,
    force: bool = False,
    dry_run: bool = False,
) -> tuple[int, int, list[str]]:
    """生成缺失的 preview 文件。

    返回：(创建数, 跳过数, 警告列表)
    """
    created = 0
    skipped = 0
    warnings: list[str] = []

    for record in effects:
        effect_id = record.get("id")
        path = record.get("path")
        if not effect_id:
            warnings.append("存在没有 id 的 registry 记录，已跳过")
            continue

        preview_path = preview_for_record(record, snippets_dir, previews_dir)
        if preview_path is None:
            continue

        if preview_path.exists() and not force:
            skipped += 1
            continue

        # 优先使用 registry.path；若未声明则按 id 推断
        if path:
            snippet_abs = effects_dir / path
        else:
            snippet_abs = snippets_dir / f"{effect_id}.html"
            warnings.append(f"{effect_id}: registry 未声明 path，已按 id 推断 snippet 路径")

        if not snippet_abs.exists():
            warnings.append(f"{effect_id}: snippet 文件不存在 {snippet_abs}")
            continue

        raw = snippet_abs.read_text(encoding="utf-8")
        styles, ext_scripts, code, body = extract_snippet_parts(raw)
        ov = OVERRIDES.get(effect_id, {})
        if ov.get("body_pre"):
            body = ov["body_pre"] + "\n" + body

        html = PREVIEW_WRAPPER.format(
            styles=styles,
            body=body,
            ext_scripts=ext_scripts,
            code=normalize_times(code),
            extra_css=ov.get("css", ""),
            extra_js=ov.get("js", ""),
        )

        if not dry_run:
            preview_path.write_text(html, encoding="utf-8")
        created += 1

    return created, skipped, warnings


def refresh_cache(cache_file: Path, effects: list[dict], dry_run: bool = False) -> dict:
    """写入 cache.json。"""
    now = datetime.now(timezone.utc)
    cache = {
        "built_at": now.isoformat(),
        "build_epoch": int(now.timestamp()),
        "count": len(effects),
        "effects": [
            {
                "id": r.get("id"),
                "name": r.get("name"),
                "category": r.get("category"),
                "path": r.get("path"),
            }
            for r in effects
            if r.get("id")
        ],
    }
    if not dry_run:
        cache_file.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    return cache


def write_registry_js(registry_js: Path, effects: list[dict], cache: dict | None = None, dry_run: bool = False) -> None:
    """生成 registry.js，供 index.html 在 file:// 协议下直接读取。

    浏览器对本地文件限制 fetch，但 <script src> 可以正常加载，
    因此把 registry.json 的内容与缓存元数据写入一个全局变量作为回退数据源。
    """
    payload = {
        "effects": effects,
        "built_at": cache.get("built_at") if cache else None,
        "build_epoch": cache.get("build_epoch") if cache else None,
        "count": len(effects),
    }
    content = f"window.__EFFECTS_REGISTRY__ = {json.dumps(payload, ensure_ascii=False, indent=2)};\n"
    if not dry_run:
        registry_js.write_text(content, encoding="utf-8")


def validate(
    effects: list[dict],
    snippets_dir: Path,
    previews_dir: Path,
) -> tuple[bool, list[str]]:
    """校验每条记录是否都存在 snippet 与 preview。

    返回：(是否全部通过, 问题列表)
    """
    ok = True
    issues: list[str] = []

    for record in effects:
        effect_id = record.get("id")
        if not effect_id:
            issues.append("存在没有 id 的 registry 记录")
            ok = False
            continue

        snippet_path = snippet_for_record(record, snippets_dir)
        preview_path = preview_for_record(record, snippets_dir, previews_dir)

        if snippet_path and not snippet_path.exists():
            issues.append(f"{effect_id}: 缺少 snippet 文件 {snippet_path}")
            ok = False

        if preview_path and not preview_path.exists():
            issues.append(f"{effect_id}: 缺少 preview 文件 {preview_path}")
            ok = False

        if record.get("path") and not record["path"].startswith("snippets/"):
            issues.append(f"{effect_id}: path 建议以 snippets/ 开头，当前为 {record['path']}")
            # 视为警告，不置为失败

    return ok, issues


def cmd_build(args: argparse.Namespace) -> int:
    """build 子命令。"""
    effects_dir = args.effects_dir
    registry, snippets_dir, previews_dir, _, registry_js = get_paths(effects_dir)
    effects = load_registry(registry)
    ensure_dirs(snippets_dir, previews_dir)

    created, skipped, warnings = build_previews(
        effects, effects_dir, snippets_dir, previews_dir, force=args.force, dry_run=args.dry_run
    )
    write_registry_js(registry_js, effects, dry_run=args.dry_run)

    print(f"registry 特效数: {len(effects)}")
    print(f"生成 previews: {created} 个")
    print(f"跳过已存在: {skipped} 个")
    for w in warnings:
        print(f"警告: {w}")
    return 0


def cmd_refresh(args: argparse.Namespace) -> int:
    """refresh 子命令。"""
    registry, _, _, cache_file, registry_js = get_paths(args.effects_dir)
    effects = load_registry(registry)

    cache = refresh_cache(cache_file, effects, dry_run=args.dry_run)
    write_registry_js(registry_js, effects, cache=cache, dry_run=args.dry_run)
    print(f"已刷新界面缓存: {cache_file}")
    print(f"  刷新时间: {cache['built_at']}")
    print(f"  特效数量: {cache['count']}")
    print(f"  已同步生成: {registry_js}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """validate 子命令。"""
    registry, snippets_dir, previews_dir, _, _ = get_paths(args.effects_dir)
    effects = load_registry(registry)
    ok, issues = validate(effects, snippets_dir, previews_dir)

    if ok and not issues:
        print(f"校验通过，共 {len(effects)} 个特效。")
        return 0

    for issue in issues:
        print(f"问题: {issue}")

    if ok:
        print(f"共 {len(effects)} 个特效，存在警告但无阻塞错误。")
        return 0
    print("校验未通过。")
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="根据 registry 和 snippets 重建特效库 previews 或刷新界面缓存。"
    )
    parser.add_argument(
        "--effects-dir",
        type=Path,
        default=SKILL_DIR / "assets" / "effects_library",
        help="特效库目录，默认: assets/effects_library",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只输出计划操作，不写入文件",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    p_build = sub.add_parser("build", help="生成缺失的 previews/<id>.html")
    p_build.add_argument(
        "--force",
        action="store_true",
        help="强制覆盖已存在的 preview",
    )
    p_build.set_defaults(func=cmd_build)

    p_refresh = sub.add_parser("refresh", help="重新生成 cache.json 界面缓存")
    p_refresh.set_defaults(func=cmd_refresh)

    p_validate = sub.add_parser("validate", help="校验 registry、snippets、previews 一致性")
    p_validate.set_defaults(func=cmd_validate)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
