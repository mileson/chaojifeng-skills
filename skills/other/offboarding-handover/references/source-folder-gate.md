# Source Folder Gate

Use this reference at the very beginning of every first-run handover task.

The agent must know where the handover materials are before scanning. If the user starts the skill without a folder path, ask one short question and wait:

`需要交接的材料在哪个文件夹？你可以回复“当前文件夹”，也可以给一个路径。`

## Accepted Answers

- `当前文件夹`: use the current working directory.
- absolute path: expand and validate the path.
- relative path: resolve it against the current working directory, then validate it.

## Validation

Before inventory:

- confirm the path exists
- confirm it is a directory
- confirm it is readable
- show a small top-level preview if useful

If the path is missing, unclear, or unreadable, stop and ask again. Do not infer a folder from nearby paths, recent history, or output folders.

## Do Not Scan These As Source Roots

Do not treat these as the source material folder unless the user explicitly says so:

- an existing `离职交接包`
- `.offboarding-handover`
- `site`
- a ZIP export
- a previous generated handover output directory

## User-Facing Wording

Keep the question plain:

- Good: `需要交接的材料在哪个文件夹？`
- Good: `我可以用当前文件夹，也可以用你给的路径。`
- Avoid: `请传入 target_dir 参数`
- Avoid: `执行 bootstrap_handover.py`
