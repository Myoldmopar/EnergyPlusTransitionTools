from unittest import TestCase

from energyplus_transition.international import Language, report_missing_keys, set_language, translate


class TestInternational(TestCase):
    def test_missing_keys(self) -> None:
        self.assertFalse(report_missing_keys(mute=True))  # add assertion here

    def test_translaiton_english(self) -> None:
        set_language(lang=Language.English)
        self.assertEqual("", translate(key=None))  # type: ignore[arg-type]
        self.assertEqual("", translate(key=""))
        self.assertEqual("TRANSLATION MISSING", translate(key="WHAT", mute=True))
        self.assertEqual("TRANSLATION MISSING", translate(key="WHAT", mute=True))
        self.assertEqual("Close", translate(key="Close", mute=True))

    def test_translation_spanish(self) -> None:
        set_language(lang=Language.Spanish)
        self.assertEqual("", translate(key=None))  # type: ignore[arg-type]
        self.assertEqual("", translate(key=""))
        self.assertEqual("TRANSLATION MISSING", translate(key="WHAT", mute=True))
        self.assertEqual("TRANSLATION MISSING", translate(key="WHAT", mute=True))
        self.assertEqual("Cerca", translate(key="Close", mute=True))

    def test_translation_french(self) -> None:
        set_language(lang=Language.French)
        self.assertEqual("", translate(key=None))  # type: ignore[arg-type]
        self.assertEqual("", translate(key=""))
        self.assertEqual("TRANSLATION MISSING", translate(key="WHAT", mute=True))
        self.assertEqual("TRANSLATION MISSING", translate(key="WHAT", mute=True))
        self.assertEqual("Fermer", translate(key="Close", mute=True))
