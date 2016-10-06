import os
import sys
import unittest

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'IDFVersionUpdater'))

from EnergyPlusPath import EnergyPlusPath


class TestGetVersionNumberFromPath(unittest.TestCase):
    def test_proper_path_no_trailing_slash(self):
        eight_one = EnergyPlusPath.get_version_number_from_path('/Applications/EnergyPlus-8-1-0')
        self.assertEqual(eight_one, '8-1-0')

    def test_proper_path_with_trailing_slash(self):
        eight_one = EnergyPlusPath.get_version_number_from_path('/Applications/EnergyPlus-8-1-0/')
        self.assertEqual(eight_one, '8-1-0')

    def test_bad_path_with_enough_tokens(self):
        eight_one = EnergyPlusPath.get_version_number_from_path('/usr/local/EnergyPlus-8-1-0')
        self.assertIsNone(eight_one)

    def test_bad_path_not_enough_tokens(self):
        with self.assertRaises(IndexError):
            EnergyPlusPath.get_version_number_from_path('/EnergyPlus-8-1-0')


class TestGetPathFromVersionNumber(unittest.TestCase):
    """The function tested here is quite dumb, just a concatenation wrapper, so it accepts anything"""
    def test_valid_version_number(self):
        path = EnergyPlusPath.get_path_from_version_number('8-5-0')
        self.assertEqual(path, '/Applications/EnergyPlus-8-5-0')

    def test_none_version_number(self):
        path = EnergyPlusPath.get_path_from_version_number(None)
        self.assertEqual(path, '/Applications/EnergyPlus-None')

    def test_other_version_number(self):
        path = EnergyPlusPath.get_path_from_version_number('SOMETHINGELSE')
        self.assertEqual(path, '/Applications/EnergyPlus-SOMETHINGELSE')


class TestGetLatestEPlusVersion(unittest.TestCase):
    pass  # we'd have to install E+ on the test machine...


class TestGetTransitionRunDir(unittest.TestCase):
    def test_valid_install_dir(self):
        path = EnergyPlusPath.get_transition_run_dir('/Applications/EnergyPlus-8-5-0')
        self.assertEqual(path, '/Applications/EnergyPlus-8-5-0/PreProcess/IDFVersionUpdater')

    def test_slashed_install_dir(self):
        path = EnergyPlusPath.get_transition_run_dir('/Applications/EnergyPlus-8-5-0/')
        self.assertEqual(path, '/Applications/EnergyPlus-8-5-0/PreProcess/IDFVersionUpdater')

    def test_other_install_dir(self):
        path = EnergyPlusPath.get_transition_run_dir('/path/to/ep')
        self.assertEqual(path, '/path/to/ep/PreProcess/IDFVersionUpdater')


class TestGetTransitionsAvailable(unittest.TestCase):
    pass  # we'd have to install E+ on the test machine...
