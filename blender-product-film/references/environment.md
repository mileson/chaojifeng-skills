# 环境准备与平台边界

## 已验证事实

最初的案例机器未发现 Blender 桌面 App。实际执行的是：

```sh
uv run --python 3.11 --with bpy==4.5.3 python <builder.py>
```

这下载/复用了官方 bpy wheel 与其依赖，随后以 Blender 原生引擎保存 `.blend` 并渲染。不要把这个事实描述为已经安装桌面 Blender。

后来同一 bpy 环境实测发现 Apple M5 Pro 的 Metal GPU。该记录证明的是这台 macOS ARM64 机器，不证明其它机器已有可用 GPU。

## 自动准备顺序

1. 执行 doctor；检查用户当前是否已有合适的 Blender、bpy、uv、FFmpeg，以及任务所属进程。
2. 优先复用 job/runtime.json 中可用的运行环境，其次当前机器的 Blender 可执行文件和已有 bpy。
3. 有 uv 时先尝试离线缓存，再在已授权范围内准备兼容 Python/bpy。
4. uv 不存在时，可经 PyPI 安装用户态 uv；不要修改 shell profile。如果 pip 或平台 wheel 不可用，进入官方 portable 路径。
5. 从官方发行页查证 OS、CPU 架构、版本和校验文件，调用 `install_blender_archive.py`。

```sh
python <skill-root>/scripts/install_blender_archive.py --job <job> \
  --url <verified-download.blender.org-url> --sha256 <verified-digest> \
  --checksum-source <official-checksum-page>
```

Windows/Linux 解压到任务运行目录；macOS 以只读方式挂载官方 DMG，复制 App 到任务目录并卸载挂载点。不要覆盖 `/Applications`、用户现有 Blender、配置或插件。

若用户要求打开桌面 App，再使用已准备的应用；操作系统安全提示、管理员权限或许可协议需按宿主规则处理，不能绕过。

## FFmpeg 与可选工具

FFmpeg/ffprobe 是编码和最终验证必需项。先复用 PATH 中的工具；缺失时从 FFmpeg 官方下载页指向的对应平台来源获取，并验证来源/校验信息。没有明确许可时不进行全局包管理器变更。把可执行文件放在任务/用户工具目录，并向子进程显式传 PATH 或绝对路径。

HyperFrames/Remotion 是可选后期。只有任务需要其能力时才准备 Node 和依赖，复用已有项目与 lockfile；依次安装/构建/渲染，不并行开多个浏览器 worker。

内置 ImageGen 由 Codex 宿主提供，不能通过安装 Python 包获得。缺失时说明该能力不可用；可以请求用户启用相应能力或提供素材，不能悄悄改用另一个供应商。

## 资源控制

预检空闲磁盘、内存压力、GPU 可用性和已有任务。估计原生帧文件、模型与下载解压所需空间。每次只允许一个重渲染任务；多角色不等于多进程并行。

代表帧应覆盖人物近景、透明头发、反射和复杂阴影。根据真实耗时估计全片时间。EEVEE 与 Cycles 的采样数不能直接比较；选择通过视觉检查且适合预算的路径。

停止脚本使用任务 STOP 标记，不假定向未连接 TTY 的 stdin 写 Ctrl+C 会停止 Python。宿主需要强制终止时，先确认当前任务保存的 PID 与进程身份，只管理自己启动的进程。

不反复清空全局缓存、不并行下载同一素材、不关闭用户的浏览器或服务。GUI、端口和挂载点不再需要时关闭。

## 官方入口与再验证

- Blender 下载：https://www.blender.org/download/
- 官方发行目录：https://download.blender.org/release/
- bpy 发行：https://pypi.org/project/bpy/
- Python 模块说明：https://docs.blender.org/api/current/info_advanced_blender_as_bpy.html
- uv：https://docs.astral.sh/uv/
- FFmpeg：https://ffmpeg.org/download.html

这些是检索入口，不是永久不变的参数保证。目标平台的实际安装、原生渲染和编码小样未执行时，标记“未验证”，不要宣称跨平台全通过。
