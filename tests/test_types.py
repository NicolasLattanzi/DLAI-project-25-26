from leveledit.types import TYPES, type_of_object, cls_of


def test_29_tipi():
    assert len(TYPES) == 29 and "~S" not in TYPES and "PP" not in TYPES


def test_oggetti_noti():
    casi = {("indoor", "D4"): "#P", ("indoor", "DE"): "DK", ("indoor", "A4"): "DK",
            ("indoor", "3F"): "#W", ("indoor", "47"): "#W", ("overworld", "20"): "#R",
            ("overworld", "5C"): "BU", ("indoor", "20"): "BV", ("indoor", "A7"): "BP",
            ("overworld", "78"): "=B", ("indoor", "01"): "~H", ("indoor", "06"): "~L",
            ("indoor", "AC"): "#F", ("indoor", "A0"): "#X"}
    for (reg, oid), atteso in casi.items():
        assert type_of_object(reg, oid) == atteso, (reg, oid)


def test_classe():
    assert cls_of("~H") == "~" and cls_of("_V") == " " and TYPES["BV"].walkable is False
