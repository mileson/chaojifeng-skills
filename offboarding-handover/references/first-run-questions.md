# First-Run Questions

Use this reference on the first run after a light folder scan.

The goal is not to interview the user at length. The goal is to eliminate the highest-value unknowns before generating the first HTML site.

The user is answering the skill in natural conversation. The agent may store those answers through internal state files or internal script parameters, but should not assume the user is running commands manually.

## Source Folder Question

Ask this before inventory if the user did not provide a folder:

`需要交接的材料在哪个文件夹？你可以回复“当前文件夹”，也可以给一个路径。`

Do not ask the role/profile questions until the folder exists and the inventory baseline is available.

## Ask These First

1. `这批资料的交接人是谁？有没有常用简称、英文名、花名或文件里常见的别名？`
2. `我推断的岗位/职责边界是否准确？如果不准确，请直接改。`
3. `接手人是谁？`
4. `交接负责人或确认人是谁？`
5. `最后工作日是？如果暂时未知，是否要在草稿里标为“暂未知”？`
6. `这批资料最接近你哪类工作？`
7. `这里面主要是内部资料，还是也包含客户/项目资料？`
8. `有没有还在推进、还没收尾的事？`
9. `有没有账号、权限、设备或敏感资料需要交接？`
10. `是否有其他同事的个人材料、述职、试用期、岗位说明或交接包混在里面？这些默认不放进核心交接包，可以吗？`

## Optional Follow-Ups

Ask only when the folder or first answers suggest risk:

- `如果文件名出现其他同事姓名，哪些属于项目共用材料，哪些应该排除？`
- `同一文档多个版本时，是否默认只保留最终版或最新版本，并把旧版本写入排除说明？`
- `复制进交接包的文件名是否可以按“序号-项目-主题-类型-状态-日期-版本”重命名，同时保留原路径映射？`
- `是否有工作微信、企微、客户群或运营账号需要处理？`
- `是否有纸质材料或手写笔记需要交接？`
- `是否有手机号绑定或验证码链路？`
- `是否有口头约定或非书面规则？`
- `是否有备用金、借款或未核销报销？`
- `是否有群主责任或内容监管责任？`
- `客户关系或对接人是否已经明确移交？`

## Rules

- Prefer single-choice or short factual answers
- Do not ask questions the scan already answered with high confidence
- Stop once the generated site will no longer be full of `待补充`
- A guessed role can only produce a draft. The user must confirm or correct it before polished output.
- Ask these questions only after source folder validation, inventory baseline, trigger handling, synthesis, and coverage check.
- If successor, handover coordinator, last working day, or role boundary remain unknown, the output must stay draft unless the user explicitly marks them intentionally unknown.
- If the user agrees to default behavior, other-person personal materials are excluded, ambiguous shared materials go to `review`, and duplicate versions are collapsed before staging.
