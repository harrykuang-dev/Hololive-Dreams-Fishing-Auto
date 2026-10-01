# 1.0.1 Beta 1

这是测试版（Prerelease），不会替代当前正式版 v1.0。软件内部版本为 1.0.1。

## 本次修复

- 修复白雪背景、浅色角色下，准备钓鱼界面被误认成图鉴并自动点击右上角 X 的问题。
- 图鉴判断增加右侧纸张及列表上方连续纸张区域检查；继续保留自动关闭图鉴、奖励和道具详情。
- 不修改拉扯控制算法。

## 验证情况

- 115 项离线测试通过。
- 从本次 EXE 中提取实际打包的识别与导航模块，用 7 张真实截图测试 5 种尺寸，共 35 组通过。涵盖图鉴 X、奖励空白处、道具详情 X、鱼获继续及本次误判的准备界面。
- 上述验证是离线识别及模拟点击决策，不等于游戏实际点击响应或所有场景的实测保证。

## 1.0.0 已知问题及临时方案

正式版显示为 1.0，发布标签为 v1.0，此处称为 1.0.0。

| 问题 | 临时解决／排查方案 | 本 beta 状态 |
|---|---|---|
| 白雪、浅色角色导致准备界面被误认成图鉴，点击 X 退出钓鱼界面 | 手动进入等待咬钩画面后再启动助手，或试用本 beta；若仍误操作请停止 | 已修复识别条件，真实截图回放通过 |
| 开发者模式可能造成周期性卡顿、拉扯跟随不稳 | 日常关闭开发者模式，仅在收集诊断时短时间开启；减少不必要的后台负载 | 未修复，仍需同机对照确认影响 |
| 部分用户遇到 SetCursorPos 错误，运行停止 | 重开游戏和助手，优先普通权限运行；避免锁屏、切换用户和 UAC 提示；远程操作用户尝试本机对照并提供诊断 | 未修复，根因未确认 |

问题细节及诊断限制见 [已知问题文档](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/blob/beta/docs/KNOWN_ISSUES.md)。临时方案不保证解决所有情况。

## 下载与反馈

下载附件 `Hololive-Dreams-Fishing-Auto-v1.0.1.exe`，无需安装 Python。用 `SHA256SUMS-v1.0.1.txt` 核对文件。EXE 尚未进行可信数字签章，Windows 可能显示安全提示。

反馈请通过 [GitHub Issues](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/issues)，注明 beta 版本、角色、游戏语言、分辨率、Windows 缩放及异常阶段。诊断截图可能含有游戏画面，请检查后再分享。

---

## English

This is **1.0.1 Beta 1**, a prerelease on the `beta` branch. It does not replace stable v1.0; the app displays version 1.0.1.

- Fixed the snowy/pale-character fishing preparation screen being mistaken for the encyclopedia and closed via its X.
- Added right-page and continuous paper-header checks. Encyclopedia, reward and item-detail handling remain enabled. Reeling control is unchanged.
- All 115 offline tests passed. The modules extracted from the actual EXE passed 35 real-image navigation checks (seven images at five sizes). These checks do not guarantee live click acceptance or coverage of every scene.

**Known issues in 1.0.0 / v1.0:**

- Preparation-screen misclassification: manually enter the waiting-for-a-bite screen before starting, or try this beta. Fixed here with offline verification.
- Possible Developer-mode reeling stalls: leave Developer mode off for normal use and enable briefly for diagnostics. Not fixed here; same-machine comparison is still needed.
- Reported `SetCursorPos` failures: restart the game and assistant, preferably without elevation; avoid lock-screen/user/UAC transitions and compare local operation if using remote control. Cause unknown and not fixed here.

Download the single EXE and checksum file below. The EXE is unsigned. See [known issues](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/blob/beta/docs/KNOWN_ISSUES.md) and report problems through [Issues](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/issues).
