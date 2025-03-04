from pathlib import Path
import unittest


# EnergyPlusPath is entirely based on an existing installation, so it doesn't make it easy to unit test on a standalone
# machine without Installing E+ itself

from energyplus_transition.energyplus_path import EnergyPlusPath


class TestEnergyPlusPath(unittest.TestCase):
    def test_basic_invalid_path(self):
        ep = EnergyPlusPath("")
        self.assertFalse(ep.valid_install)
        self.assertIsInstance(str(ep), str)

    def test_auto_find(self):
        found = EnergyPlusPath.try_to_auto_find()
        self.assertTrue(isinstance(found, Path) or Path is None)  # just check the interface

    def test_parse_version(self):
        valid = Path("/Applications/EnergyPlus-8-5-0")
        version, _ = EnergyPlusPath.parse_version(valid, mute=True)
        self.assertEqual(8.5, version)
        invalid_no_dashes = Path("/Applications/EnergyPlus-TestBuild")
        version, _ = EnergyPlusPath.parse_version(invalid_no_dashes, mute=True)
        self.assertIsNone(version)
        invalid_with_dashes = Path("/Applications/EnergyPlus-Test-Build-1")
        version, _ = EnergyPlusPath.parse_version(invalid_with_dashes, mute=True)
        self.assertIsNone(version)

#     def test_proper_path_no_trailing_slash(self):
#         eight_one = EnergyPlusPath('/Applications/EnergyPlus-8-1-0')
#         self.assertEqual(eight_one, '8-1-0')
#
#     def test_proper_path_with_trailing_slash(self):
#         eight_one = EnergyPlusPath.get_version_number_from_path('/Applications/EnergyPlus-8-1-0/')
#         self.assertEqual(eight_one, '8-1-0')
#
#     def test_bad_path_with_enough_tokens(self):
#         eight_one = EnergyPlusPath.get_version_number_from_path('/usr/local/EnergyPlus-8-1-0')
#         self.assertIsNone(eight_one)
#
#     def test_bad_path_not_enough_tokens(self):
#         with self.assertRaises(IndexError):
#             EnergyPlusPath.get_version_number_from_path('/EnergyPlus-8-1-0')
#
#
# class TestGetPathFromVersionNumber(unittest.TestCase):
#     """The function tested here is quite dumb, just a concatenation wrapper, so it accepts anything"""
#     def test_valid_version_number(self):
#         path = EnergyPlusPath.get_path_from_version_number('8-5-0')
#         self.assertEqual(path, '/Applications/EnergyPlus-8-5-0')
#
#     def test_none_version_number(self):
#         path = EnergyPlusPath.get_path_from_version_number(None)
#         self.assertEqual(path, '/Applications/EnergyPlus-None')
#
#     def test_other_version_number(self):
#         path = EnergyPlusPath.get_path_from_version_number('SOMETHINGELSE')
#         self.assertEqual(path, '/Applications/EnergyPlus-SOMETHINGELSE')
#
#
# class TestGetLatestEPlusVersion(unittest.TestCase):
#     pass  # we'd have to install E+ on the test machine...
#
#
# class TestGetTransitionRunDir(unittest.TestCase):
#     def test_valid_install_dir(self):
#         path = EnergyPlusPath.get_transition_run_dir('/Applications/EnergyPlus-8-5-0')
#         self.assertEqual(path, '/Applications/EnergyPlus-8-5-0/PreProcess/IDFVersionUpdater')
#
#     def test_slashed_install_dir(self):
#         path = EnergyPlusPath.get_transition_run_dir('/Applications/EnergyPlus-8-5-0/')
#         self.assertEqual(path, '/Applications/EnergyPlus-8-5-0/PreProcess/IDFVersionUpdater')
#
#     def test_other_install_dir(self):
#         path = EnergyPlusPath.get_transition_run_dir('/path/to/ep')
#         self.assertEqual(path, '/path/to/ep/PreProcess/IDFVersionUpdater')


class TestGetTransitionsAvailable(unittest.TestCase):
    pass  # we'd have to install E+ on the test machine...
