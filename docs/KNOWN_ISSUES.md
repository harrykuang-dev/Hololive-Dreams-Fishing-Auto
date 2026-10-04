# 已知问题 / Known issues

这里记录已确认或仍在调查的问题和临时解决方案。持续讨论及新的诊断请通过 [GitHub Issues](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/issues) 提交；各版本的修复状态以对应 Release 为准。

## 1.1（发布标签为 v1.1）

- **准备钓鱼界面被误关：已修正。** 本版包含 beta 的准备界面保护，进一步区分图鉴页面结构与关闭 X。
- **Ina 深紫色奖励后无法继续：已修正已知截图。** 本版扩展深色奖励横幅及按钮识别；其他场景或新游戏版本若仍有问题，请提交诊断。
- **TAP 未识别：增加素材字形回退。** 已通过离线回放和角色配色测试，仍不能保证覆盖所有动画、分辨率及实际游戏状态。
- **开发者模式可能增加卡顿：诊断已改为有界后台 JPEG。** 不再在控制循环同步保存大型 PNG；图像采集本身仍有开销，建议日常关闭开发者模式。
- **SetCursorPos 调用失败：保留管理员运行方案。** 遇到此错误时以系统管理员身份执行；本版未改变 Windows 权限要求。
- **开始快捷键被其他程序占用：** 先关闭旧版助手，确认运行记录显示快捷键已就绪，或换一个按键；F12 为 Windows 保留键。快捷键可在助手处于后台时启动，但运行中的游戏需保持前景。

诊断 ZIP 只在启用开发者模式时产生，供用户回报问题，不会自动删除或上传；打包成功后删除已打包原始文件。一般模式不产生常驻启动日志。

以下为旧版问题记录及当时的临时解决方案。1.1 的修复状态以上方说明为准。

## 1.0.0（发布标签为 v1.0）

### 1. 准备钓鱼界面可能被误认成图鉴并关闭

- 状态：已通过用户诊断复现；1.0.1 beta 已修复识别条件。
- 表现：浅色 UI 角色（例如 Fuwawa）可能无法正常自动钓鱼：准备界面的右上角 X 被误认成图鉴关闭按钮，助手点击后退出钓鱼界面。已收到的诊断中，白雪与浅色角色画面触发了该误判；不是已确认的助手进程崩溃。
- 临时方案：更换其他角色；若仍出现误操作，请停止使用并提供诊断。也可试用 1.0.1 beta。
- 验证范围：beta 已通过真实截图离线回放；不代表已覆盖所有角色、场景或游戏动画。

### 2. 开发者模式可能增加拉扯卡顿

- 状态：仍在调查；1.0.1 beta 未修复。
- 证据：一份诊断中截图通常耗时约 58～65 ms，拉扯控制平均约 9 次／秒，并出现 200～350 ms 级别的采样间隔。周期性长间隔与同步诊断图片保存高度吻合，但尚无关闭开发者模式的同机对照，不能断言唯一原因是诊断保存或电脑配置。
- 临时方案：日常使用关闭开发者模式；仅短时间开启以复现和收集问题。保持游戏前台、完整可见，并减少不必要的后台负载。关闭诊断不能保证解决所有失败。

### 3. 部分用户遇到 SetCursorPos 错误后停止

- 状态：已有用户报错截图，根因未确认；1.0.1 beta 未修复。
- 表现：提示 `(0, 'SetCursorPos', 'No error message is available')`，表示移动鼠标调用失败。
- 解决方案：以系统管理员身份执行。

### 4. Ina 的深紫色 UI 导致奖励界面无法自动继续

- 状态：已通过 [Issue #1](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/issues/1) 提供的截图离线复现；1.0.0 和 1.0.1 beta 均受影响，尚未修复。
- 表现：使用 Ina 时，获得漂流金属后可能停留在奖励界面，不自动点击“继续”。现有颜色筛选未完整覆盖深紫色奖励横幅及较暗、低饱和度的按钮，导致画面被判为 `unknown`，未发起续局点击；并非漂流金属物品本身导致。
- 临时方案：手动点击“继续”，或更换其他 UI 配色的角色；若仍无法自动续局，请提供诊断资料及游戏画面。
- 验证范围：已用用户截图在当前源码及 1.0.1 beta EXE 内的识别代码中复现。其他物品、深色主题及动画尚未全面验证。

## English

### 1.0.0 (released as v1.0)

1. **Fishing preparation screen mistaken for the encyclopedia — fixed in 1.0.1 beta.** Snow and pale character art could trigger the old encyclopedia check, causing the assistant to click the preparation screen's X and leave fishing. Light-UI characters such as Fuwawa may be affected. On 1.0.0, switch to another character, or try the beta. Stop if incorrect actions persist. The fix passed real-image offline checks, not exhaustive live testing.
2. **Developer mode may introduce reeling stalls — under investigation, not fixed in this beta.** One session showed roughly nine control updates per second and periodic 200–350 ms sampling gaps consistent with synchronous diagnostic image saving. A same-machine comparison with diagnostics disabled is still needed. Keep Developer mode off for normal use and enable it briefly for reproductions; this is not a guaranteed solution.
3. **SetCursorPos failure stops some sessions — cause unknown, not fixed in this beta.**  Run as administrator.

4. **Ina's dark-purple UI prevents automatic continuation after a material reward — reproduced, not fixed in 1.0.0 or 1.0.1 beta.** The assistant may remain on the reward screen after receiving the drifting-metal material. Current color filters do not fully cover the purple reward strip and dark, low-saturation Continue button, so the screen is classified as `unknown` and no continuation click is attempted. The item itself is not the cause. Temporarily click Continue manually or switch to a character with a different UI color scheme. The screenshot attached to [Issue #1](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/issues/1) reproduces the failure in both the current source and the recognition code bundled in the beta EXE; other items, dark themes and animations have not been exhaustively tested.

Diagnostic images can contain game screenshots. Review them before sharing; the app does not upload them automatically.
