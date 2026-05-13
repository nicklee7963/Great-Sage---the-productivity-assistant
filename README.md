# 生產力工具專題（純 Python）

此專案以 Python 實作完整桌面體驗（不再使用 HTML/JS/Flask）：
- 一個 PyQt5 桌面 GUI（以 `gui2.py` 為主，含大賢者風格介面與番茄鐘）
- 一個桌面小寵物（走路動畫素材），點擊會打開內建 GUI

快速開始

1. 安裝依賴：

```bash
python -m pip install -r requirements.txt
```

2. 準備桌面寵物圖片：
 - 把走路圖片放在 `assets/walk/`，並依序命名為 `1.png`、`2.png`、`3.png` ...

3. 啟動桌面寵物（會啟動 PyQt GUI）：

```bash
python pet.py
```

4. 點擊桌面寵物會打開內建的 GUI（不需要瀏覽器）。

檔案說明

- `gui2.py`：主 GUI（大賢者風格預覽版）。
- `pet.py`：桌面寵物（使用 PyQt5，點擊顯示 GUI）。
- `assets/walk/`：桌面寵物走路動畫素材。
- `requirements.txt`：必要套件。
- `README.md`：說明文件。

注意事項

- 若無法安裝 `PyQt5`，可以改用 `PySide6`（需要修改 `pet.py` 與 `gui2.py` 中的 imports/小差異）。

