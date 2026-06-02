import unittest
from pathlib import Path
from unittest.mock import patch

from energyplus_transition.energyplus_path import EnergyPlusPath

# EnergyPlusPath is entirely based on an existing installation, so it doesn't make it easy to unit test on a standalone
# machine without Installing E+ itself


class TestEnergyPlusPath(unittest.TestCase):
    def test_basic_invalid_path(self) -> None:
        ep = EnergyPlusPath("")
        self.assertFalse(ep.valid_install)
        self.assertIsInstance(str(ep), str)

    def test_auto_find(self) -> None:
        found = EnergyPlusPath.try_to_auto_find()
        self.assertTrue(found is None or isinstance(found, Path))  # just check the interface

    def test_auto_find_darwin(self) -> None:
        with patch("energyplus_transition.energyplus_path.platform", "darwin"):
            found = EnergyPlusPath.try_to_auto_find()
            self.assertTrue(found is None or isinstance(found, Path))

    def test_auto_find_windows(self) -> None:
        with patch("energyplus_transition.energyplus_path.platform", "win32"):
            found = EnergyPlusPath.try_to_auto_find()
            self.assertTrue(found is None or isinstance(found, Path))

    def test_parse_version_valid_mac(self) -> None:
        eplus_root_path = Path("/Applications/EnergyPlus-8-5-0")
        version, path = EnergyPlusPath.parse_version(path=eplus_root_path, mute=True)
        self.assertEqual(8.5, version)
        self.assertEqual(eplus_root_path, path)

    def test_parse_version_eplus_root_path_windows(self) -> None:
        eplus_root_path = Path("C:/EnergyPlusV8-5-0")
        version, path = EnergyPlusPath.parse_version(path=eplus_root_path, mute=True)
        self.assertEqual(8.5, version)
        self.assertEqual(eplus_root_path, path)

    def test_parse_version_eplus_root_path_linux(self) -> None:
        eplus_root_path = Path("/usr/local/EnergyPlus-8-5-0")
        version, path = EnergyPlusPath.parse_version(path=eplus_root_path, mute=True)
        self.assertEqual(8.5, version)
        self.assertEqual(eplus_root_path, path)

    def test_parse_version_invalid_no_dashes(self) -> None:
        eplus_root_path = Path("/Applications/EnergyPlus-TestBuild")
        version, _ = EnergyPlusPath.parse_version(path=eplus_root_path, mute=True)
        self.assertIsNone(version)

    def test_parse_version_invalid_with_dashes(self) -> None:
        eplus_root_path = Path("/Applications/EnergyPlus-Test-Build-1")
        version, _ = EnergyPlusPath.parse_version(path=eplus_root_path, mute=True)
        self.assertIsNone(version)

    def test_parse_version_invalid_not_eplus(self) -> None:
        eplus_root_path = Path("/Applications/SomethingElseCompletely-8-5-0")
        version, _ = EnergyPlusPath.parse_version(path=eplus_root_path, mute=True)
        self.assertIsNone(version)

#     def test_proper_path_no_trailing_slash(self) -> None:
#         eight_one = EnergyPlusPath('/Applications/EnergyPlus-8-1-0')
#         self.assertEqual(eight_one, '8-1-0')
#
#     def test_proper_path_with_trailing_slash(self) -> None:
#         eight_one = EnergyPlusPath.get_version_number_from_path('/Applications/EnergyPlus-8-1-0/')
#         self.assertEqual(eight_one, '8-1-0')
#
#     def test_bad_path_with_enough_tokens(self) -> None:
#         eight_one = EnergyPlusPath.get_version_number_from_path('/usr/local/EnergyPlus-8-1-0')
#         self.assertIsNone(eight_one)
#
#     def test_bad_path_not_enough_tokens(self) -> None:
#         with self.assertRaises(IndexError):
#             EnergyPlusPath.get_version_number_from_path('/EnergyPlus-8-1-0')
#
#
# class TestGetPathFromVersionNumber(unittest.TestCase):
#     """The function tested here is quite dumb, just a concatenation wrapper, so it accepts anything"""
#     def test_valid_version_number(self) -> None:
#         path = EnergyPlusPath.get_path_from_version_number('8-5-0')
#         self.assertEqual(path, '/Applications/EnergyPlus-8-5-0')
#
#     def test_none_version_number(self) -> None:
#         path = EnergyPlusPath.get_path_from_version_number(None)
#         self.assertEqual(path, '/Applications/EnergyPlus-None')
#
#     def test_other_version_number(self) -> None:
#         path = EnergyPlusPath.get_path_from_version_number('SOMETHINGELSE')
#         self.assertEqual(path, '/Applications/EnergyPlus-SOMETHINGELSE')
#
#
# class TestGetLatestEPlusVersion(unittest.TestCase):
#     pass  # we'd have to install E+ on the test machine...
#
#
# class TestGetTransitionRunDir(unittest.TestCase):
#     def test_valid_install_dir(self) -> None:
#         path = EnergyPlusPath.get_transition_run_dir('/Applications/EnergyPlus-8-5-0')
#         self.assertEqual(path, '/Applications/EnergyPlus-8-5-0/PreProcess/IDFVersionUpdater')
#
#     def test_slashed_install_dir(self) -> None:
#         path = EnergyPlusPath.get_transition_run_dir('/Applications/EnergyPlus-8-5-0/')
#         self.assertEqual(path, '/Applications/EnergyPlus-8-5-0/PreProcess/IDFVersionUpdater')
#
#     def test_other_install_dir(self) -> None:
#         path = EnergyPlusPath.get_transition_run_dir('/path/to/ep')
#         self.assertEqual(path, '/path/to/ep/PreProcess/IDFVersionUpdater')


class TestGetTransitionsAvailable(unittest.TestCase):
    pass  # we'd have to install E+ on the test machine...
