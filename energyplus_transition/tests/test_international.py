from unittest import TestCase

from energyplus_transition.international import report_missing_keys, set_language, translate, Language


class TestInternational(TestCase):
    def test_missing_keys(self) -> None:
        self.assertFalse(report_missing_keys(mute=True))  # add assertion here

    def test_translation(self) -> None:
        set_language(lang=Language.Spanish)
        self.assertEqual("", translate(key=None))  # type: ignore[arg-type]
        self.assertEqual("", translate(key=""))
        self.assertEqual("TRANSLATION MISSING", translate(key="WHAT", mute=True))
        self.assertEqual("TRANSLATION MISSING", translate(key="WHAT", mute=True))
        self.assertEqual("Cerca", translate(key="Close", mute=True))
        set_language(lang=Language.French)
        self.assertEqual("Fermer", translate(key="Close", mute=True))
