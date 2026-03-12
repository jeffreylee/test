from __future__ import annotations

import os
from datetime import datetime

import gspread
from gspread.exceptions import WorksheetNotFound
from google.oauth2.service_account import Credentials

from app.parser import ExpenseRecord

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


class GoogleSheetsClient:
    def __init__(self) -> None:
        self.sheet_id = os.getenv("GOOGLE_SHEET_ID", "").strip()
        creds_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "service_account.json").strip()

        if not self.sheet_id:
            raise ValueError("缺少 GOOGLE_SHEET_ID 環境變數")

        creds = Credentials.from_service_account_file(creds_file, scopes=SCOPES)
        client = gspread.authorize(creds)
        self._spreadsheet = client.open_by_key(self.sheet_id)

    def _get_worksheet(self):
        title = os.getenv("GOOGLE_WORKSHEET_NAME", "expenses")
        try:
            ws = self._spreadsheet.worksheet(title)
        except WorksheetNotFound:
            ws = self._spreadsheet.add_worksheet(title=title, rows=1000, cols=12)
            ws.append_row(
                [
                    "created_at",
                    "user_id",
                    "user_name",
                    "raw_text",
                    "category",
                    "store",
                    "note",
                    "amount",
                    "payment_method",
                ]
            )
        return ws

    def append_expense(self, user_id: str, user_name: str, expense: ExpenseRecord) -> None:
        ws = self._get_worksheet()
        ws.append_row(
            [
                datetime.utcnow().isoformat(timespec="seconds"),
                user_id,
                user_name,
                expense.raw_text,
                expense.category,
                expense.store or "",
                expense.note,
                expense.amount,
                expense.payment_method or "",
            ]
        )
