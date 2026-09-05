# 人体、服装、面部和接触控制

## 选择资产，而不是继续堆原始几何体

需要仿真人物时，使用有合理人体拓扑、UV 和可授权来源的角色基础资产。保留原项目场景和人物角色关系，但不要把球体眼睛、圆柱肢体或几何拼接的旧人物当作逼真角色的最终基础。

允许用户已有 `.blend` 中的成熟绑定；导入其它格式前验证当前 Blender 的导入器。不能因文件里有 Armature 就假定蒙皮有效，也不能仅凭骨骼数量认证角色质量。

## MPFB 可选路径

验证过的基线为 MPFB2 2.0.17 源码、Blender/bpy 4.5.3、MakeHuman 核心资产和 default 骨架。

- 源码：https://github.com/makehumancommunity/mpfb2
- 文档：https://static.makehumancommunity.org/mpfb/docs/index.html
- 资产包：https://static.makehumancommunity.org/assets/assetpacks/index.html
- 绑定：https://static.makehumancommunity.org/mpfb/docs/rigging_mesh_assets.html

版本与资产在使用时固定到明确 revision/SHA256。首次理解仓库按宿主要求读 DeepWiki，随后以本地源码签名和实际运行结果为准。

案例中 default rig 实际含 163 根骨骼及眼球、眼睑、下颌、口周骨骼；这不是其它资产的通用数量门槛。源码 macro.json 定义 gender=0 对应 female、1 对应 male；不要盲信可能写反的示例注释。年龄参数为宏观插值，不直接把 0.8 解释为年轻成人。

`blender.rig_mpfb.create_character` 接受任务参数、已核验的源码/资产目录及可选面部目标目录。其职责限于创建基础人体、骨架、权重和资产适配。它不自动保证商业角色美术、所有动作自然或没有穿模。

## 创建合同示例

```python
character = create_character(
    {"id":"user", "body_object":"Char.user.Body", "rig_object":"Char.user.Rig",
     "height":1.72, "position":[0,0,0], "rotation_z":0,
     "phenotype":{"gender":0.0,"age":0.5},
     "assets":[{"kind":"skin","path":"skins/skin-name/skin-name.mhmat"},
               {"kind":"Clothes","path":"clothes/outfit/outfit.mhclo"}],
     "expressions":["eyeBlinkLeft","eyeBlinkRight","mouthSmileLeft","mouthSmileRight"]},
    source_dir=verified_source_src, data_dir=job_runtime,
    asset_dir=verified_asset_root, face_targets_dir=verified_face_targets)
```

路径、外形、服装和族裔参数均由项目决定。这里的占位资源必须替换为已核验素材。模型需要衣服、眼睛、牙齿、眉睫等哪些资产，由镜头用途决定。

## 动作与接触

使用手臂 IK/FK、手腕朝向与手指控制。自动权重只是起点，检查肩肘腕抬起时是否塌陷或拉长。

先调用 `normalize_prop_basis` 规范道具基准，再放置角色和握持目标。历史失败的手机道具带有旧姿态偏移，导致骨骼目标正确而手机仍离开手指。

极向角按实际骨架计算，必要时用 `calibrate_pole` 在有限候选中选取合适角度，再查看图像。不能把一个例子的 -π/2 写死为所有骨架的规则。

接触目标应位于真实表面，且考虑物体尺寸、手掌朝向与关节可达性。对关键指尖设置 IK 后查看是否穿模、反折或所有指头挤在一个位置。小指自然离开机身不等同于握持失败。

## 面部与服装

用头颈、眼球、眼睑、下颌、眉嘴控制骨骼；根据资产加入由控制属性驱动的形态键修正。只创建空控制器或只改对象位置不合格。

需要同时检查：骨骼变换、实际蒙皮变形、修正值，以及睁眼/闭眼和中性/微笑画面。传递表情时，确保眉毛、睫毛、眼睛、牙齿等附属网格也能正确跟随。

服装使用匹配人体的网格和权重。裙摆/头发可使用辅助骨骼；用户明确需要物理模拟时才加入布料/碰撞并烘焙，不能将辅助骨骼称为物理仿真。

`audit_scene.py` 取样检查真实 Armature、有效权重和网格/局部骨骼变化。填入真正会出现不同姿态的 QA 帧，避免只比较循环首尾。结构通过后仍需视觉验收。
