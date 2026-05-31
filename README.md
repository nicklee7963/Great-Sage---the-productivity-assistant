# 🎓 大賢者（Great Sage）- 生產力助手

一個集番茄鐘、行事曆、待辦清單、桌面寵物為一體的完整生產力工具。
透過可愛的桌面寵物提醒你各項任務，幫助你專注工作、記錄進度、管理時間。

**主要功能：**
- ⏲️ **番茄鐘計時器** - 自訂時間、活動分類、時間統計
- 📅 **行事曆與日程** - 日程規劃、作息安排、日期檢視
- ✓ **待辦清單** - 優先度分類、狀態追蹤、進度管理
- 🐾 **桌面寵物助手** - AI 聊天、動畫互動、智慧提醒

此專案以 Python 實作完整桌面體驗（純 PyQt5，無需瀏覽器）。

---

## 📖 目錄
1. [快速開始](#快速開始)
2. [必要安裝套件](#必要安裝套件)
3. [API 設置](#api-設置)
4. [程式碼檔案說明](#程式碼檔案說明)
5. [功能使用指南](#功能使用指南)
6. [數據檔案與自訂](#數據檔案與自訂)
7. [常見問題](#常見問題)

---

## 快速開始

### 1. 基本安裝

```bash
# 克隆或下載本專案
git clone https://github.com/yourusername/Great-Sage---the-productivity-assistant.git
cd Great-Sage---the-productivity-assistant

# 安裝所有依賴套件
python -m pip install -r requirements.txt
```

### 2. 準備桌面寵物動畫

把走路動畫圖片放在 `assets/walk/`，並依序命名為 `1.png`、`2.png`、`3.png` ...

例如：
```
assets/
└── walk/
    ├── 1.png
    ├── 2.png
    ├── 3.png
    └── 4.png
```

### 3. 配置 API（可選但推薦）

大賢者的高級功能需要設置 API，詳見下方 [API 設置](#api-設置) 部分。

### 4. 啟動大賢者

```bash
python pet.py
```

點擊桌面寵物會打開完整的生產力 GUI。

---

## 必要安裝套件

### 核心依賴

以下套件在 `requirements.txt` 中定義，執行 `pip install -r requirements.txt` 自動安裝：

| 套件 | 版本 | 用途 | 說明 |
|------|------|------|------|
| **PyQt5** | ≥5.15 | 桌面 GUI 框架 | 提供跨平台 GUI 介面、視窗管理、事件系統 |
| **requests** | ≥2.28.0 | HTTP 客戶端 | 用於調用 Google Gemini API 和 LINE Bot API |

### 額外依賴（系統層級）

- **Python 3.8+** - 推薦 Python 3.10 以上
- **Windows/macOS/Linux** - 支持所有主流作業系統

### 檢查安裝

驗證依賴是否正確安裝：

```bash
python -c "import PyQt5; import requests; print('✓ 所有依賴安裝成功')"
```

---

## API 設置

大賢者提供兩個可選的 API 集成功能，增強使用體驗：

### 🤖 Google Gemini API（寵物聊天功能）

#### 功能說明
- 寵物可與你進行自然流暢的對話
- 寵物主動根據你的行程、書單提醒你
- 提供溫暖、個性化的互動體驗

#### 獲取 API 密鑰

1. **訪問 Google AI Studio**
   - 前往 [Google AI Studio](https://aistudio.google.com/apikey)
   - 使用你的 Google 帳號登入

2. **創建 API 密鑰**
   - 點擊「Create API key」
   - 選擇「Create API key in new project」
   - 系統會自動生成一個免費 API 密鑰

3. **啟用必要的 API**
   - 確保已啟用「Generative Language API」
   - 免費配額：每分鐘 60 個請求（足夠日常使用）

#### 設置方式

**方式 A：首次運行時輸入（推薦）**
1. 首次運行 `python pet.py` 時，系統會提示輸入 API 密鑰
2. 輸入你的 Gemini API 密鑰
3. 密鑰會自動保存到 `pet_settings.json`

**方式 B：手動配置**
1. 在項目根目錄創建或編輯 `pet_settings.json`
2. 添加以下內容：

```json
{
  "api_key": "your-gemini-api-key-here"
}
```

3. 重新啟動 `python pet.py`

#### 測試連接

```bash
python -c "
import json
from pathlib import Path
settings_file = Path('pet_settings.json')
if settings_file.exists():
    with open(settings_file) as f:
        settings = json.load(f)
        print(f'✓ API 密鑰已配置: {settings.get(\"api_key\", \"未找到\")[:20]}...')
else:
    print('⚠ 尚未設置 API 密鑰')
"
```

#### 模型選擇

系統使用 **Gemini 2.0 Flash** 模型（最新、最快、免費）：
- 超快的回應速度
- 日常對話效果優秀
- 完全免費使用

如需更改模型，編輯 `pet_chat_feature.py`：
```python
DEFAULT_GEMINI_MODEL = 'gemini-2.0-flash'  # 可改為其他模型如 'gemini-1.5-pro'
```

---

### 📱 LINE Bot API（行事曆提醒功能）

#### 功能說明
- 行事曆事件開始前 5 分鐘透過 LINE 發送提醒
- 自動監控 `calendar_events.json` 中的所有事件
- 避免重複提醒，確保提醒準確可靠

#### 創建 LINE Bot

1. **訪問 LINE Developers Console**
   - 前往 [LINE Developers](https://developers.line.biz/zh-hant/)
   - 登入或創建 LINE 帳號

2. **創建 Provider（提供者）**
   - 點擊「Create new provider」
   - 輸入提供者名稱（例如：「大賢者提醒系統」）
   - 接受服務條款，點擊「Create」

3. **創建 Channel（頻道）**
   - 在新建的 Provider 下，點擊「Create a new channel」
   - 選擇 Channel type：**Messaging API**
   - 填寫以下信息：
     - **Channel name**：「大賢者行事曆提醒」
     - **Description**：「個人生產力助手的行事曆提醒 Bot」
     - **Category**：「Utilities」
     - 勾選「I agree to the LINE Channel Agreement」
   - 點擊「Create」

#### 獲取必要認證信息

1. **Channel Access Token**
   - 進入新建的 Channel
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

