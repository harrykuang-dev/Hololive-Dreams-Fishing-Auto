# Hololive Fishing Auto

Windows 版《hololive Dreams》釣魚小遊戲自動操作工具。`0.2.5` 新增遊戲語言選擇（簡體中文／繁體中文／自動識別），並以魚獲 GET 卡片確認釣獲及連勝；對已確認的魚獲卡片，即使「繼續」按鈕字形受動畫影響也可按固定卡片位置續關。仍保留嚴格的 TAP 咬鉤核對、小判定格追蹤及低延遲擷取。EXE 包含一鍵開始／停止介面。新建置使用獨立檔名，不覆蓋已有的舊版 EXE。

實機與兩段錄影的檢查詳見 [0.2.0 驗證紀錄](docs/VALIDATION-0.2.0.md)。

0.2.5 簡體中文實機以新版 EXE 連續確認 10 張魚獲 GET 卡片，並通過新圖鑑續關；詳見 [0.2.5 驗證說明](docs/RELEASE-0.2.5.md)。

0.2.1 以使用者提供的漂流金屬截圖驗證：原尺寸、75% 與 50% 均定位右下「繼續」。有繼續按鈕的獎勵優先點按鈕，無按鈕才點空白；上層道具詳情仍優先關閉 X，淡入動畫不提前點擊。55 項回歸測試通過；本次素材畫面尚未另作實機觸發測試。

0.2.2 同時搜尋 X 圓圈的內外輪廓，避免藍色外圈與背景連接時漏識別。使用者提供的圖鑑截圖在原尺寸、75%、50% 均定位右上 X；實機在目前圖鑑畫面一次點擊成功關閉，接著一次按「繼續」進入下一局。此批僅驗證關窗／續局，3 秒上限停止後未接手咬鉤，下一局逾時耗掉一個魚餌，不算拉扯勝率測試。56 項回歸測試通過，並涵蓋沒有 X 的白色圓洞不可誤點。

## EXE 使用方法

0.2.4 結算按鈕需同時具備青藍色按鈕形狀、四側白色外框及內部白色字形，不僅憑色塊判斷。新提供的舊場景錄影全 6,150 幀離線回放：非結算階段的模擬導覽誤點從 5 次降為 0，4 次真實起鉤觸發時刻不變，結算與圖鑑仍可處理。上一段冰面錄影全 1,131 幀亦無 TAP 誤報。66 項測試通過。詳見 [0.2.4 驗證說明](docs/RELEASE-0.2.4.md)；回放模擬不等於實機勝率。

0.2.3 咬鉤需同時辨識粉色提示、白色感嘆號、藍邊 TAP 字形，且連續新鮮影格確認後才點擊，同一提示不重複起鉤。新提供的冰面錄影完整 1,131 幀回放：0.2.2 有 345 幀誤報 TAP，0.2.3 為 0 幀；另外 22 張既有實機 TAP 截圖仍能辨識，3 張獎勵淡入與 2 張浮標特寫不再誤報。63 項回歸測試通過。本次是離線錄影與截圖驗證，未重新宣稱實機勝率。

1. 開啟 `hololive-Dreams` 並進入釣魚畫面。
2. 執行 `Hololive-Fishing-Auto-v0.2.5.exe`，選擇與遊戲相符的語言。
3. 點擊「開始釣魚」。運行紀錄會顯示確定的釣獲和連續成功局數。
4. 如需停止，按 F9、點擊「停止」或切換視窗。

程式辨識短暫出現的 `TAP!`，不僅憑粉色物件判斷咬鉤；會核對感嘆號與 TAP 字形、適應提示淡入縮放／反光，並跨幀確認。只在金色軌道內追蹤魚與黃色判定格。使用判定格上下邊界而非顏色重心，並容許最多 140ms 的短暫遮擋；距離大時長按／放開，靠近魚時用非阻塞快速脈衝並提前煞車。判定格越小，控制死區也會縮小，不再套用固定的大死區。

結算會依畫面關閉新圖鑑右上 X、道具詳情／提示 X、點擊獲得物品視窗的空白位置，再按「繼續／下一步／開始」。結算點擊保持 65ms 並等待畫面切換；沒反應會重試，6 次仍無變化會停止並在介面顯示原因。獎勵淡入期間會等待，避免把紫色物品誤認為 TAP。只有確實辨識的畫面才會點擊，不對未知畫面亂點。

可勾選「儲存本機診斷」記錄狀態畫面及實際時間戳追蹤資料，位於 `%LOCALAPPDATA%\HololiveFishingAuto\sessions\`。不自動錄製影片、不上傳資料。

## 從原始碼啟動 GUI

```powershell
python -m pip install -r requirements-build.txt
python .\gui.py
```

## 建置單一 EXE

```powershell
.\build.ps1
```

輸出位於 `dist\Hololive-Fishing-Auto-v0.2.5.exe`。

## 新版離線回放

```powershell
python tools/replay_recording.py "本機桌面錄影.mp4" sessions/replay --hz 10
python -m unittest discover -s tests -v
```

只分析本機影片，不產生任何遊戲輸入。回放辨識率不是實機勝率。建議遊戲維持 16:9、完整可見；目前實機涵蓋一星與二星魚，未宣稱三星以上或所有魚種 100% 成功。

## 技術與安全界線

只透過螢幕畫面辨識與正常滑鼠輸入操作，不讀取或修改遊戲記憶體、存檔或程序。程式只在標題完全相符的 `hololive-Dreams` 視窗中操作；遊戲失去焦點時會放開滑鼠並停止。

---

## 舊版校準／研究工具

《hololive Dreams》Windows 版的畫面辨識釣魚程式，以下保留舊版通用校準與回放工具說明。
目前完成通用控制器、魚／控制區辨識、單局及有界連續遊玩流程、結果記錄與離線回放。
GUI 版本已根據遊戲內教學與實機畫面完成校準；舊版 profile 工具仍需依其說明自行校準。
本版不附猜測的畫面座標、遊戲素材或可直接執行的假校準檔。沒有本機 profile 時拒絕輸入。

釣魚是 2026-09-29 更新的新功能；官方公告只確認魚種依魚餌、地點及時間而異，未提供完整
按鍵規則：[新區域官方公告](https://www.hololive-dreams.com/en/news/detail/ydwwnk5rrr1p)。
本版控制器針對「按住／放開控制移動區域，追蹤魚圖示」的玩法設計；這個操作假設、軸向、
按住移動方向及辨識模板仍須以遊戲內教學與實際畫面確認。若玩法不同，需修改控制器。

## 安裝與離線檢查

需要 Windows 10/11、Python 3.11+。在專案目錄執行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m fishing_auto --help
```

## 本機校準

先讀遊戲內釣魚說明，確認滑動軸向與按住左鍵的移動方向。以下步驟由使用者在遊戲中操作。
準備相同解析度、僅含遊戲客戶區的 PNG：`playing.png`（正在釣魚）、`success.png`
（明確釣獲結果）、`failure.png`（明確逃脫結果）。若要連續遊玩，另外準備 `ready.png`
（可拋竿）、`waiting.png`（等待咬鉤）、`bite.png`（可起鉤）。可用遊戲截圖或：

```powershell
python -m fishing_auto capture screenshots/playing.png
```

此命令有 5 秒時間讓使用者點選遊戲，只擷取畫面，不點擊遊戲。視窗需在前景、完整可見。

```powershell
python -m fishing_auto calibrate --playing screenshots/playing.png --success screenshots/success.png --failure screenshots/failure.png --axis x --direction 1 --output profiles/local
```

`--axis x` 為橫向，`y` 為縱向；`--direction 1` 表示按住向右／向下，`-1` 向左／向上。
**這些參數是範例，須按實際教學選擇。** 校準視窗會要求框選完整魚活動軌道、魚圖示、
控制區純色內部、收竿按鈕與各狀態專屬的固定標記。用 Enter 接受、Esc 取消。
成功／失敗標記須各自代表真正結果；不選所有畫面共用的確認按鈕。
校準會回測全部來源圖片，模糊或互相混淆的模板不會產生 runnable profile。
校準中途取消後需改用新的輸出資料夾，既有資料不會被覆蓋。

連續模式在上述命令加入 `--auto-cycle --ready screenshots/ready.png --waiting screenshots/waiting.png --bite screenshots/bite.png`。
並需框選拋竿、起鉤、成功／失敗結果的關閉按鈕。只校準當前釣魚流程，不包含地圖導航或魚餌購買。

## 執行

先觀察辨識結果，不輸入左鍵：

```powershell
python -m fishing_auto run --profile profiles/local/profile.json --observe-only --record
```

開始命令後有 5 秒讓使用者點選遊戲。保持遊戲完整在前景，按 **F9** 停止。
先手動進入釣魚，再讓程式接手單局：

```powershell
python -m fishing_auto run --profile profiles/local/profile.json --record
```

連續模式需已完成連續校準：

```powershell
python -m fishing_auto run --profile profiles/local/profile.json --auto-cycle --rounds 20 --record --seconds 600
```

上限 100 局／600 秒，預設一局。失焦、遮擋、視窗移動、過高延遲、無法辨識或 F9 會停止。
缺失追蹤立即放開左鍵，超過 0.25 秒則中止。結果首次出現即放開，跨幀確認後才記成功或失敗。
畫面消失不等於釣獲；未確認局列為 `unconfirmed`，不會用來湊成功率。

`sessions/<時間>/` 包含逐幀 `frames.jsonl`、`summary.json`，選用 MP4 及最後畫面。
每個 JSONL frame 對應一個 MP4 frame；MP4 標稱幀率不是實際擷取幀率，請看時間戳和統計。
observe-only 結果只是觀察到的遊戲結果，不能算作程式釣獲。
實際成功／失敗仍應以錄影檢查模板是否辨識正確。

## 回放與調整

```powershell
python -m fishing_auto replay --profile profiles/local/profile.json --video sessions/某次測試/game.mp4 --timestamps sessions/某次測試/frames.jsonl --output replay.jsonl
python tools/control_benchmark.py --output synthetic-benchmark.json
```

回放只分析本機影片，沒有按鍵輸入。`--timestamps` 保留實際擷取間隔；省略時採 MP4 標稱時基。
合成基準在人工物理模型上搜尋參數、再以不同軌跡驗證；不會寫回 profile 或冒充實機勝率。
控制參數可在本機 profile 的 `control` 中調整，應先用真實錄影檢查失誤，再跑實機批次。
單次連勝僅代表該批測試，不能證明所有魚種、畫面延遲及版本永久 100% 成功。

## 開發狀態

參見 [驗證紀錄](docs/VALIDATION.md)。`0.1.0` 已完成實機規則確認、畫面校準與多輪釣獲測試；遊戲更新、解析度或 UI 配色改變後仍可能需要重新調整。
`profiles/`、`screenshots/`、`sessions/`、遊戲資料及本機路徑不會上傳 GitHub。
只透過畫面與正常滑鼠輸入操作，不修改遊戲、讀取程序記憶體或修改存檔。
