from app.services.actors import normalize_actor_name, infer_actor_type


def test_normalize_actor_name_unifies_persian_arabic_letters() -> None:
    assert normalize_actor_name("  وزارت ارتباطات و فناوري اطلاعات ") == "وزارت ارتباطات و فناوری اطلاعات"


def test_normalize_actor_name_removes_punctuation_and_spacing() -> None:
    assert normalize_actor_name("نهاد‌ الف،  ایران") == "نهاد الف ایران"


def test_infer_actor_type_detects_organization_marker() -> None:
    assert infer_actor_type("وزارت ارتباطات") == "organization"
