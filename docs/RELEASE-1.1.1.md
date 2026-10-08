# 1.1.1 — 修正特定水面場景 TAP 漏判

修正深藍水面被誤認為獎勵橫幅／過場，導致 TAP 提示明明出現，助手卻沒有點擊的問題。

- 明確的 TAP 證據現在可優先於尚未確認的橫幅判斷。
- 保留原有 TAP 辨識條件與連續影格確認；真正的獎勵、魚獲結算及圖鑑／物品彈窗仍優先處理。
- 故障截圖在六種語言、四種畫面尺寸共 24 組離線回放中，均恢復一次咬鉤點擊決策。155 項自動化測試通過；藍色時鐘畫面的等待測試未產生點擊。

下載 **`Hololive-Dreams-Fishing-Auto-v1.1.1.exe`**，先關閉舊版再執行。附件包含源碼 ZIP 與 `SHA256SUMS.txt`。

以上為離線驗證，仍需實機確認。若原場景仍有問題，請開啟開發者模式重現後，提供新的診斷 ZIP。

## English

Fixes missed TAP prompts in a specific dark-blue water scene. The water could be mistaken for a reward strip or transition, causing the classifier to skip TAP recognition.

- Confirmed TAP evidence can now override an unconfirmed strip/transition classification.
- Existing TAP checks and consecutive-frame confirmation remain. Confirmed rewards, fish results and encyclopedia/item dialogs retain priority.
- The reported two-frame sequence produces one hook-click decision in 24 offline language/size combinations. All 155 automated tests pass; the blue-clock waiting test produces no clicks.

Download **`Hololive-Dreams-Fishing-Auto-v1.1.1.exe`** and close the older version before running it. Source ZIP and SHA-256 checksums are included. Live confirmation is still needed; if the issue persists, please provide a new diagnostic ZIP.

[使用說明 / User guide](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/blob/main/README.md) · [已知問題 / Known issues](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/blob/main/docs/KNOWN_ISSUES.md)
