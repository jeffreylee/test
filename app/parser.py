from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


PAYMENT_KEYWORDS = {
    "linepay": "LINE Pay",
    "line pay": "LINE Pay",
    "line": "LINE Pay",
    "cash": "現金",
    "現金": "現金",
    "信用卡": "信用卡",
    "刷卡": "信用卡",
    "jkopay": "街口支付",
    "街口": "街口支付",
    "applepay": "Apple Pay",
    "apple pay": "Apple Pay",
}

STORE_KEYWORDS = [
    "康是美",
    "屈臣氏",
    "全聯",
    "家樂福",
    "7-11",
    "全家",
    "momo",
    "蝦皮",
]

CATEGORY_KEYWORDS = {
    "生活用品": ["洗髮", "牙膏", "藥膏", "清潔", "康是美", "屈臣氏"],
    "餐飲": ["便當", "午餐", "晚餐", "早餐", "咖啡", "餐"],
    "交通": ["捷運", "高鐵", "台鐵", "uber", "taxi", "公車", "停車"],
    "娛樂": ["電影", "遊戲", "netflix", "spotify"],
    "醫療": ["掛號", "診所", "藥", "醫院"],
    "其他": [],
}


@dataclass
class ExpenseRecord:
    raw_text: str
    category: str
    store: Optional[str]
    note: str
    amount: int
    payment_method: Optional[str]


def _find_payment(text: str) -> Optional[str]:
    normalized = text.lower()
    for keyword in sorted(PAYMENT_KEYWORDS, key=len, reverse=True):
        if keyword in normalized:
            return PAYMENT_KEYWORDS[keyword]
    return None


def _find_store(text: str) -> Optional[str]:
    lowered = text.lower()
    for store in STORE_KEYWORDS:
        if store.lower() in lowered:
            return store
    return None


def _guess_category(note: str, store: Optional[str]) -> str:
    haystack = f"{note} {store or ''}".lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword.lower() in haystack for keyword in keywords):
            return category
    return "其他"


def _clean_note(text: str, amount: int, payment_method: Optional[str], store: Optional[str]) -> str:
    cleaned = text
    cleaned = re.sub(r"\d+", "", cleaned)

    if payment_method:
        for key, value in PAYMENT_KEYWORDS.items():
            if value == payment_method:
                cleaned = re.sub(key, "", cleaned, flags=re.IGNORECASE)

    if store:
        cleaned = cleaned.replace(store, "")

    cleaned = re.sub(r"[\s,，。]+", "", cleaned)
    return cleaned.strip() or "未提供記事"


def parse_expense_text(text: str) -> ExpenseRecord:
    if not text or not text.strip():
        raise ValueError("輸入內容不可為空")

    amount_match = re.search(r"(\d{1,7})(?!.*\d)", text)
    if not amount_match:
        raise ValueError("找不到金額，請至少輸入一組數字，例如：午餐150現金")

    amount = int(amount_match.group(1))
    payment_method = _find_payment(text)
    store = _find_store(text)
    note = _clean_note(text, amount, payment_method, store)
    category = _guess_category(note, store)

    return ExpenseRecord(
        raw_text=text,
        category=category,
        store=store,
        note=note,
        amount=amount,
        payment_method=payment_method,
    )
