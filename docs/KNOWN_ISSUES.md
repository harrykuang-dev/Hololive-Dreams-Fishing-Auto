# 已知问题 / Known issues

这里记录已确认或仍在调查的问题和临时解决方案。持续讨论及新的诊断请通过 [GitHub Issues](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/issues) 提交；各版本的修复状态以对应 Release 为准。

## 1.0.0（发布标签为 v1.0）

### 1. 准备钓鱼界面可能被误认成图鉴并关闭

- 状态：已通过用户诊断复现；1.0.1 beta 已修复识别条件。
- 表现：白雪背景和浅色角色可能让准备界面满足旧的图鉴条件，助手点击右上角 X，退出钓鱼界面。不是已确认的助手进程崩溃。
- 临时方案：在 1.0.0 中先手动进入等待咬钩的画面，再启动助手；若仍误操作请停止。也可试用 1.0.1 beta。
- 验证范围：beta 已通过真实截图离线回放；不代表已覆盖所有角色、场景或游戏动画。

### 2. 开发者模式可能增加拉扯卡顿

- 状态：仍在调查；1.0.1 beta 未修复。
- 证据：一份诊断中截图通常耗时约 58～65 ms，拉扯控制平均约 9 次／秒，并出现 200～350 ms 级别的采样间隔。周期性长间隔与同步诊断图片保存高度吻合，但尚无关闭开发者模式的同机对照，不能断言唯一原因是诊断保存或电脑配置。
- 临时方案：日常使用关闭开发者模式；仅短时间开启以复现和收集问题。保持游戏前台、完整可见，并减少不必要的后台负载。关闭诊断不能保证解决所有失败。

### 3. 部分用户遇到 SetCursorPos 错误后停止

- 状态：已有用户报错截图，根因未确认；1.0.1 beta 未修复。
- 表现：提示 `(0, 'SetCursorPos', 'No error message is available')`，表示移动鼠标调用失败，不等同于图像识别失败。
- 临时排查：重新打开游戏和助手，优先让两者都以普通权限运行；不要锁屏、切换用户或在 UAC 提示期间测试。使用远程控制时，尝试在本机操作对照。请提供诊断及报错所处阶段。上述步骤是排查建议，不是保证有效的修复。

### 4. Ina 的深紫色 UI 导致奖励界面无法自动继续

- 状态：已通过 [Issue #1](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/issues/1) 提供的截图离线复现；1.0.0 和 1.0.1 beta 均受影响，尚未修复。
- 表现：使用 Ina 时，获得漂流金属后可能停留在奖励界面，不自动点击“继续”。现有颜色筛选未完整覆盖深紫色奖励横幅及较暗、低饱和度的按钮，导致画面被判为 `unknown`，未发起续局点击；并非漂流金属物品本身导致。
- 临时方案：手动点击“继续”，或更换其他 UI 配色的角色；若仍无法自动续局，请提供诊断资料及游戏画面。
- 验证范围：已用用户截图在当前源码及 1.0.1 beta EXE 内的识别代码中复现。其他物品、深色主题及动画尚未全面验证。

## English

### 1.0.0 (released as v1.0)

1. **Fishing preparation screen mistaken for the encyclopedia — fixed in 1.0.1 beta.** Snow and pale character art could trigger the old encyclopedia check, causing the assistant to click the preparation screen's X and leave fishing. On 1.0.0, manually enter the waiting-for-a-bite screen before starting the assistant, or try the beta. Stop if incorrect actions persist. The fix passed real-image offline checks, not exhaustive live testing.
2. **Developer mode may introduce reeling stalls — under investigation, not fixed in this beta.** One session showed roughly nine control updates per second and periodic 200–350 ms sampling gaps consistent with synchronous diagnostic image saving. A same-machine comparison with diagnostics disabled is still needed. Keep Developer mode off for normal use and enable it briefly for reproductions; this is not a guaranteed solution.
3. **SetCursorPos failure stops some sessions — cause unknown, not fixed in this beta.** Restart the game and assistant, preferably both without elevation. Avoid locking the screen, switching users, or testing during UAC prompts. Compare local operation if remote-control software is involved. Send diagnostics and identify the phase where the error occurs; these are troubleshooting steps, not a confirmed fix.

4. **Ina's dark-purple UI prevents automatic continuation after a material reward — reproduced, not fixed in 1.0.0 or 1.0.1 beta.** The assistant may remain on the reward screen after receiving the drifting-metal material. Current color filters do not fully cover the purple reward strip and dark, low-saturation Continue button, so the screen is classified as `unknown` and no continuation click is attempted. The item itself is not the cause. Temporarily click Continue manually or switch to a character with a different UI color scheme. The screenshot attached to [Issue #1](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/issues/1) reproduces the failure in both the current source and the recognition code bundled in the beta EXE; other items, dark themes and animations have not been exhaustively tested.

Diagnostic images can contain game screenshots. Review them before sharing; the app does not upload them automatically.
