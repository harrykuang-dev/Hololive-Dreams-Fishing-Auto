# 已知問題 / Known issues

## 繁體中文

以下以 **1.1 正式版**為準，統一列出已修正的舊版問題與仍需注意的情況。更新說明見 [v1.1 Release](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/releases/tag/v1.1)。

| 問題 | 表現 | 1.1 狀態 | 處理方式 |
| --- | --- | --- | --- |
| 準備釣魚畫面被誤關 | 舊版可能把準備畫面的 X 當成圖鑑關閉 X，點擊後退出釣魚；淺色角色配色較容易觸發。 | **已修正**：加入準備畫面保護及圖鑑結構核對。 | 更新至 1.1。若仍誤關，停止助手並提供診斷。 |
| Ina 獎勵畫面無法繼續 | 深紫色 UI 下，領取材料後可能停在獎勵畫面，沒有點擊「繼續」。見 [Issue #1](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/issues/1)。 | **已修正已知案例**：擴展深色獎勵橫幅與按鈕辨識，已通過原問題截圖的離線驗證。 | 更新至 1.1。若仍停住，可手動點擊「繼續」，並提供診斷。 |
| TAP 提示未被辨識 | 魚咬鉤時沒有點擊，錯過 TAP 階段。 | **辨識已改善**：新增遊戲素材字形回退，通過離線回放及角色配色測試；未保證覆蓋所有實機情況。 | 若仍無反應，提供包含 TAP 階段的診斷與遊戲語言、角色資料。 |
| 開發者模式增加拉扯卡頓 | 舊版同步保存大型圖片可能拉長控制間隔；擷取畫面本身也有開銷。 | **診斷寫入已改善**：改為有上限的背景 JPEG 儲存；尚未證明所有卡頓均已消除。 | 日常關閉開發者模式，僅在重現問題時短暫開啟；保持遊戲前景、完整可見。 |
| `SetCursorPos` 呼叫失敗 | 出現 `(0, 'SetCursorPos', 'No error message is available')`，助手停止。 | **有使用者回報的解決方式**：本版未修改 Windows 權限要求，根因仍未確認。 | 以系統管理員身分執行助手。 |
| 開始快捷鍵無法註冊 | 快捷鍵被舊版助手或其他程式佔用，運行記錄顯示未就緒。 | **會提示註冊失敗**：按鍵佔用需由使用者處理。 | 關閉舊版助手，或改用其他按鍵；F12 為 Windows 保留鍵。確認記錄顯示「開始快捷鍵已就緒」後再使用。 |

辨識修正已用真實截圖、離線回放及配色測試驗證，不代表所有角色、動畫、解析度或遊戲更新後的畫面都已實機確認。開始快捷鍵可在助手處於背景時使用，但釣魚運行期間遊戲仍需保持前景。

回報請使用 [GitHub Issues](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/issues)，附上助手版本、遊戲語言／角色、解析度、Windows 顯示縮放、問題描述及診斷 ZIP。

只有開啟開發者模式才會產生診斷 ZIP；停止後成功打包並驗證會刪除已打包原始檔，保留 ZIP 供回報。ZIP 不會自動刪除或上傳，可在回報後自行刪除。一般模式不產生常駐啟動日誌。分享前請檢查截圖是否含有不想公開的內容。

## English

This table describes the **1.1 stable release**, covering resolved issues from earlier versions and remaining limitations. See the [v1.1 Release](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/releases/tag/v1.1) for the update notes.

| Issue | Symptoms | Status in 1.1 | What to do |
| --- | --- | --- | --- |
| Fishing preparation screen closed by mistake | Earlier versions could mistake the preparation screen's X for the encyclopedia close button and leave fishing, especially with pale character colors. | **Fixed**: preparation-screen protection and encyclopedia structure checks were added. | Update to 1.1. If it still closes the wrong screen, stop the assistant and provide diagnostics. |
| Ina reward screen does not continue | With the dark-purple UI, the assistant could stay on the reward screen after receiving a material without clicking Continue. See [Issue #1](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/issues/1). | **Known case fixed**: dark reward-strip and button recognition was expanded and verified offline against the reported screenshot. | Update to 1.1. If it still stalls, click Continue manually and provide diagnostics. |
| TAP prompt not recognized | The assistant misses the bite prompt and does not click during the TAP phase. | **Recognition improved**: an asset-based letter-shape fallback passed offline replay and character-palette checks; not every live situation is covered. | Provide diagnostics covering the TAP phase, along with the game language and character. |
| Developer mode adds reeling stalls | Synchronous image saving in earlier versions could delay control updates; screen capture also has a performance cost. | **Diagnostic writing improved**: JPEG saving now runs in the background with bounded storage; elimination of all stalls has not been established. | Keep Developer mode off for normal use and enable it briefly to reproduce problems. Keep the game foreground and fully visible. |
| `SetCursorPos` call fails | The error `(0, 'SetCursorPos', 'No error message is available')` appears and the assistant stops. | **User-reported workaround available**: Windows permission requirements are unchanged; the root cause remains unconfirmed. | Run the assistant as administrator. |
| Start hotkey cannot be registered | An older assistant instance or another program occupies the key; the log indicates that registration failed. | **Registration failure is reported**: key conflicts still require user action. | Close the older assistant or choose another key. F12 is reserved by Windows. Confirm that the log says the Start hotkey is ready. |

Recognition changes were checked with real screenshots, offline replay and palette tests. This does not establish live coverage of every character, animation, resolution or future game update. The Start hotkey works while the assistant is in the background, but the game must remain foreground while fishing runs.

Report problems through [GitHub Issues](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/issues), including the assistant version, game language/character, resolution, Windows display scaling, a description and the diagnostic ZIP.

Diagnostic ZIPs are created only with Developer mode enabled. Successful, verified packaging removes the packed originals and keeps the ZIP for reporting. ZIPs are not automatically deleted or uploaded; you may delete them after reporting. Normal mode does not create persistent startup logs. Review screenshots before sharing.
