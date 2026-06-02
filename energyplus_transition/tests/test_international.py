from unittest import TestCase

from energyplus_transition.international import report_missing_keys, set_language, translate, Language


class TestInternational(TestCase):
    def test_missing_keys(self) -> None:
        self.assertFalse(report_missing_keys(mute=True))  # add assertion here

    def test_translation(self) -> None:
        set_language(Language.Spanish)
        self.assertEqual("", translate(None))  # type: ignore[arg-type]
        self.assertEqual("", translate(""))
        self.assertEqual("TRANSLATION MISSING", translate("WHAT", mute=True))
        self.assertEqual("TRANSLATION MISSING", translate("WHAT", mute=True))
        self.assertEqual("Cerca", translate("Close", mute=True))
        set_language(Language.French)
        self.assertEqual("Fermer", translate("Close", mute=True))
