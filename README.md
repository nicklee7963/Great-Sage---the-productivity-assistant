# 🎓 大賢者（Great Sage）- 生產力助手

一個集番茄鐘、行事曆、待辦清單、桌面寵物為一體的完整生產力工具。
透過可愛的桌面寵物提醒你各項任務，幫助你專注工作、記錄進度、管理時間。

**主要功能：**
- ⏲️ **番茄鐘計時器** - 自訂時間、活動分類、時間統計
- 📅 **行事曆與日程** - 日程規劃、作息安排、日期檢視
- ✓ **待辦清單** - 優先度分類、狀態追蹤、進度管理
- 🐾 **桌面寵物助手** - AI 聊天、動畫互動、智慧提醒
- 📚 **進度追蹤** - 書籍進度、視覺化書架展示

此專案以 Python 實作完整桌面體驗（純 PyQt5，無需瀏覽器）。

---

## 📖 目錄
1. [快速開始](#快速開始)
2. [安裝必要程式庫](#安裝必要程式庫)
3. [API 設置](#api-設置)
4. [啟動程式](#啟動程式)
5. [完整功能使用指南](#完整功能使用指南)
   - [史萊姆寵物互動](#史萊姆寵物互動)
   - [史萊姆對話框](#史萊姆對話框)
   - [番茄鐘使用](#番茄鐘使用)
   - [代辦清單使用](#代辦清單使用)
   - [行事曆使用](#行事曆使用)
   - [進度追蹤](#進度追蹤)
6. [數據檔案與自訂](#數據檔案與自訂)
7. [常見問題](#常見問題)

---

## 快速開始

### 簡單三步啟動大賢者

```bash
# 1. 進入專案目錄
cd Great-Sage---the-productivity-assistant

# 2. 安裝依賴套件
python -m pip install -r requirements.txt

# 3. 啟動桌面寵物
python pet.py
```

完成！你會看到一隻可愛的史萊姆寵物出現在桌面上。

---

## 安裝必要程式庫

### 第一步：檢查 Python 版本

確保你已安裝 Python 3.8 以上版本：

```bash
python --version
```

輸出應該顯示 `Python 3.8.x` 或更高版本。如果版本過低，請前往 [Python 官網](https://www.python.org/downloads/) 下載最新版本。

### 第二步：安裝依賴套件

在項目根目錄執行：

```bash
python -m pip install -r requirements.txt
```

或使用 pip3：

```bash
pip3 install -r requirements.txt
```

### 核心依賴說明

| 套件 | 版本 | 功能說明 |
|------|------|--------|
| **PyQt5** | ≥5.15 | 桌面 GUI 框架，提供所有視窗、按鈕、對話框 |
| **requests** | ≥2.28.0 | HTTP 請求庫，用於調用 Gemini API 和 LINE Bot API |

### 第三步：驗證安裝

驗證所有依賴是否正確安裝：

```bash
python -c "import PyQt5; import requests; print('✓ 所有依賴安裝成功！')"
```

若成功，會看到 `✓ 所有依賴安裝成功！` 的輸出。

---

## API 設置

大賢者提供兩個可選的 API 功能。如果不配置，程式也能正常運行，但會失去高級功能。

### 🤖 Google Gemini API（史萊姆聊天功能）

#### 這個 API 的用途
- 讓史萊姆能和你進行自然、有趣的對話
- 史萊姆會根據你的行程、書單主動提醒和聊天
- 提供溫暖、個性化的互動體驗

#### 獲取 API 密鑰步驟

**步驟 1：訪問 Google AI Studio**
- 打開瀏覽器，前往 [Google AI Studio](https://aistudio.google.com/apikey)
- 使用你的 Google 帳號登入（如無帳號請先註冊）

**步驟 2：創建免費 API 密鑰**
- 點擊左側「Get API Key」或「Create API key」按鈕
- 選擇「Create API key in new project」
- 系統會自動生成一個免費 API 密鑰，複製它

**步驟 3：檢查 API 配額**
- 免費密鑰每分鐘可以發送 60 個請求
- 這對日常使用完全足夠

#### 配置 Gemini API 密鑰

**方式 A：首次運行時自動設置（推薦）**

1. 執行 `python pet.py`
2. 如果尚未配置 API，系統會彈出對話框
3. 在對話框中輸入你的 Gemini API 密鑰
4. 點擊「確定」，密鑰會自動保存到 `pet_settings.json`

**方式 B：手動編輯配置檔**

1. 在項目根目錄找到 `pet_settings.json`（如不存在則新建）
2. 編輯檔案，加入以下內容：

```json
{
  "gemini_api_key": "your-gemini-api-key-here"
}
```

將 `your-gemini-api-key-here` 替換為你的實際 API 密鑰。

3. 保存檔案，重新執行 `python pet.py`

#### 驗證 Gemini API 設置

執行以下命令檢查 API 是否正確配置：

```bash
python -c "
import json
from pathlib import Path
settings_file = Path('pet_settings.json')
if settings_file.exists():
    with open(settings_file) as f:
        settings = json.load(f)
        key = settings.get('gemini_api_key', '')
        if key:
            print(f'✓ Gemini API 密鑰已配置')
        else:
            print('⚠ 配置檔中找不到 API 密鑰')
else:
    print('⚠ 尚未設置 API 密鑰')
"
```

---

### 📱 LINE Bot API（行事曆提醒功能）

#### 這個 API 的用途
- 行事曆中的事件開始前 5 分鐘，系統會透過 LINE 發送提醒訊息給你
- 自動監控 `calendar_events.json` 中的所有日程
- 智慧去重複，同一個事件只會提醒一次

#### 創建 LINE Bot 步驟

**步驟 1：訪問 LINE Developers 控制台**
- 打開瀏覽器，前往 [LINE Developers](https://developers.line.biz/zh-hant/)
- 用 LINE 帳號登入（如無帳號請先用 LINE App 註冊）
- 點擊「登入」並授權

**步驟 2：創建 Provider（提供者）**
- 點擊「Create new provider」按鈕
- 輸入 Provider 名稱，例如：「大賢者提醒系統」
- 勾選服務條款，點擊「Create」

**步驟 3：創建 Channel（頻道）**
- 在新建的 Provider 下，點擊「Create a new channel」
- 選擇 Channel type：**Messaging API**
- 填寫以下信息：
  - **Channel name**：「大賢者行事曆提醒」
  - **Description**：「個人生產力助手的事件提醒服務」
  - **Category**：選擇「Utilities」
  - 勾選「I agree to the LINE Channel Agreement」
- 點擊「Create」

#### 獲取認證信息

在新建的 Channel 頁面上，找到以下信息：

**1. Channel Access Token**
- 在「Messaging settings」區域找到「Channel access token」
- 點擊「Issue」生成 Token
- 複製這個 Token（類似：`a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5...`）

**2. 獲取你的 User ID**
- 在該頻道的頁面上找到「Your user ID」
- 複製你的 User ID（類似：`U1234567890abcdef1234567890abcdef`）

#### 配置 LINE Bot

1. 編輯 `pet_settings.json`，加入以下內容：

```json
{
  "gemini_api_key": "your-gemini-api-key",
  "line_channel_access_token": "your-channel-access-token",
  "line_user_id": "your-user-id"
}
```

2. 保存檔案，重新執行 `python pet.py`

#### 測試 LINE 提醒

1. 在行事曆中添加一個 5 分鐘後開始的事件，例如「測試提醒」
2. 等待，系統會自動在事件開始前 5 分鐘透過 LINE 發送訊息
3. 檢查你的 LINE 是否收到提醒

---

## 啟動程式

### 啟動史萊姆寵物

在項目根目錄執行：

```bash
python pet.py
```

你會看到：
1. 一隻可愛的史萊姆寵物出現在桌面的右下方
2. 寵物會自動在桌面上走動，還會有呼吸動畫
3. 如果配置了 Gemini API，寵物會定期主動和你聊天
4. 如果配置了 LINE Bot，行事曆提醒會在後台運行

### 啟動圖形化管理界面

有兩種方式啟動完整的管理 GUI（番茄鐘、代辦清單、行事曆、進度追蹤）：

**方式 1：點擊桌面寵物（推薦）**
- 用滑鼠「左鍵」點擊桌面上的史萊姆寵物
- 管理界面會彈出

**方式 2：直接運行 GUI 程式**
```bash
python gui2.py
```

---

## 完整功能使用指南

### 史萊姆寵物互動

#### 寵物在桌面上的位置和行為

當你執行 `python pet.py` 後：
- 史萊姆會出現在螢幕右下方
- 它會自動在螢幕底部來回走動
- 如果長時間不互動，寵物會越來越靠近右邊界

#### 左鍵點擊 - 開始使用

**操作**：用滑鼠左鍵單擊史萊姆

**效果**：
1. 完整的生產力管理界面會彈出
2. 界面包含四個功能區：
   - 番茄鐘（左上）
   - 行事曆（右上）
   - 代辦清單（左下）
   - 進度追蹤（右下）
3. 界面保持開啟，你可以繼續操作

#### 右鍵點擊 - 結束運行

**操作**：用滑鼠右鍵單擊史萊姆

**效果**：
1. 程式會完全退出
2. 史萊姆寵物消失
3. 所有後台服務（行事曆提醒等）停止

#### 按 Q 鍵 - 快速關閉

**操作**：當管理界面開啟時，按鍵盤上的「Q」鍵

**效果**：
1. 管理界面關閉，回到只有寵物的狀態
2. 寵物仍然在桌面上活動，後台服務繼續運行

---

### 史萊姆對話框

#### 開啟對話框

如果你已配置 Gemini API，史萊姆會在以下情況下和你聊天：

**自動聊天**（寵物主動開啟對話）
- 寵物會定期（大約每 2-5 分鐘）彈出聊天氣泡
- 氣泡會根據你的行程、書單內容進行智慧對話
- 例如：「我看到你今天有個重要的會議，要不要先準備一下？」

**點擊寵物開啟**
1. 寵物身上有個「點我跟我聊天」的提示
2. 點擊寵物，寵物會顯示一個對話氣泡
3. 氣泡會顯示寵物想和你聊的內容

#### 對話框中的操作

當對話氣泡彈出時：

**查看完整對話**
- 如果訊息被截斷，點擊氣泡可以展開查看全文

**關閉對話**
- 點擊氣泡外的任何地方即可關閉
- 或等待幾秒鐘，對話會自動消失

**多輪對話**
- 寵物會根據你的行程和待辦事項進行連續對話
- 每次對話都是獨立的，內容會有所不同

---

### 番茄鐘使用

番茄鐘是一種時間管理技術，幫助你專注工作，定期休息。

#### 界面說明

打開管理界面後，左上方就是番茄鐘面板，包含：
- **大圓形計時器** - 顯示當前時間倒計時
- **活動類別選擇** - 下拉列表選擇正在進行的活動
- **時間設置** - 可自訂番茄鐘時長
- **統計圖表** - 顯示今日/本週/本月的活動時間分布

#### 基本操作步驟

**步驟 1：選擇活動類別**
1. 點擊「活動類別」的下拉列表
2. 選擇你現在要做的事，例如：
   - 讀書中
   - 修習中（學習、上課）
   - 工作中
   - 健身中
   - 冥想中
   - 休息中
   - 睡覺中
   - 吃飯中
   - 寫作中
   - 或其他自訂類別

**步驟 2：設置時長**
1. 點擊時間輸入框（預設 25 分鐘）
2. 輸入你想要的時間（單位：分鐘），例如 45 分鐘
3. 點擊「Start」開始計時

**步驟 3：開始計時**
1. 按鈕會變成「Stop」
2. 圓形計時器開始倒計時，顏色會根據活動類別改變
3. 你可以繼續進行其他操作

**步驟 4：時間到**
1. 系統會彈出完成提示
2. 這段時間會自動記錄到統計數據中
3. 可以選擇開始新的一輪或休息

#### 自訂活動類別

如果預設類別不夠用，可以添加自己的活動：

1. 在活動類別輸入框中輸入新的活動名稱，例如「代碼審查」
2. 按 Enter 或點擊「Add」
3. 新類別會被添加到下拉列表中
4. 使用新類別進行計時，數據會自動記錄

#### 查看時間統計

界面右側的圖表區域會顯示：

**日視圖**（預設）
- 今天各項活動的時間分配圓餅圖
- 右側顯示活動列表和總時間

**週視圖**
- 點擊「Week」標籤查看本週數據
- 顯示本週各項活動的總時間

**月視圖**
- 點擊「Month」標籤查看本月數據
- 顯示本月各項活動的總時間

**年視圖**
- 點擊「Year」標籤查看本年數據
- 顯示本年各項活動的總時間

#### 重要提示

- 計時數據會自動保存到 `session_records.json`
- 每次計時完成後，數據立即記錄，無需手動保存
- 關閉程式不會丟失數據

---

### 代辦清單使用

代辦清單幫助你組織和追蹤所有任務。

#### 界面說明

打開管理界面後，左下方就是代辦清單面板，包含：
- **任務列表**（左列） - 顯示所有任務
- **任務詳情**（中間列） - 顯示選中任務的詳細信息
- **編輯面板**（右列） - 編輯或新增任務

#### 基本操作：新增任務

**步驟 1：點擊「新增」**
1. 在右側編輯面板點擊「新增」或「Add New」按鈕
2. 編輯面板會清空，準備輸入新任務

**步驟 2：輸入任務信息**
在編輯面板中填寫：

| 欄位 | 說明 | 範例 |
|------|------|------|
| **任務名稱** | 任務的主要內容 | 完成專案報告 |
| **優先度** | 任務的重要程度 | 緊急 / 常規 / 低優先度 |
| **狀態** | 任務進度 | 待處理 / 進行中 / 已完成 |
| **日期** | 任務應完成的日期 | 2026-06-10 |
| **備註** | 額外說明 | 需要附上圖表和數據 |

**步驟 3：保存任務**
1. 點擊「Save」或「保存」按鈕
2. 新任務會出現在左側列表中
3. 清單會自動根據優先度排序

#### 編輯現有任務

**步驟 1：選中任務**
1. 在左側列表中點擊要編輯的任務
2. 中間列會顯示該任務的詳細信息
3. 右側編輯面板會填入該任務的數據

**步驟 2：修改信息**
1. 編輯右側面板中的任何欄位
2. 修改優先度或狀態
3. 更新日期或備註

**步驟 3：保存更改**
1. 點擊「Save」按鈕
2. 修改會立即保存到 `todo_records.json`
3. 列表會自動重新排序

#### 標記任務完成

**方法 1：編輯狀態**
1. 選中任務
2. 在右側編輯面板中找到「狀態」欄位
3. 選擇「已完成」
4. 點擊「Save」

**方法 2：快速操作**
- 任務完成後，已完成的任務會顯示為灰色或有勾號
- 系統會自動將其移到清單底部

#### 刪除任務

1. 選中要刪除的任務
2. 在右側編輯面板中點擊「Delete」或「刪除」按鈕
3. 確認刪除
4. 任務會從清單和數據檔中移除

#### 日期篩選

代辦清單提供了一個小行事曆幫助篩選任務：

1. 在代辦清單左側找到「小行事曆」
2. 點擊特定日期
3. 清單會篩選出那一天的所有任務
4. 有任務的日期會被高亮顯示

#### 優先度分類

任務自動按優先度排序：

| 優先度 | 說明 | 色彩 |
|-------|------|------|
| 緊急 | 需要立即處理的任務 | 紅色 |
| 常規 | 普通的日常任務 | 藍色 |
| 低優先度 | 可以稍後處理的任務 | 綠色 |

#### 狀態分類

| 狀態 | 說明 |
|------|------|
| 待處理 | 還未開始的任務 |
| 進行中 | 正在進行的任務 |
| 已完成 | 已經完成的任務 |

---

### 行事曆使用

行事曆幫助你規劃日程和安排作息。

#### 界面說明

打開管理界面後，右上方就是行事曆面板，包含：
- **月視圖** - 顯示整個月份
- **日期選擇** - 可點擊特定日期
- **事件列表** - 顯示選定日期的所有事件
- **編輯區域** - 添加或修改事件

#### 基本操作：添加事件

**步驟 1：選擇日期**
1. 在月視圖上點擊一個日期
2. 該日期會被高亮選中
3. 如果有多個月份，使用「◀」和「▶」按鈕切換月份

**步驟 2：點擊「新增事件」**
1. 在右側編輯區域點擊「新增」或「Add Event」
2. 編輯面板會顯示新事件的輸入框

**步驟 3：填寫事件詳情**

| 欄位 | 說明 | 格式 | 範例 |
|------|------|------|------|
| **時間** | 事件開始時間 | HH:mm（24小時制）| 14:30 |
| **事件名稱** | 事件的內容說明 | 任意文字 | 團隊會議 |

**步驟 4：保存事件**
1. 點擊「Save」或「保存」按鈕
2. 事件會加入該日期的事件列表
3. 事件會按時間自動排序

#### 編輯現有事件

**步驟 1：選擇日期並選中事件**
1. 點擊該事件所在的日期
2. 在事件列表中點擊要編輯的事件
3. 右側編輯面板會填入該事件的信息

**步驟 2：修改信息**
1. 編輯時間或事件名稱
2. 任何修改都會即時反映

**步驟 3：保存**
1. 點擊「Save」按鈕
2. 修改會立即保存到 `calendar_events.json`

#### 刪除事件

1. 選中要刪除的事件
2. 點擊「Delete」或「刪除」按鈕
3. 確認刪除
4. 事件會從該日期移除

#### LINE 提醒設置

如果你配置了 LINE Bot API：

1. 行事曆中的所有事件會自動被監控
2. 事件開始前 5 分鐘，系統會透過 LINE 發送提醒
3. 無需任何額外設置，自動執行

**示例**：
- 事件：「下午茶會」，時間 14:30
- 系統會在 14:25 時發送 LINE 訊息提醒

#### 月份導航

- 點擊「◀」返回上一個月份
- 點擊「▶」進入下一個月份
- 點擊「今天」返回當前月份

---

### 進度追蹤

進度追蹤幫助你記錄書籍閱讀進度，視覺化書架。

#### 功能說明

進度追蹤包含兩部分：
- **書架展示**（左側） - 視覺化顯示你的書籍封面和進度
- **書籍管理**（右側） - 添加、編輯書籍信息

#### 第一步：準備書籍封面圖片

**準備圖片**
1. 找到你要追蹤的書籍的封面圖片（JPG 格式）
2. 圖片解析度建議 280×420 像素或更高（不一定嚴格，系統會自動縮放）

**放置圖片**
1. 在項目根目錄找到或創建文件夾：`assets/book_covers/`
2. 將書籍封面圖片放入這個文件夾
3. **重要**：圖片文件名必須和你在進度追蹤中輸入的「書名」完全相同

**命名規則**
- 如果書名是「Python編程」，圖片應命名為 `Python編程.jpg`
- 如果書名是「三體」，圖片應命名為 `三體.jpg`
- 大小寫和符號必須完全匹配

**目錄結構示例**
```
assets/
├── book_covers/
│   ├── Python編程.jpg
│   ├── 三體.jpg
│   ├── 活著.jpg
│   └── 解憂雜貨店.jpg
├── music/
└── walk/
```

#### 第二步：添加書籍信息

**打開進度追蹤面板**
1. 在管理界面右下方找到「進度追蹤」區域

**點擊「新增書籍」**
1. 點擊「新增」或「Add Book」按鈕
2. 編輯區域會清空，準備輸入新書籍

**填寫書籍信息**

| 欄位 | 說明 | 範例 | 重要性 |
|------|------|------|--------|
| **書名** | 書籍的名稱 | Python編程 | ⭐⭐⭐ 必須和圖片文件名相同 |
| **作者** | 書籍作者 | Guido van Rossum | 選填，便於識別 |
| **分類** | 書籍類別 | 程式設計 | 選填，幫助組織書架 |
| **總頁數** | 書籍總共有多少頁 | 450 | 選填，用於計算進度 |
| **當前頁數** | 你已經讀到第幾頁 | 120 | 選填，自動計算進度百分比 |

**保存書籍**
1. 所有信息填完後，點擊「Save」或「保存」按鈕
2. 新書籍會加入書架
3. 如果有對應的封面圖片，左側書架會顯示封面

#### 第三步：查看書架

**自動顯示書架**
1. 在右側列表中點擊任何書籍
2. 左側會自動切換到書架視圖
3. 你會看到：
   - 按分類分組的所有書籍
   - 每行最多 4 本書
   - 每本書顯示封面、進度條和完成百分比

**書架布局**
- 書籍按分類分組顯示（例如：「程式設計」分類的書放在一起）
- 同一分類的書按字母順序排列
- 每本書下方顯示進度條，顏色從紅到綠變化
- 進度條下方顯示「50% (120/240)」表示進度

**缺失封面的處理**
- 如果找不到對應的封面圖片，會顯示問號「?」
- 檢查圖片文件名是否和書名完全相同
- 確保圖片放在 `assets/book_covers/` 文件夾中

#### 第四步：更新閱讀進度

**編輯現有書籍**
1. 在右側列表中點擊要更新的書籍
2. 編輯面板會填入該書籍的信息

**更新當前頁數**
1. 修改「當前頁數」欄位，輸入你最新讀到的頁數
2. 進度百分比會自動計算
3. 點擊「Save」保存

**進度計算**
- 進度 = （當前頁數 ÷ 總頁數）× 100%
- 例如：讀了 150 頁，總共 300 頁 → 50% 完成

#### 刪除書籍

1. 選中要刪除的書籍
2. 點擊「Delete」或「刪除」按鈕
3. 確認刪除
4. 書籍會從列表和數據檔中移除
5. 書架會自動刷新

#### 分類管理

**添加新分類**
1. 在「分類」欄位下拉菜單中選擇「新增分類」或直接輸入新分類名
2. 例如：「奇幻文學」、「歷史傳記」、「自我提升」
3. 新分類會被保存到 `book_categories.json`

**查看分類書籍**
1. 在書架上，同分類的書會聚集在一起
2. 分類標題會在每組書的上方顯示

#### 常見問題

**Q: 書架上顯示問號是什麼意思？**
A: 說明找不到對應的封面圖片。檢查：
- 圖片文件名是否和書名完全相同（包括大小寫和標點）
- 圖片是否放在 `assets/book_covers/` 文件夾
- 圖片格式是否是 `.jpg`

**Q: 可以用其他圖片格式嗎？**
A: 系統目前只支持 `.jpg` 格式。如果有 PNG 或其他格式的圖片，請轉換為 JPG 後再放入

**Q: 刪除了一本書，書架上還顯示怎麼辦？**
A: 重新點選任何書籍，書架會自動刷新並移除已刪除的書

**Q: 書籍順序可以調整嗎？**
A: 目前按字母順序自動排列（中文書在前，英文書在後）。系統會自動根據分類和名稱排序

**Q: 進度會自動同步嗎？**
A: 是的，編輯右側面板中的任何信息後，書架會自動更新。無需手動刷新

---

## 數據檔案與自訂

### 數據檔案說明

大賢者使用 JSON 檔案儲存所有數據。你可以直接編輯這些檔案來自訂設置。

| 檔案名 | 用途 | 說明 |
|-------|------|------|
| `pet_settings.json` | 寵物和 API 設置 | 儲存 Gemini API 密鑰、LINE Bot Token、User ID |
| `session_records.json` | 番茄鐘數據 | 儲存所有計時記錄（活動、時間、日期） |
| `todo_records.json` | 待辦清單 | 儲存所有任務（名稱、優先度、狀態、日期） |
| `calendar_events.json` | 行事曆事件 | 儲存所有日程安排（日期、時間、事件名稱） |
| `progress_records.json` | 書籍進度 | 儲存書籍信息（書名、作者、分類、進度） |
| `book_categories.json` | 書籍分類 | 儲存所有書籍分類 |
| `pet.py` | 主程式 | 啟動史萊姆寵物和所有後台服務 |
| `gui2.py` | 管理界面 | 啟動完整的生產力管理 GUI |

### 備份你的數據

定期備份重要的 JSON 檔案：

```bash
# 備份到 backup 文件夾
mkdir backup
cp *.json backup/
```

### 編輯 JSON 檔案（進階）

如果你熟悉 JSON 格式，可以直接編輯這些檔案。例如：

**編輯 pet_settings.json**
```json
{
  "gemini_api_key": "your-key",
  "line_channel_access_token": "your-token",
  "line_user_id": "your-user-id"
}
```

**編輯 status_options.json**
```json
{
  "待處理": "pending",
  "進行中": "in_progress",
  "已完成": "completed"
}
```

---

## 常見問題

### 安裝和啟動相關

**Q: 執行 `python pet.py` 後沒有任何反應**
A: 檢查以下項目：
1. 確保 Python 版本 ≥ 3.8：`python --version`
2. 確保依賴已安裝：`pip list | grep PyQt5`
3. 嘗試使用 `python3 pet.py`
4. 檢查是否有錯誤訊息，複製並搜索

**Q: ImportError: No module named 'PyQt5'**
A: 依賴尚未安裝，執行：
```bash
pip install -r requirements.txt
```

**Q: 寵物出現後立即消失或崩潰**
A: 檢查 `assets/walk/` 文件夾：
1. 確保文件夾中有圖片文件（1.png、2.png 等）
2. 如果沒有圖片，系統會使用預設佔位符，但可能出現問題
3. 確保圖片格式正確（PNG 或 JPG）

### 寵物互動相關

**Q: 寵物不說話，也不聊天**
A: 可能的原因：
1. 沒有配置 Gemini API
   - 檢查 `pet_settings.json` 是否有 `gemini_api_key`
   - 重新設置 API 密鑰
2. API 密鑰無效或過期
   - 前往 [Google AI Studio](https://aistudio.google.com/apikey) 重新生成
3. 網絡連接問題
   - 確保能訪問 `generativelanguage.googleapis.com`

**Q: 寵物移動時卡頓或跳躍**
A: 這通常是正常的，特別是在系統繁忙時。如果嚴重卡頓：
1. 檢查 `assets/walk/` 中的圖片數量
2. 圖片過多可能導致加載慢，建議 8-12 張為佳
3. 確保圖片分辨率不過高（推薦 120×120）

**Q: 右鍵點擊寵物沒有反應**
A: 右鍵應該直接結束程式，無需確認。如果沒有反應：
1. 嘗試用 Ctrl+C 在終端中停止程式
2. 或直接關閉終端窗口

### API 相關

**Q: Gemini API 返回「API 配額已用盡」**
A: 免費配額為每分鐘 60 個請求。如果超過：
1. 等待一分鐘後重試
2. 或升級到付費計畫
3. 在 Google Cloud Console 中檢查配額使用情況

**Q: LINE 提醒沒有發送**
A: 檢查以下項目：
1. 確保 `pet_settings.json` 中有：
   - `line_channel_access_token`（Channel Access Token）
   - `line_user_id`（你的 LINE User ID）
2. 確保 Token 和 User ID 正確複製（沒有多餘的空格）
3. 檢查 LINE 帳號是否加入了 Bot（掃描 QR Code）
4. 確保行事曆事件的時間格式正確（HH:mm，例如 14:30）

### 數據相關

**Q: 我的待辦清單數據丟失了怎麼辦？**
A: 檢查備份：
1. `todo_records.json` 應該在項目根目錄
2. 如果檔案被刪除，可能無法恢復
3. 建議定期備份 JSON 檔案

**Q: 如何匯出我的數據？**
A: 所有數據都儲存在 JSON 檔案中：
1. 複製 `.json` 檔案到外部儲存設備
2. 或使用 Python 讀取和處理這些檔案

**Q: 可以在多台電腦上同步數據嗎？**
A: 目前不支援雲同步。你可以：
1. 手動複製 JSON 檔案到其他電腦
2. 使用 Git 或其他版本控制工具
3. 使用 Dropbox、Google Drive 等雲儲存自動同步文件夾

### 界面和設置相關

**Q: 界面太小或太大了**
A: 系統會根據螢幕解析度自動縮放，但：
1. 如果仍不滿意，可以編輯代碼中的 `_screen_scale()` 函數
2. 或調整系統的 DPI 設置
3. 在 `gui2.py` 和相關 feature 檔案中修改

**Q: 如何改變界面主題或色彩？**
A: 大賢者使用「霓虹」科技主題。要自訂：
1. 編輯各 feature 檔案中的 `ACTIVITY_NEON_PALETTE` 和 `ACTIVITY_NEON_COLORS`
2. 修改 PyQt5 的 StyleSheet
3. 詳見各個 Python 檔案中的色彩設置

### 效能相關

**Q: 程式運行很慢或卡頓**
A: 檢查以下項目：
1. 系統資源（CPU、記憶體）是否充足
2. 是否有太多背景程式執行
3. `assets/walk/` 中的圖片是否過多或過大
4. 嘗試關閉圖表和動畫減少負擔

---

## 進階設置和開發

### 修改番茄鐘預設時長

編輯 `pomodoro_feature.py`，找到預設時間設置，修改分鐘數。

### 自訂活動類別顏色

編輯各 feature 檔案中的 `ACTIVITY_NEON_COLORS` 字典，添加或修改顏色映射。

### 擴展功能

大賢者的代碼結構清晰，容易擴展。你可以：
1. 添加新的 feature 模塊
2. 集成其他 API（例如天氣、郵件）
3. 修改寵物動畫或行為

---

## 許可證

本項目採用 MIT 許可證。詳見 LICENSE 檔案。

---

## 支持和反饋

如有問題或建議，歡迎提出 Issue 或 Pull Request。

**祝你使用大賢者愉快！🎓✨**
   - 導航到「Messaging API」標籤
   - 在「Channel access token」區域，點擊「Issue」
   - 複製生成的 Token（長字符串）

2. **Your User ID**
   - 在同一頁面的「Your user ID」區域
   - 複製你的 User ID（用於接收提醒）
   - 如果看不到，可添加該 Bot 為好友，發送任何訊息後再查看

#### 設置提醒功能

編輯 `pet.py`，在初始化代碼中添加 LINE 提醒管理器：

```python
from line_reminder import LineReminderManager

# 在 main() 函數中添加
channel_access_token = "your-channel-access-token-here"
user_id = "your-user-id-here"
line_manager = LineReminderManager(channel_access_token, user_id)
line_manager.start()  # 啟動後台監控線程
```

#### 完整配置示例

在 `pet_settings.json` 中保存 LINE 認證信息：

```json
{
  "api_key": "your-gemini-api-key-here",
  "line_channel_access_token": "your-line-channel-access-token",
  "line_user_id": "your-line-user-id"
}
```

然後在 `pet.py` 中使用：

```python
import json
from pathlib import Path

def load_settings():
    settings_file = Path('pet_settings.json')
    if settings_file.exists():
        with open(settings_file) as f:
            return json.load(f)
    return {}

settings = load_settings()
line_manager = LineReminderManager(
    settings.get('line_channel_access_token'),
    settings.get('line_user_id')
)
line_manager.start()
```

#### 測試 LINE 連接

1. **添加 Bot 為好友**
   - 在 LINE Developers Console 中進入 Channel
   - 導航到「Messaging API」標籤
   - 掃描「QR code」區域的 QR 碼
   - 將 Bot 添加為 LINE 好友

2. **發送測試訊息**
   - 執行測試腳本：
   ```bash
   python -c "
   from line_reminder import LineReminderManager
   manager = LineReminderManager('your-token', 'your-user-id')
   manager._send_line_message('大賢者提醒系統已啟動！')
   "
   ```
   - 檢查你的 LINE 是否收到測試訊息

3. **驗證提醒功能**
   - 在 `calendar_events.json` 中添加即將發生的事件
   - 系統會在事件開始前 5 分鐘自動發送 LINE 提醒

#### 常見問題

**Q: 如何獲得 User ID？**  
A: 添加 Bot 為好友後，Bot 會自動記錄。你也可以向 Bot 發送訊息，然後在 LINE Developers 後台的「Messaging API」頁面查看。

**Q: 能否改變提醒時間？**  
A: 可以。編輯 `line_reminder.py`，修改 `REMINDER_ADVANCE_SECONDS` 的值：
```python
REMINDER_ADVANCE_SECONDS = 5 * 60  # 改為需要的秒數（例如 10 * 60 為 10 分鐘）
```

**Q: 如何禁用某個功能？**  
A: 在 `pet.py` 中直接注釋掉 `line_manager.start()` 行即可停用提醒功能。

---

## 程式碼檔案說明

### 核心啟動檔

#### **pet.py** 🐾
**用途：** 桌面寵物主程式

**功能：**
- 在桌面上顯示可愛的寵物角色
- 寵物會自動行走（從 `assets/walk/` 載入動畫幀）
- 點擊寵物會打開完整的生產力 GUI
- 支持鍵盤快鍵：按 `Q` 關閉寵物，`G` 顯示/隱藏 GUI
- 可與寵物對話（需要 Gemini API 密鑰）

**編輯建議：**
- 修改寵物起始位置：編輯 `PetWindow` 類中的 `move()` 函數
- 改變寵物大小：修改 `setFixedSize()` 的值
- 自訂動畫速度：編輯 `self.animation_speed` 參數

---

#### **gui2.py** 💻
**用途：** 主要 GUI 視窗（整合所有功能）

**功能：**
- 統一介面整合番茄鐘、行事曆、待辦清單
- 霓虹科技風格的大賢者主題設計
- 支持多螢幕縮放適配（自動檢測螢幕解析度）
- 標籤頁切換各功能模組

**編輯建議：**
- 改變顏色主題：編輯 `ACTIVITY_NEON_PALETTE` 和 `ACTIVITY_NEON_COLORS`
- 調整 UI 大小：修改 `_scaled()` 函數中的倍數
- 新增功能標籤：在 `def create_sage_windows()` 中加入新的 `addTab()`

---

### 功能模組

#### **pomodoro_feature.py** ⏲️
**用途：** 番茄鐘計時與時間統計

**功能：**
- 可自訂時間的番茄鐘計時器（預設25分鐘）
- 支持多種活動分類（讀書、修習、健身、休息等）
- 日/週/月/年的活動時間統計圖表
- 圓餅圖顯示當日時間分配
- 長條圖顯示週/月/年的分類統計
- 工作記錄自動存檔

**編輯建議：**
- 新增活動類別：編輯 `ACTIVITY_NEON_COLORS` 字典
- 改變計時時間：修改 `self._last_work_minutes = 25`
- 自訂顏色：編輯 `ACTIVITY_NEON_PALETTE` 中的 RGB 值

**工作原理：**
- 每次計時完成時，時間記錄會存入 `session_records.json`
- 統計圖表自動從記錄檔計算數據

---

#### **calendar_feature.py** 📅
**用途：** 行事曆與日程管理

**功能：**
- 月份行事曆檢視
- 新增、編輯、刪除日程安排
- 查看特定日期的全天作息紀錄
- 支持多個事件同時安排
- 事件時間和任務描述記錄

**編輯建議：**
- 改變行事曆起始日：編輯 `calendar.setFirstWeekDay()`
- 自訂事件顏色：修改 `_build_ui()` 中的樣式表
- 新增事件字段：編輯 `_build_editor_page()` 以加入新的輸入框

**工作原理：**
- 所有事件存入 `calendar_events.json`
- 格式：`{"2026-05-31": [{"time": "08:00", "task": "起床"}]}`

---

#### **todo_feature.py** ✓
**用途：** 待辦清單與任務追蹤

**功能：**
- 建立、編輯、完成、刪除任務
- 任務優先度分類：緊急、常規、低優先度
- 任務狀態追蹤：待處理、進行中、已完成
- 三欄佈局：左側清單 | 中間詳情 | 右側編輯
- 小型行事曆與日期篩選
- 任務描述和建立時間記錄

**編輯建議：**
- 新增優先度等級：編輯 `TodoListPanel.TYPE_NAMES`
- 改變任務狀態：編輯 `TodoListPanel.STATUS_NAMES`
- 自訂狀態顏色：修改 `STATUS_COLORS` 字典

**工作原理：**
- 任務存入 `todo_records.json`
- 格式：`{"id": "uuid", "name": "任務名", "type": "urgent", "status": "pending"}`

---

#### **pet_chat_feature.py** 🤖
**用途：** AI 寵物聊天功能

**功能：**
- 使用 Google Gemini API 進行自然對話
- 自動從書單、行事曆獲取上下文提醒
- 背景執行緒避免 UI 卡頓
- 支持自訂 API 密鑰
- 寵物主動打招呼和提醒

**編輯建議：**
- 改變寵物個性：編輯 `CHAT_SYSTEM_PROMPT` 的提示詞
- 修改聊天頻率：調整 `CHAT_PROMPT_MIN_MS` 和 `CHAT_PROMPT_MAX_MS`
- 新增提醒類型：編輯 `LOCAL_OPENERS`, `BOOK_TOPIC_OPENERS`, `CALENDAR_TOPIC_OPENERS`

**設定 Gemini API 密鑰：**
- 首次運行時會提示輸入 API 密鑰
- 或在 `pet_settings.json` 中直接設定：
```json
{"api_key": "your-gemini-api-key-here"}
```

---

## 功能使用指南

### 🕐 如何使用番茄鐘

1. **打開番茄鐘** - 點擊 GUI 中的「番茄鐘」標籤
2. **選擇活動類別** - 從下拉選單選擇你要做的活動（如「讀書中」）
3. **啟動計時** - 點擊「開始」按鈕
4. **檢視統計** - 切換「當日」/「當週」/「當月」/「當年」查看時間分配統計

**新增活動類別：**
- 在番茄鐘介面中點擊下拉選單的「新增...」選項
- 輸入新的活動名稱（系統會自動在末尾加上「中」）
- 系統會自動為新活動分配顏色

### 📅 如何管理行事曆

1. **打開行事曆** - 點擊 GUI 中的「行事曆」標籤
2. **瀏覽月份** - 使用左右箭頭切換月份
3. **點擊日期** - 查看該日期的全天作息紀錄
4. **新增事件** - 輸入時間和任務描述，點擊「新增」
5. **查看列表** - 下方列表顯示該日所有事件

### ✓ 如何管理待辦清單

1. **打開待辦清單** - 點擊 GUI 中的「待辦清單」標籤
2. **左側清單** - 顯示所有任務（可按日期和優先度篩選）
3. **中間詳情** - 點擊任務查看完整描述
4. **右側編輯** - 新增、編輯、標記完成或刪除任務
5. **優先度** - 選擇「緊急」、「常規」或「低優先度」
6. **狀態** - 設定「待處理」、「進行中」或「已完成」

---

## 數據檔案與自訂

### 📝 JSON 檔案格式說明

#### **session_records.json** - 番茄鐘工作記錄
存儲每次番茄鐘工作的記錄。

**格式示例：**
```json
[
  {
    "timestamp": "2026-05-31T14:30:00",
    "status": "讀書中",
    "seconds": 1500
  },
  {
    "timestamp": "2026-05-31T15:00:00",
    "status": "修習中",
    "seconds": 1200
  }
]
```

**欄位說明：**
- `timestamp` - ISO 格式時間戳記
- `status` - 活動類別名稱
- `seconds` - 工作秒數

---

#### **todo_records.json** - 待辦清單任務
存儲所有待辦任務。

**格式示例：**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "完成專案報告",
    "type": "urgent",
    "status": "in_progress",
    "description": "需要完成 Q2 季度的詳細報告",
    "created_date": "2026-05-20T10:00:00",
    "completed_date": null
  },
  {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "name": "日常代碼審查",
    "type": "routine",
    "status": "pending",
    "description": "審查今天提交的代碼",
    "created_date": "2026-05-31T08:00:00",
    "completed_date": null
  }
]
```

**欄位說明：**
- `id` - 唯一識別符（UUID）
- `name` - 任務名稱
- `type` - 優先度：`urgent` (緊急)、`routine` (常規)、`low` (低優先度)
- `status` - 狀態：`pending` (待處理)、`in_progress` (進行中)、`completed` (已完成)
- `description` - 任務描述
- `created_date` - 建立時間
- `completed_date` - 完成時間（未完成時為 null）

**如何手動編輯：**
1. 在編輯器中打開 `todo_records.json`
2. 複製現有任務結構並修改字段
3. 確保 `id` 是唯一的（可使用線上 UUID 生成器）
4. 儲存檔案（GUI 會自動讀取）

---

#### **calendar_events.json** - 行事曆事件
存儲日程安排和作息紀錄。

**格式示例：**
```json
{
  "2026-05-31": [
    {
      "time": "08:00",
      "task": "起床"
    },
    {
      "time": "10:00",
      "task": "開會"
    },
    {
      "time": "14:00",
      "task": "健身"
    }
  ],
  "2026-06-01": [
    {
      "time": "09:00",
      "task": "工作"
    }
  ]
}
```

**欄位說明：**
- 日期字串（ISO 格式 `YYYY-MM-DD`）為鍵
- 事件陣列為值
- 每個事件包含 `time` (時間) 和 `task` (任務描述)

**如何手動添加：**
```json
{
  "2026-06-05": [
    {"time": "19:00", "task": "看書"}
  ]
}
```

---

#### **status_options.json** - 活動類別設定
存儲番茄鐘的所有活動類別。

**格式示例：**
```json
{
  "statuses": [
    "讀書中",
    "修習中",
    "健身中",
    "休息中",
    "工作中",
    "自訂活動中"
  ]
}
```

**如何添加新活動類別：**
1. 打開 `status_options.json`
2. 在 `statuses` 陣列中新增活動名稱（必須以「中」結尾）
3. 儲存檔案
4. 重新啟動 GUI，新活動會自動出現在下拉選單中

**範例 - 新增程式開發活動：**
```json
{
  "statuses": [
    "讀書中",
    "修習中",
    "健身中",
    "休息中",
    "工作中",
    "程式開發中"
  ]
}
```

---

#### **book_categories.json** - 書單分類
存儲讀書書單，寵物 AI 可從中獲取提醒內容。

**格式示例：**
```json
[
  "Python 進階程式設計",
  "設計模式",
  "時間管理的奧秘",
  "自我管理的秘密"
]
```

**如何添加新書籍：**
1. 打開 `book_categories.json`
2. 在陣列中新增書名
3. 儲存檔案
4. 寵物下次聊天時可能會提及這些書籍

**範例 - 新增書籍：**
```json
[
  "Python 進階程式設計",
  "設計模式",
  "時間管理的奧秘",
  "自我管理的秘密",
  "AI 時代的學習策略"
]
```

---

#### **pet_settings.json** - 寵物設定
存儲寵物個性化設定（Gemini API 與 Line Bot 凭证）。

**格式示例：**
```json
{
  "gemini_api_key": "your-gemini-api-key-here",
  "line_channel_access_token": "your-line-channel-access-token",
  "line_user_id": "your-line-user-id"
}
```

**欄位說明：**
- `gemini_api_key` - Google Gemini AI 聊天 API 密鑰
- `line_channel_access_token` - Line Bot Channel Access Token（用於行事曆提醒）
- `line_user_id` - 你的 Line User ID（接收提醒的目標用戶）

**設定 Gemini API 密鑰：**
1. 前往 [Google AI Studio](https://aistudio.google.com/)
2. 建立或取得你的 API 密鑰
3. 在此檔案中設定 `gemini_api_key` 欄位

**設定 Line Bot 行事曆提醒：**
1. 前往 [Line Developers](https://developers.line.biz/) 建立 Channel
2. 取得 **Channel Access Token**
3. 在 Line Messaging API 中設定 Webhook（可設為空）
4. 找出你的 **Line User ID**（可透過寵物聊天或傳送訊息取得）
5. 在此檔案中設定：
```json
{
  "line_channel_access_token": "your-token-here",
  "line_user_id": "your-id-here"
}
```

**獲取 Line User ID：**
- 最簡單方式：寵物啟動後，在 Line 上傳送任何訊息給 Bot 帳號
- 機器人會在終端機或日誌中顯示你的 User ID
- 將此 ID 複製到 `pet_settings.json` 中

**Line Bot 行事曆提醒功能：**
- ✅ 自動監控 `calendar_events.json` 中的日程
- ✅ 在事件開始前 5 分鐘透過 Line 發送提醒
- ✅ 簡潔提醒格式：`⏰ 5分鐘後你有「開會」(14:00)`
- ✅ 每個事件只提醒一次（避免重複提醒）
- ✅ 後台執行緒運行（不會影響 GUI 性能）

---

### 🎨 資源檔案管理

#### **assets/walk/** - 寵物動畫素材
存儲寵物行走動畫的所有幀。

**如何自訂寵物動畫：**
1. 建立或準備你的動畫幀（推薦 PNG 格式，透明背景）
2. 放入 `assets/walk/` 資料夾
3. 依序命名為 `1.png`、`2.png`、`3.png`...
4. 重新啟動 `pet.py`

**建議設定：**
- 圖片尺寸：100×100 到 200×200 像素
- 格式：PNG（支持透明背景）
- 幀數：4-8 幀（越多越流暢）

---

## 新功能：Line Bot 行事曆提醒 📱

### 功能介紹

**大賢者現在可以在行事曆事件開始前 5 分鐘透過 Line 自動提醒你！**

- ⏰ **自動提醒** - 監控行事曆，在事件前 5 分鐘發送 Line 訊息
- 📝 **簡潔格式** - 提醒訊息包含時間和事件名稱
- 🔄 **智慧去重** - 同一事件只提醒一次，避免騷擾
- 🔌 **後台執行** - 不會影響主程式運行
- 🎯 **自動檢測** - 每 30 秒掃描一次，確保不漏掉任何事件

### 快速設定

#### 1️⃣ 建立 Line Bot Channel

1. 前往 [Line Developers](https://developers.line.biz/)
2. 登入你的 Line 帳號
3. 建立新的 **Messaging API Channel**
4. 取得 **Channel Access Token**（從 Channel 設定頁面）
5. 設定 **Webhook URL**（可設為空）

#### 2️⃣ 取得你的 User ID

有兩種方式取得 Line User ID：

**方法 1（推薦）：透過寵物聊天**
1. 啟動 `python pet.py`
2. 點擊寵物，打開聊天對話框
3. 傳送任何訊息給寵物 AI
4. 在終端機查看輸出，會顯示你的 User ID

**方法 2：手動查詢**
- 使用 Line Bot SDK 或 Postman 查詢
- 訪問 [Line My Page](https://line.me/ti/p) 查看 ID

#### 3️⃣ 設定 pet_settings.json

編輯 `pet_settings.json` 並填入你的凭证：

```json
{
  "gemini_api_key": "your-gemini-key-here",
  "line_channel_access_token": "YOUR_CHANNEL_ACCESS_TOKEN",
  "line_user_id": "YOUR_USER_ID"
}
```

例如：
```json
{
  "line_channel_access_token": "PAaimyzoqRqt...",
  "line_user_id": "Ue1571b42d5c0..."
}
```

#### 4️⃣ 啟動大賢者

```bash
python pet.py
```

終端機會顯示：
```
[Main] Line Bot 行事曆提醒已啟動
```

### 使用範例

假設你的 `calendar_events.json` 中有：
```json
{
  "2026-06-05": [
    {"time": "14:00", "task": "與客戶開會"},
    {"time": "16:00", "task": "團隊討論"}
  ]
}
```

**提醒時間表：**
- 13:55 → 寵物啟動，開始監控
- 13:55:00 → Line 訊息：`⏰ 5分鐘後你有「與客戶開會」(14:00)`
- 15:55:00 → Line 訊息：`⏰ 5分鐘後你有「團隊討論」(16:00)`

### 故障排除

**問題：Line 提醒沒有發送**

檢查清單：
1. ✓ `pet_settings.json` 中的 `line_channel_access_token` 和 `line_user_id` 是否正確
2. ✓ 網際網路連接是否正常（提醒需要連線到 Line API）
3. ✓ 終端機是否顯示「Line Bot 行事曆提醒已啟動」
4. ✓ `calendar_events.json` 中的時間格式是否為 `HH:MM`（如 `14:00`）
5. ✓ 事件時間是否正確（系統使用本地時間）

**問題：收到「Permission denied」或「Unauthorized」錯誤**

- 確認 Channel Access Token 是正確的（無多餘空格或換行）
- 確認 User ID 是否真的是你的 ID（不是其他人的）
- Token 可能已過期，重新從 Line Developers 取得新的

**問題：看不到我的 User ID**

- 使用 `python line_reminder.py <token> <test_id>` 測試
- 在 Line 官方帳號中加入機器人，傳送訊息以觸發日誌輸出
- 查看終端機輸出取得正確的 User ID

---

## 常見問題

### Q1: Gemini API 配額超限 (Quota exceeded)

**問題訊息：**
```
Gemini API quota exceeded: Your API key has reached the usage limit.
```

**原因：**
- 你的免費 Gemini API 配額已用完（免費帳號每分鐘有限制）
- 這只影響 **寵物 AI 聊天功能**，不影響 Line 提醒

**解決方案：**

**方案 1：重新產生新的 API 密鑰**
1. 前往 [Google AI Studio](https://aistudio.google.com/)
2. 登出並重新登入
3. 建立新的 API 密鑰
4. 更新 `pet_settings.json` 中的 `gemini_api_key`

**方案 2：禁用 AI 聊天功能（保留 Line 提醒）**
- 編輯 `pet.py`，註解掉寵物聊天初始化：
```python
# 以下程式碼會被跳過，寵物不會嘗試聊天
try:
    api_key = resolve_gemini_api_key(prompt_if_missing=False)
    w.chat_feature = create_pet_chat_feature(w, controller, api_key=api_key)
except Exception:
    w.chat_feature = None  # 聊天功能不可用，其他功能正常
```

**方案 3：升級 API 配額**
- 前往 [Google Cloud Console](https://console.cloud.google.com/)
- 設定付費帳號以提高配額限制

**重要：** ✅ **Line 行事曆提醒不受影響**
- Line 提醒功能使用的是 Line Messaging API，與 Gemini 無關
- 即使 Gemini 配額超限，Line 提醒仍會正常運作

---

### Q2: Line 提醒發送失敗 (DNS 解析錯誤)

**問題訊息：**
```
Failed to resolve 'api.line.biz' ([Errno 11001] getaddrinfo failed)
```

**原因：**
- ✅ 已修復：之前的 API 端點錯誤（用了 `api.line.biz` 而不是 `api.line.me`）

**解決方案：**
1. **更新 `line_reminder.py`** - 確保使用正確的端點：
   ```python
   self.line_api_url = 'https://api.line.me/v2/bot/message/push'
   ```
   
2. **重新啟動程式：**
   ```bash
   python pet.py
   ```

3. **檢查網際網路連接：**
   ```bash
   ping api.line.me
   ```
   應該能連接到 Line 伺服器

---

### Q3: 寵物 AI 聊天不工作

**答：** 需要設定 Google Gemini API 密鑰
1. 前往 [Google AI Studio](https://aistudio.google.com/) 建立免費 API 密鑰
2. 打開 `pet_settings.json`
3. 填入密鑰：
```json
{"gemini_api_key": "your-key-here"}
```
4. 重新啟動程式

如果仍然出現「配額超限」錯誤，請參考上面的 **Q1 解決方案**

---

### Q4: 如何改變 GUI 顏色主題

**答：** 編輯 `gui2.py` 或 `pomodoro_feature.py` 中的顏色設定

```python
# 修改霓虹顏色調色板
ACTIVITY_NEON_PALETTE = [
    QtGui.QColor(0, 255, 200),    # 青色
    QtGui.QColor(0, 200, 255),    # 藍色
    QtGui.QColor(255, 140, 110),  # 橙色
    # ... 添加更多顏色
]
```

---

### Q5: 如何新增新功能

**答：** 建議步驟
1. 建立新的 Python 檔案（如 `new_feature.py`）
2. 在 `gui2.py` 中導入新模組
3. 在 `create_sage_windows()` 函數中加入新標籤頁
4. 在新檔案中定義功能類別

**範例：**
```python
# 在 gui2.py 中
from new_feature import NewFeaturePanel

# 在 create_sage_windows() 中
new_tab = NewFeaturePanel(compact_mode=compact_mode)
main_window.addTab(new_tab, "新功能")
```

---

### Q6: 如何備份或轉移我的數據

**答：** 只需複製 JSON 檔案
- `session_records.json` - 番茄鐘記錄
- `todo_records.json` - 待辦清單
- `calendar_events.json` - 行事曆事件
- `status_options.json` - 活動類別
- `book_categories.json` - 書單

將這些檔案複製到新電腦的相同位置即可。

---

### Q7: 寵物在多螢幕上位置不對

**答：** 編輯 `pet.py` 中的位置設定

```python
# 在 PetWindow.__init__ 中修改
self.move(100, 100)  # 改為你想要的位置
```

或使用相對於螢幕邊緣的計算。

---

## 系統需求

- **Python** 3.8 以上
- **PyQt5** 5.15 以上
- **requests** 2.28.0 以上（用於 API 調用）
- **Google Gemini API 密鑰**（用於 AI 聊天）

---

## 注意事項

- 若無法安裝 `PyQt5`，可改用 `PySide6`（需修改 imports）
- 所有數據自動保存到 JSON 檔案
- 程式不需要網路連接（除非使用 AI 聊天功能）
- 建議定期備份 JSON 檔案

---

## 故障排除

**問題：GUI 沒有出現**
- 確認 PyQt5 已正確安裝：`pip list | grep PyQt5`
- 檢查是否有 Python 錯誤訊息

**問題：寵物動畫素材沒有載入**
- 檢查 `assets/walk/` 資料夾是否存在
- 確認檔案命名為 `1.png`, `2.png`...
- 檢查圖片格式是否為 PNG

**問題：任務或事件沒有保存**
- 檢查 `todo_records.json` 和 `calendar_events.json` 是否可寫入
- 確認磁碟有足夠空間

---

祝你使用愉快！🎓 有任何問題歡迎查閱本說明手冊。

