import pytest

from energyplus_transition.international import Language, report_missing_keys, set_language, translate


def test_missing_keys() -> None:
    assert not report_missing_keys(mute=True)


@pytest.mark.parametrize("lang,expected_close", [
    (Language.English, "Close"),
    (Language.Spanish, "Cerca"),
    (Language.French, "Fermer"),
])
def test_translation(lang: Language, expected_close: str) -> None:
    set_language(lang=lang)
    assert translate(key=None) == ""  # type: ignore[arg-type]
    assert translate(key="") == ""
    assert translate(key="WHAT", mute=True) == "TRANSLATION MISSING"
    assert translate(key="Close", mute=True) == expected_close
