# 1.0 — 介面升級與自動釣魚修正

彙總 0.3.0 至 1.0 的主要新增與修正。

## 自動續局與拉扯

- 改善不同角色配色下「繼續／下一步」及關閉 X 的辨識，修復部分藍紫色按鈕與較暗魚獲卡片無法自動續局的問題。
- 改善低飽和度魚標及滑塊高光的追蹤，保留軌道、卡片和按鈕結構核對，避免僅憑顏色誤點。
- 恢復 0.3.0 的拉扯控制節奏，撤回造成退化的實驗性控制方案；新增長按無上浮進展及滑鼠按鍵被外部放開時的重新按下機制。
- 補充擷取／辨識耗時、追蹤間隔與按鍵狀態診斷，便於排查不同電腦上的追蹤及輸入異常。

## 介面與操作

- 換用簡約的 Windows 原生淺色介面，統一開始／停止按鈕尺寸，改善字體及跨螢幕高 DPI 縮放。
- 移除外層捲動條，僅保留運行記錄的捲動條；目標數量改為普通輸入框。
- 新增魚獲計數與目標數量：每次開始都從零計算，達標後自動停止，`0` 表示不限。只計已確認的魚獲，不計材料或重複結果，不保存計數。
- 新增可自訂停止快捷鍵，預設 F9；點擊設定框後直接按鍵即可綁定或修改，切回視窗不會重新觸發綁定。
- 更新像素風海盜魚圖標，以 32×32 辨識度為目標，補齊 Windows 不同縮放比例的圖標尺寸。

## 多語言與診斷

- 支援繁體中文、简体中文、English、日本語、한국어、Indonesian 六種語言，介面、狀態及運行訊息同步切換；不會修改遊戲語言。
- README 改為軟件介紹與使用指南，提供六種語言版本，更新內容獨立放在 Release Notes。
- 「儲存本機診斷」改為「開發者模式」。右側 `?` 提供說明，可直接開啟本機診斷資料夾及項目地址。
- 診斷依目前 Windows 帳戶儲存，每次運行建立時間命名的資料夾。資料包含遊戲畫面與追蹤記錄，不會自動上傳；啟用後會增加效能負擔。

## 下載與使用

下載附件 **`Hololive-Fishing-Auto-v1.0.exe`** 即可使用，無需安裝 Python 或另外複製素材。適用於 Windows 10／11 x64；運行時讓遊戲保持前景，客戶區維持 16:9。附件 `SHA256SUMS.txt` 可核對下載檔案。

使用說明：[繁體中文](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/blob/main/README.md) · [简体中文](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/blob/main/README.zh-CN.md) · [English](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/blob/main/README.en.md) · [日本語](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/blob/main/README.ja.md) · [한국어](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/blob/main/README.ko.md) · [Indonesian](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/blob/main/README.id.md)

114 項離線／模擬測試已通過，但不代表所有角色、場景或魚種均已實機驗證，不保證四／五星魚或任何難度的成功率。如遇異常，請啟用開發者模式重現問題，並向作者提供問題描述與對應診斷資料。
