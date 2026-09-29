# Hololive Fishing Auto

Windows 版《hololive Dreams》釣魚小遊戲自動操作工具。`0.1.0` 已包含經實機校準的圖形介面版本，下載 EXE 後可直接啟動。

## EXE 使用方法

1. 開啟 `hololive-Dreams` 並進入釣魚畫面。
2. 執行 `Hololive-Fishing-Auto.exe`。
3. 點擊「開始釣魚」。
4. 如需停止，點擊「停止」；切換到其他視窗時也會自動安全停止。

程式會辨識短暫出現的 `TAP!`，在拉扯階段以三段式閉環控制操作捲線器：距離大時長按上升或放開下降，靠近魚時快速連點以減少滑塊大幅擺動。釣獲後會自動按「繼續」並等待下一竿。

## 從原始碼啟動 GUI

```powershell
python -m pip install -r requirements-build.txt
python .\gui.py
```

## 建置單一 EXE

```powershell
.\build.ps1
```

輸出位於 `dist\Hololive-Fishing-Auto.exe`。

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
