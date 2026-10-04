# Hololive Dreams Auto Fishing

[已知问题与临时解决方案](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/blob/main/docs/KNOWN_ISSUES.md)

[繁體中文](README.md) · [简体中文](README.zh-CN.md) · [English](README.en.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Indonesian](README.id.md)

Windows 版《hololive Dreams》的自动钓鱼助手。通过游戏画面识别与普通鼠标输入，处理咬钩、拉扯、鱼获结算和继续钓鱼；提供简洁的图形界面，无需手动校准即可使用。

## 下载

前往 [GitHub Releases](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/releases/latest)，下载附件中的 `Hololive-Dreams-Fishing-Auto-v1.0.exe`。

只需这一个 EXE，无需安装 Python，也无需另行复制图标或素材。Release 同时提供 SHA-256 校验文件；源码 ZIP 不是可直接运行的软件。


## 功能

- 1.1 开发版新增“鱼饵耗尽时切换无限混合鱼饵”开关，默认关闭。开启后暂停续局，确认耗尽提示，选择带 ∞ 的混合鱼饵并确认；无法确认时停止，请手动处理后重启。
- 自动识别咬钩提示，跟踪鱼与判定区间并控制拉扯。
- 识别“继续／下一步”，关闭新图鉴和物品弹窗，接续钓鱼。
- 支持繁體中文、简体中文、English、日本語、한국어、Indonesian 六种界面语言。切换助手语言不会修改游戏语言。
- 显示钓获计数，支持目标数量，达到目标后停止。
- 每次点击“开始钓鱼”都从零计数；只计确认的鱼获，不计材料或未确认结果，不保存计数。
- 开始快捷键默认 F8，停止快捷键默认 F9；点击各自的设置框后按下新按键或组合键即可自定义。两者不能冲突，长按只启动一次。
- 简约浅色界面、高 DPI 缩放、运行记录，以及可选的本机开发者诊断模式。

## 使用方法

1. 打开游戏，准备鱼饵并进入钓鱼画面。
2. 运行 EXE，在“语言 / Language”中选择与游戏一致的语言。
3. 设置目标数量，`0` 表示不限；如需修改停止快捷键，点击快捷键框并按下要使用的键。
4. 点击“开始钓鱼”。助手会尝试切回游戏；运行时让游戏保持前台且完整可见。
5. 按停止快捷键、点击“停止”，或切换窗口即可停止。再次开始会清零并重新计算目标。

## 使用条件与限制

适用于 Windows 10／11 x64 及 Windows 版游戏。游戏客户区需保持 16:9；运行时不要最小化、遮挡或改变窗口。工具不支持后台钓鱼，也不会自动购买鱼饵、切换地图或补充游戏资源。

识别与操作仍可能受角色配色、动画、分辨率、性能及游戏更新影响；遇到异常请停止并提供诊断。本工具不是官方软件，不读取或修改游戏进程内存、存档或游戏文件。本工具仅供 Python 编程学习、图像识别技术研究交流使用。请自行确认游戏对自动化工具的使用规定，请勿用于破坏游戏生态或任何商业盈利场景，因使用本工具造成的任何问题开发者概不负责。

## 问题反馈与开发者模式

无法继续钓鱼、跟踪异常或其他问题，可通过 [GitHub Issues](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/issues) 联系作者。

勾选“开发者模式”后重现问题，会保存状态截图、鱼获卡片、跟踪数据及耗时，仅存于本机，不自动上传。截图包含游戏画面，启用后会增加性能负担。

点击右侧 `?` 可查看并打开诊断目录：

截图以 JPEG 后台保存，单张不超过 192 KiB，保留最近 64 张事件图及最新画面；追踪 CSV 保留最近两段各 4 MiB。诊断 ZIP 不包含可选录像。

```text
%LOCALAPPDATA%\HololiveFishingAuto\sessions\
```

路径随当前 Windows 账号变化；每次运行会创建以时间命名的文件夹。请提供软件版本、游戏语言／角色、分辨率、Windows 显示缩放、问题描述，以及停止后自动生成的 `diagnostics-YYYY-MM-DD_HH-MM-SS.zip`。分享前请检查截图中是否有不想公开的内容。

## 源码与许可

源码运行、单文件构建和离线测试见 [开发说明](docs/DEVELOPMENT.md)。代码采用 [MIT](LICENSE) 许可；鱼角色及游戏相关权利属于原权利人。
