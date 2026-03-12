# LINE 記帳 Bot（Python + Railway + Google Sheets）

這個專案提供一個 LINE Bot，讓使用者輸入像這樣的訊息：

`洗髮精藥膏681linepay康是美`

系統會解析並寫入 Google 試算表：
- 類別
- 店家
- 記事
- 金額
- 支付方式
- 使用人姓名（LINE 顯示名稱）

---

## 1) 功能重點

- 支援「無空白連續輸入」與一般輸入。
- 自動判斷金額（抓最後一組數字）。
- 自動辨識常見支付方式（LINE Pay / 現金 / 信用卡...）。
- 自動辨識店家（可自行擴充關鍵字）。
- 使用 LINE User ID 取得顯示名稱，寫入 Google Sheets，支援多使用者。

---

## 2) 專案結構

- `app/main.py`: FastAPI + LINE Webhook。
- `app/parser.py`: 記帳文字解析器。
- `app/sheets.py`: Google Sheets 寫入邏輯。
- `tests/test_parser.py`: 解析器測試。
- `Procfile`: Railway 啟動設定。

---

## 3) 前置需求

1. LINE Developers Channel（Messaging API）
2. Google Cloud Service Account
3. 一份 Google 試算表（先建立好）
4. Python 3.11+

---

## 4) 本機啟動（step by step）

### Step 1. 安裝依賴

```bash
pip install -r requirements.txt
```

### Step 2. 建立環境變數

```bash
cp .env.example .env
```

填入：
- `LINE_CHANNEL_SECRET`
- `LINE_CHANNEL_ACCESS_TOKEN`
- `GOOGLE_SHEET_ID`
- `GOOGLE_WORKSHEET_NAME`（可用預設 `expenses`）
- `GOOGLE_SERVICE_ACCOUNT_FILE`（預設 `service_account.json`）

### Step 3. 放入 Google 憑證

把 Google service account JSON 放在專案根目錄，例如：

`service_account.json`

### Step 4. Google 試算表授權

把試算表分享給 service account email（JSON 裡的 `client_email`）且給「編輯者」權限。

### Step 5. 啟動服務

```bash
set -a && source .env && set +a
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 5) LINE Webhook 設定

1. 將 webhook URL 設為：
   `https://<你的網域>/callback`
2. 啟用 webhook。
3. 可先用 ngrok 測試：
   `ngrok http 8000`

---

## 6) Railway 發布（step by step）

### Step 1. 建立專案

- 到 Railway 新增專案，連結此 GitHub repository。

### Step 2. 設定啟動命令

此專案已提供 `Procfile`，Railway 會自動啟動：

`uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}`

### Step 3. 設定 Railway Variables

在 Railway Variables 填入：
- `LINE_CHANNEL_SECRET`
- `LINE_CHANNEL_ACCESS_TOKEN`
- `GOOGLE_SHEET_ID`
- `GOOGLE_WORKSHEET_NAME`（可選）

### Step 4. 上傳 Google 憑證

建議做法：
1. 把 service account JSON 內容存成環境變數（如 `GOOGLE_SERVICE_ACCOUNT_JSON`）
2. 在啟動前寫成檔案 `service_account.json`

可在 Railway Start Command 前加一段：

```bash
python - <<'PY'
import os
from pathlib import Path
Path('service_account.json').write_text(os.environ['GOOGLE_SERVICE_ACCOUNT_JSON'])
print('service_account.json created')
PY
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

### Step 5. 設定 LINE Webhook

把 LINE Developers 後台 webhook URL 改成 Railway 網址：

`https://<railway-domain>/callback`

---

## 7) 輸入範例

- `洗髮精藥膏681linepay康是美`
- `午餐120現金`
- `捷運35悠遊卡`

> 目前支付方式、店家、類別關鍵字在 `app/parser.py`，可自行擴充。

---

## 8) 測試

```bash
pytest -q
```

---

## 9) 注意事項

- 若訊息沒有數字，會回覆格式錯誤。
- 若店家/支付方式無法辨識，會以「未辨識」顯示，但仍可寫入。
- `user_name` 來自 LINE profile API，若取得失敗會寫入 `unknown`。
