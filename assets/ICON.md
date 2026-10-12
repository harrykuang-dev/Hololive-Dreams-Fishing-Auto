# Application artwork / 程式圖像素材

## English

- `fishing-hook.png` is the transparent blue hook artwork generated from a hook reference with imagegen. `fishing-hook.ico` is the active EXE, window and dialog icon.
- The ICO contains 16/20/24/28/32/40/48/56/60/64/72/80/96/128/256-pixel frames. `tools/make_icon.py` crops transparent padding and packages resized frames.
- `snowsea-angel-thumb.png` is the simplified Snowsea Angel thumbnail from the game's fishing encyclopedia. It appears beside the application heading. See [NOTICE.md](NOTICE.md) for game-artwork rights.

```powershell
python tools/make_icon.py assets/fishing-hook.png assets/fishing-hook.ico --crop
python tools/preview_icon.py
```

The preview tool writes `build/icon-preview.png`, showing the current icon at native and enlarged sizes on light and dark backgrounds.

## 繁體中文

- `fishing-hook.png` 是以魚鉤參考圖透過 imagegen 產生的透明藍色圖示。`fishing-hook.ico` 用於 EXE、程式視窗及彈窗。
- ICO 包含 16/20/24/28/32/40/48/56/60/64/72/80/96/128/256 像素圖層。`tools/make_icon.py` 裁去透明留白，再將各尺寸打包。
- `snowsea-angel-thumb.png` 是遊戲釣魚圖鑑中的雪花海天使簡化縮圖，顯示於程式標題旁。遊戲素材權利說明見 [NOTICE.md](NOTICE.md)。
- 上方指令可重新產生 ICO 與預覽圖；預覽工具輸出 `build/icon-preview.png`，展示淺色與深色背景下的原尺寸及放大圖示。
