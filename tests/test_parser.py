from app.parser import parse_expense_text


def test_parse_compact_text():
    record = parse_expense_text("洗髮精藥膏681linepay康是美")

    assert record.amount == 681
    assert record.store == "康是美"
    assert record.payment_method == "LINE Pay"
    assert record.category == "生活用品"
    assert record.note == "洗髮精藥膏"


def test_parse_with_space():
    record = parse_expense_text("午餐 120 現金")

    assert record.amount == 120
    assert record.payment_method == "現金"
    assert record.category == "餐飲"
