import os
import sys
import unittest
# import threading
# TODO: Lots more testing


# add the source directory to the path so the unit test framework can find it
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'IDFVersionUpdater'))


from EnergyPlusPath import EnergyPlusPath
# from EnergyPlusThread import EnergyPlusThread


class TestEnergyPlusPaths(unittest.TestCase):
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


# class TestEnergyPlusThread(unittest.TestCase):
#     def test_construction(self):
#         paths = ['/dummy/', '/path', '/to_nothing']
#         obj = EnergyPlusThread(paths[0], paths[1], paths[2], None, None, None, None)
#         self.assertTrue(isinstance(obj, threading.Thread))
#         self.assertTrue(obj.run_script, paths[0])
#         self.assertTrue(obj.input_file, paths[1])
#         self.assertTrue(obj.weather_file, paths[2])


# allow execution directly as python tests/test_ghx.py
if __name__ == '__main__':
    unittest.main()
