# 1.1 — 辨識改善、開始快捷鍵與精簡診斷

本版以 **1.0** 為基準，整合主要功能與修正。

## 遊戲 UI 辨識

- 改善不同角色配色下的辨識，涵蓋深紫色獎勵橫幅、較暗的「繼續」按鈕及圖鑑關閉 X，修正 Ina 領取材料後無法自動續局的已知情況。
- 加強準備釣魚畫面與圖鑑的結構區分，避免把開始釣魚畫面的 X 當成圖鑑 X，誤操作退出釣魚。
- 參考 hololive-toolkit 解包研究取得的遊戲素材，新增 TAP 字形辨識回退，改善原有辨識條件未命中的咬鉤提示。

## 開始與停止快捷鍵

- 新增可自訂的**開始快捷鍵**，預設 **F8**；停止快捷鍵維持 **F9**，兩者皆可改成按鍵或組合鍵。
- 遊戲在前景、助手在背景時可直接按開始快捷鍵啟動；運行記錄會顯示快捷鍵是否註冊成功、啟動來源與連接階段，方便判斷問題。

## 更輕量的診斷資料

- 截圖改為背景儲存的壓縮 JPEG，單張最多 **192 KiB**、寬度最多 1280 像素，取代原先約 2 MB 的 PNG；保留最近 64 張事件截圖及最新畫面。
- 圖片佇列與追蹤記錄皆設有上限，降低診斷寫入對拉扯控制的干擾。
- 每次運行使用日期時間命名的資料夾，停止後自動產生 `diagnostics-YYYY-MM-DD_HH-MM-SS.zip`。驗證打包成功後刪除已打包原始檔，只需提供 ZIP 即可回報；打包失敗則保留原始檔。
- 一般模式不寫入常駐啟動日誌；開發者模式的連接記錄併入診斷 ZIP。診斷只存於本機，不會自動上傳。

## 簡化點擊定位

TAP 咬鉤和拉扯期間使用遊戲客戶區內的現有滑鼠位置，必要時使用畫面中央，移除固定底部的操作點。這兩個階段可在畫面任意位置點擊；選單與結算按鈕仍按實際位置操作。

## 下載與使用

下載 **`Hololive-Dreams-Fishing-Auto-v1.1.exe`** 即可使用，無需安裝 Python。`SHA256SUMS.txt` 提供 EXE 與源碼 ZIP 的 SHA-256 校驗。

請先關閉舊版助手，完成設定並進入遊戲釣魚畫面，再按 F8 或點擊「開始釣魚」。運行時遊戲需保持前景且完整可見。魚餌用完仍需手動處理；本版沒有自動換餌功能。

已完成 Windows 自動化測試、真實截圖與影片離線回放、角色配色和多語言素材檢查。這些驗證不代表所有角色、動畫或遊戲更新後的畫面均能正確辨識。

使用說明：[繁體中文](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/blob/main/README.md) · [简体中文](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/blob/main/README.zh-CN.md) · [English](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/blob/main/README.en.md) · [日本語](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/blob/main/README.ja.md) · [한국어](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/blob/main/README.ko.md) · [Indonesian](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/blob/main/README.id.md)

[已知問題與臨時解決方案](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/blob/main/docs/KNOWN_ISSUES.md)
