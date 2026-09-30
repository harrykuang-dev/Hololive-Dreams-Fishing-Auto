# 1.0 — 輸入操作與像素圖標

## 下載與使用

下載本頁附件 `Hololive-Fishing-Auto-v1.0.exe` 即可使用，無需安裝 Python 或另外複製素材。支援 Windows 10／11 x64；遊戲需在前景，客戶區維持 16:9。

使用說明：[繁體中文](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/blob/main/README.md) · [简体中文](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/blob/main/README.zh-CN.md) · [English](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/blob/main/README.en.md) · [日本語](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/blob/main/README.ja.md) · [한국어](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/blob/main/README.ko.md) · [Indonesian](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/blob/main/README.id.md)。

`SHA256SUMS.txt` 可核對 EXE 的 SHA-256。下載後可在 PowerShell 執行 `Get-FileHash .\Hololive-Fishing-Auto-v1.0.exe -Algorithm SHA256` 並比較結果。

## 主要內容

本次不修改拉扯算法、辨識邏輯或預設控制參數，保留高 DPI 和魚獲計數，目標改為每次開始獨立計算。

- 語言選擇標籤改為「語言 / Language」「语言 / Language」「言語 / Language」「Bahasa / Language」「언어 / Language」；英文介面只顯示「Language」。
- 目標釣魚數量改為普通輸入框，移除右側增減箭頭；仍驗證非負整數，0 代表不限。
- 每次有效點擊「開始釣魚」都將計數歸零，重新釣到設定目標。達標後可直接重新開始，不要求提高目標；手動停止後再開始也歸零。運行中開始按鈕停用，重複啟動請求不會清除當前計數。
- 停止快捷鍵預設 F9。只有點擊設定框才進入綁定，直接按鍵即完成；已完成後再次點擊可修改，切回視窗或重新取得焦點不會自動重綁。點其他地方或失去焦點取消未完成的設定。可用功能鍵、字母／數字、常見導覽鍵、標點及 Ctrl／Alt／Shift 組合。單獨按修飾鍵不會改設定；运行期間鎖定快捷鍵設定。
- 移除外層頁面捲動條，僅保留運行記錄的捲動條。高 DPI／短螢幕改以縮減垂直留白保留控件與日誌，不縮小文字。移除介面的計數不保存提示句，計數仍保持重啟歸零。
- 開發者模式右側 ? 改為較小字體和緊湊按鈕。「診斷資料位於：」下的路徑可點擊開啟本機資料夾；首次使用若資料夾不存在會先建立空資料夾，再開啟檔案總管。「項目地址：」下的網址可點擊，以預設瀏覽器開啟專案 GitHub。移除固定／本機帳戶的路徑解釋句；路徑仍由目前電腦的 `LOCALAPPDATA` 取得。
- 開發者模式說明採用使用者確認的文字：用於定位與排查異常，每次運行建立時間命名的資料夾，可透過項目地址聯繫作者並提供問題描述及診斷資料，且明確提示效能負擔。六種語言同步更新，兩個地址仍可點擊。
- 以提供的海盜魚製作靜態像素風圖標（不是安裝 ChatGPT 寵物），以 32×32 可辨識為目標，保留紅色魚身、紫金海盜帽、眼睛、紫色嘴唇與魚鰭，去除魚身細碎心形／船錨裝飾。帽徽按使用者確認改為箭穿黑白兩半的愛心，不是骷髏頭或星球。ICO 內建 16／20／24／28／32／40／48／56／60／64／72／80／96／128／256 像素，補齊中間 DPI 尺寸；採最近鄰縮放，避免像素邊緣被平滑。視窗、說明視窗與 EXE 統一使用 `assets/fish-clear.ico`，原圖和舊版素材保留。
- 視窗、EXE 檔名和版本字串均標記為 1.0（Windows 數值版本 1.0.0.0）。
- README 改為軟件介紹與使用指南，不再列出各版更新；提供繁體中文、简体中文、English、日本語、한국어、Indonesian 六種說明。版本變更放在 Release Notes，建置／研究工具說明移至開發文件。

單檔輸出：`dist/Hololive-Fishing-Auto-v1.0.exe`；無需另外提供 Python 或素材。

## 驗證範圍

114 項離線／模擬運行測試，包含六種語言、100／125／150／200% DPI 控件佈局、等高操作按鈕、小尺寸問號、無增減箭頭的輸入框、單次點擊綁定及再次點擊修改／取消、组合鍵及鎖定設定、預設 F9、計數與目標流程、不同帳戶的診斷目錄、確認文字逐字核對、點擊診斷／專案地址、首次建立診斷目錄及錯誤處理、只保留日誌捲動條、ICO 各尺寸與透明度、圖標打包可重現性，以及六種 README 的覆蓋與連結核對。

另檢視 16／32／48 像素圖標轉出的 PNG；非實體螢幕截圖驗收，未操作遊戲或重新測試釣魚勝率。
