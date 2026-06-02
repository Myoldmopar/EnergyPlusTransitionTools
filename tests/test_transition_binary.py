import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from energyplus_transition.transition_binary import TransitionBinary, prepare_transition_directory


def fake_having_transition_binary(base_path: Path, source_version: str, target_version: str) -> TransitionBinary:
    """Create a helper TransitionBinary object with the expected support files in place.

    :param source_version: The source version string, in the form '8-6-0'
    :param target_version: The target version string, in the form '8-7-0'
    """
    tb = TransitionBinary(full_path=base_path / f"Transition-V{source_version}-to-V{target_version}")
    tb.source_version_idd_path.write_text(f"V{source_version}-Energy+.idd")
    tb.target_version_idd_path.write_text(f"V{target_version}-Energy+.idd")
    tb.report_variables_path.write_text(f"Report Variables {source_version} to {target_version}.csv")
    return tb


class TestTransitionBinary(unittest.TestCase):
    def test_good_transition_object(self) -> None:
        valid_path = Path("/Applications/EnergyPlus-8-5-0/PreProcess/IDFVersionUpdater/Transition-V8-5-0-to-V8-6-0")
        valid_object = TransitionBinary(valid_path)
        self.assertEqual(valid_object.full_path_to_binary, valid_path)
        self.assertEqual(valid_object.binary_name, "Transition-V8-5-0-to-V8-6-0")
        self.assertEqual(valid_object.source_version, 8.5)
        self.assertEqual(valid_object.target_version, 8.6)
        self.assertIsInstance(str(valid_object), str)

        self.assertEqual(
            valid_object.source_version_idd_path, valid_object.full_path_to_binary.parent / "V8-5-0-Energy+.idd"
        )
        self.assertEqual(
            valid_object.target_version_idd_path, valid_object.full_path_to_binary.parent / "V8-6-0-Energy+.idd"
        )
        self.assertEqual(
            valid_object.report_variables_path,
            valid_object.full_path_to_binary.parent / "Report Variables 8-5-0 to 8-6-0.csv",
        )
        if not valid_path.exists():
            self.assertFalse(valid_object.has_support_files())

    def test_transition_object_just_file_name(self) -> None:
        just_file_name = "Transition-V8-5-0-to-V8-6-0"
        just_file_name_object = TransitionBinary(Path(just_file_name))
        self.assertEqual(just_file_name_object.full_path_to_binary, Path(just_file_name))
        self.assertEqual(just_file_name_object.binary_name, "Transition-V8-5-0-to-V8-6-0")
        self.assertEqual(just_file_name_object.source_version, 8.5)
        self.assertEqual(just_file_name_object.target_version, 8.6)

    def test_bad_transition_object(self) -> None:
        invalid_path = "/Applications/EnergyPlus-8-5-0/PreProcess/IDFVersionUpdater/BadBinaryName"
        with self.assertRaises(Exception):
            TransitionBinary(Path(invalid_path))

    def test_repr(self) -> None:
        valid_path = Path("/Applications/EnergyPlus-8-5-0/PreProcess/IDFVersionUpdater/Transition-V8-5-0-to-V8-6-0")
        obj = TransitionBinary(valid_path)
        self.assertIn("8.5", repr(obj))
        self.assertIn("8.6", repr(obj))

    def test_prepare_transition_directory(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            idd_dir = Path(tmp_dir)

            transitions = [
                fake_having_transition_binary(base_path=idd_dir, source_version="8-5-0", target_version="8-6-0"),
                fake_having_transition_binary(base_path=idd_dir, source_version="8-6-0", target_version="8-7-0"),
            ]

            with prepare_transition_directory(transitions=transitions) as run_dir:
                self.assertTrue(run_dir.is_dir())
                for tb in transitions:
                    self.assertTrue((run_dir / tb.source_version_idd_path.name).exists())
                    self.assertTrue((run_dir / tb.target_version_idd_path.name).exists())
                    self.assertTrue((run_dir / tb.report_variables_path.name).exists())
