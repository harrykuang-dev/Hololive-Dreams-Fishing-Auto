# 1.1 角色配色逐项验证（2026-10-04）

已收集 **62 名角色的五个色值，共 310 个 RGB 值**。本机解包确认钓鱼 UI 使用角色套色元件；完整角色主资料仍加密，所以色表用 [HolodoriDB 的公开解包 Character 主资料](https://github.com/HolodoriDB/holodori-db-eng-diff/blob/ffc3155067cda6679eaea246eed862e09c9af673/Character.json) 补齐，并核对日文版：62 个角色的五色全部相同。

实际钓鱼控件主矩阵采用 `color4`：本机钓鱼 prefab 的 `CharacterColorSetter._colorType = 3`，`ExecuteColorSetter` 默认背景 `#3D51FF` 与 Tokino Sora 的 `color4` 相符。**这是静态资源推断的映射，尚未在运行中的游戏逐角色确认。** 不把随机模拟色相当作角色配色。

修正前，主色矩阵在 1,674 个离线案例中有 **50 次失败，涉及 10 名角色**。修正后，扩展矩阵 **6,696 个案例全部通过**。

- 角色：62 名。
- 场景：底部按钮、图鉴 X、准备画面 Start、只有准备 X 时不点击、物品详情 X、GET 奖励、奖励继续、TAP、拉线。
- 小窗口压力样例：500×300、900×540、1920×1152。
- 16:9 布局样例：960×540、1280×720、1920×1080。
- 六语言识别设置：zh-CN、zh-TW、en、ja、ko、id，各在 900×540 执行。
- 同时验证目标位置；准备 X 缺少 Start 时应无点击。TAP 与拉线使用共同图案。

**这些是实际 RGB 色值套入既有几何测试画面的离线验证，不是 62 位角色的实机截图。** 按钮测试文字为 NEXT、奖励文字为 GET；六语言测试核对识别设置，不代表六种游戏字形已经逐屏实测。五个颜色字段先做过通用压力扫描，其中白色等辅助字段不应套到有白字的实心按钮；最终主矩阵只使用上述控件主色。尚不能宣称消除所有 UI 问题。

## 本次修正

- Botan 灰色：补充局部灰色候选；奖励条还要与外围亮度不同，整片灰色背景不应判成奖励。
- Nene 等色相分界：X 的色相候选范围适度重叠，避免缩放后分到两个范围。
- Noel、Ina、Zeta 等深色：X 先定位中心字形再检查对角结构，避免缩放使深色细边消失。
- 小窗口深色按钮：排除白边混色形成的连接，继续要求四边白框与字形。
- 灰色 X 与卡片灰边连接：只在灰色候选中容许较粗糙的圆形轮廓，仍检查中央 X 与弹窗纸张。
- 反例：空圆、加号、实心方块、单斜线、均匀灰色背景都不点击。

## 回归证据

- 132 项单元测试通过，其中角色主色覆盖 3,348 个布局案例；另有上述完整矩阵。
- 159 张历史截图与稳定 1.0 的场景、TAP、鱼获判定完全一致。
- 799 帧问题影片回放：24 帧 TAP、一次点击决策；主拉线 325 帧、完整标记 323 帧、追踪 324 帧，保持原结果。
- 新 EXE 包内识别模块另测全部 62 主色的 558 个场景，并保留 Ina 真实截图检查。

## 逐角色结果

“修正前漏项”来自首次主色压力扫描；“通过”表示最终离线矩阵中该角色全部 108 个案例通过。

| 角色 | color1 | color2 | color3 | 控件主色 color4 | color5 | 修正前漏项 | 修正后 |
|---|---|---|---|---|---|---|---|
| Tokino Sora | #6878FF | #FD368A | #FFC942 | #3D51FF | #487DDB | 无 | 108/108 |
| Robocosan | #FF6187 | #FD91B7 | #9355D6 | #EF3964 | #EA51AB | 无 | 108/108 |
| Aki Rosenthal | #ABE64D | #FF4991 | #5E82FF | #8BE100 | #55B29F | 无 | 108/108 |
| Akai Haato | #E5395B | #0046B3 | #FFC85D | #E70D38 | #FE0000 | 无 | 108/108 |
| Shirakami Fubuki | #93D5F2 | #65637F | #6B85ED | #1EB4F5 | #FFFFFF | 无 | 108/108 |
| Natsuiro Matsuri | #FFCB30 | #8DD600 | #FF7D31 | #FFA600 | #FFA401 | 无 | 108/108 |
| Murasaki Shion | #BF57ED | #716EFF | #BFDD00 | #8727B1 | #6342C5 | 无 | 108/108 |
| Nakiri Ayame | #DD305B | #8A6F72 | #E8B532 | #C51743 | #FE0000 | 无 | 108/108 |
| Yuzuki Choco | #FF5487 | #FF85BC | #9956EF | #E72767 | #EA51AB | 无 | 108/108 |
| Oozora Subaru | #E5CE00 | #5CD0DC | #A3CC00 | #DEC000 | #FFF000 | 无 | 108/108 |
| AZKi | #F081A3 | #634C59 | #87D996 | #FA598A | #EA51AB | 无 | 108/108 |
| Ookami Mio | #DB3131 | #575769 | #FFC232 | #BD1616 | #018D39 | 无 | 108/108 |
| Sakura Miko | #FF909E | #DD3654 | #FFD64F | #FF5B70 | #FFBDE1 | 无 | 108/108 |
| Nekomata Okayu | #D866ED | #9A70F3 | #68C8CD | #C843E1 | #6342C5 | 无 | 108/108 |
| Inugami Korone | #FFCD28 | #FF637C | #4BBED1 | #FFBB00 | #FFF000 | 无 | 108/108 |
| Hoshimachi Suisei | #75C0FF | #2B2D80 | #DBBA67 | #269BFF | #487DDB | 无 | 108/108 |
| Usada Pekora | #57A9FF | #97DAEF | #FFC32A | #3E8EFF | #8ECDD8 | 无 | 108/108 |
| Shiranui Flare | #FFAB2D | #4AB0E9 | #FF4D00 | #FF8B10 | #FFA401 | 无 | 108/108 |
| Shirogane Noel | #A5B5B7 | #4F6E8F | #66E6A9 | #363F3C | #FFFFFF | 图鉴 X、详情 X | 108/108 |
| Houshou Marine | #C2153B | #453748 | #EAB759 | #950025 | #FE0000 | 无 | 108/108 |
| Amane Kanata | #8CE6F3 | #2566E9 | #DAC67C | #2BD2EA | #8ECDD8 | 无 | 108/108 |
| Tsunomaki Watame | #E2D065 | #FF8F96 | #D1A287 | #E5C401 | #FFF000 | 无 | 108/108 |
| Tokoyami Towa | #B77FFF | #FC96DC | #B0E22C | #9E59F7 | #B16FD9 | 无 | 108/108 |
| Himemori Luna | #FF93D0 | #99C6FF | #A595FF | #F16BB7 | #FFBDE1 | 无 | 108/108 |
| Yukihana Lamy | #49AAFF | #5CCEFF | #FF8CAE | #1C96FF | #8ECDD8 | 无 | 108/108 |
| Momosuzu Nene | #FFC633 | #FF852D | #FF8CAE | #FFAE00 | #FFA401 | 图鉴 X、详情 X | 108/108 |
| Shishiro Botan | #757575 | #91C1B1 | #5FCFA6 | #5F5F5F | #FFFFFF | 图鉴 X、按钮、详情 X、准备 Start、奖励、奖励继续 | 108/108 |
| Omaru Polka | #ED0043 | #0083EB | #FFCA0F | #D4003C | #FE0000 | 无 | 108/108 |
| La+ Darknesss | #9464D2 | #493A58 | #B8E600 | #7F3DD4 | #6342C5 | 无 | 108/108 |
| Takane Lui | #831550 | #41282E | #ED9492 | #71003D | #FE0000 | 准备 Start | 108/108 |
| Hakui Koyori | #FF95C8 | #52DFCE | #9D6FFF | #F461A8 | #FFBDE1 | 无 | 108/108 |
| Sakamata Chloe | #BC0200 | #2C2B2B | #A8A5A4 | #B22F2D | #FE0000 | 无 | 108/108 |
| Kazama Iroha | #5ECFC8 | #D5C293 | #009BCF | #00C8BE | #55B29F | 无 | 108/108 |
| Ayunda Risu | #FFAAAA | #9F7060 | #FFE085 | #FF7B98 | #FFBDE1 | 无 | 108/108 |
| Moona Hoshinova | #AA83FF | #FAD443 | #78DAE1 | #8454EA | #6342C5 | 无 | 108/108 |
| Airani Iofifteen | #9CDF36 | #FDA2BB | #61D7E4 | #88D414 | #018D39 | 无 | 108/108 |
| Kureiji Ollie | #C40041 | #394452 | #FF85AB | #A10036 | #FE0000 | 无 | 108/108 |
| Anya Melfissa | #F3BF41 | #B3906F | #7E5B5A | #FFB400 | #FFF000 | 无 | 108/108 |
| Pavolia Reine | #004DC2 | #5AC6B6 | #B47BE0 | #003E9D | #487DDB | 无 | 108/108 |
| Vestia Zeta | #9290A1 | #7E95ED | #525C86 | #363449 | #FFFFFF | 图鉴 X、详情 X | 108/108 |
| Kaela Kovalskia | #FC4045 | #54291A | #FFC942 | #AB0B0F | #FE0000 | 无 | 108/108 |
| Kobo Kanaeru | #50CFE1 | #63668E | #FF5559 | #00C0DC | #8ECDD8 | 无 | 108/108 |
| Mori Calliope | #E01C61 | #FF8EB8 | #4C3E46 | #AB003C | #FFBDE1 | 无 | 108/108 |
| Takanashi Kiara | #FF792E | #38D2A8 | #273DCC | #FF5723 | #FFA401 | 无 | 108/108 |
| Ninomae Ina'nis | #5D4E83 | #FF8D35 | #C884CE | #3C3157 | #B16FD9 | 图鉴 X、详情 X、准备 Start | 108/108 |
| Gawr Gura | #5588FF | #8AC7ED | #EF4D55 | #2E63CB | #487DDB | 无 | 108/108 |
| Watson Amelia | #F8DB92 | #7B4439 | #CBB097 | #E6B63F | #FFF000 | 无 | 108/108 |
| IRyS | #DF185D | #60CED0 | #8E00AD | #AB003B | #EA51AB | 无 | 108/108 |
| Ceres Fauna | #B3DD8D | #50D0B3 | #FE9591 | #79B257 | #55B29F | 无 | 108/108 |
| Ouro Kronii | #2221AA | #DCB33E | #8BD2F8 | #29297C | #487DDB | 详情 X、准备 Start | 108/108 |
| Nanashi Mumei | #CCA495 | #41312D | #44BBBB | #906F62 | #8ECDD8 | 详情 X | 108/108 |
| Hakos Baelz | #EE2222 | #48D5C8 | #FFBD15 | #E00000 | #FE0000 | 无 | 108/108 |
| Shiori Novella | #C288F7 | #44445D | #633CFF | #9A43E9 | #FFFFFF | 无 | 108/108 |
| Koseki Bijou | #8674FF | #FFA7CA | #76D6D1 | #5137FF | #6342C5 | 无 | 108/108 |
| Nerissa Ravencroft | #3950EE | #3F3D53 | #A5A5AC | #152CC5 | #487DDB | 无 | 108/108 |
| Fuwawa Abyssgard | #80C2F8 | #F79BC2 | #AA87F5 | #33A1F0 | #8ECDD8 | 无 | 108/108 |
| Mococo Abyssgard | #F79BC2 | #80C2F8 | #AA87F5 | #F168A1 | #FFBDE1 | 无 | 108/108 |
| Hiodoshi Ao | #204596 | #88D3FD | #3272FF | #1E3566 | #487DDB | 图鉴 X、详情 X、准备 Start | 108/108 |
| Otonose Kanade | #FFD380 | #FC8275 | #A1705C | #FFBA35 | #FFF000 | 无 | 108/108 |
| Ichijou Ririka | #FF77A9 | #9D8DFF | #FFB6C8 | #F2558F | #EA51AB | 无 | 108/108 |
| Juufuutei Raden | #357B6C | #D7845A | #A32220 | #144F41 | #018D39 | 图鉴 X、详情 X、准备 Start | 108/108 |
| Todoroki Hajime | #A4AAFF | #DEC2A7 | #84D3FF | #6D77FF | #6342C5 | 无 | 108/108 |

完整案例见同目录 `角色配色测试明细.csv`。源码内可运行：

```powershell
python tools/verify_character_palettes.py palette-results
python -m unittest discover -s tests -q
```
