from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

from app.parser import parse_expense_text
from app.sheets import GoogleSheetsClient

app = FastAPI(title="LINE 記帳 Bot")

channel_secret = os.getenv("LINE_CHANNEL_SECRET", "")
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")

if not channel_secret or not channel_access_token:
    raise RuntimeError("請先設定 LINE_CHANNEL_SECRET 與 LINE_CHANNEL_ACCESS_TOKEN")

handler = WebhookHandler(channel_secret)
configuration = Configuration(access_token=channel_access_token)

sheets_client = GoogleSheetsClient()


@app.get("/healthz", response_class=PlainTextResponse)
def healthz() -> str:
    return "ok"


@app.post("/callback")
async def callback(request: Request):
    signature = request.headers.get("X-Line-Signature", "")
    body = await request.body()
    body_text = body.decode("utf-8")

    try:
        handler.handle(body_text, signature)
    except InvalidSignatureError as exc:
        raise HTTPException(status_code=400, detail="Invalid signature") from exc

    return "OK"


@handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event: MessageEvent):
    raw_text = event.message.text.strip()
    user_id = event.source.user_id or "unknown"

    with ApiClient(configuration) as api_client:
        line_api = MessagingApi(api_client)

        try:
            profile = line_api.get_profile(user_id)
            user_name = profile.display_name
        except Exception:
            user_name = "unknown"

        try:
            expense = parse_expense_text(raw_text)
            sheets_client.append_expense(user_id=user_id, user_name=user_name, expense=expense)
            reply = (
                "✅ 已記錄\n"
                f"分類：{expense.category}\n"
                f"店家：{expense.store or '未辨識'}\n"
                f"記事：{expense.note}\n"
                f"金額：{expense.amount}\n"
                f"支付：{expense.payment_method or '未辨識'}"
            )
        except ValueError as exc:
            reply = f"⚠️ 格式錯誤：{exc}"
        except Exception as exc:  # noqa: BLE001
            reply = f"❌ 寫入失敗：{exc}"

        line_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply)],
            )
        )
