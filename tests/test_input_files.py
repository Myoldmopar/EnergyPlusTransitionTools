import tempfile
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from energyplus_transition.input_files import (
    cleanup_transition_artifacts,
    get_idf_version,
    get_selected_input_files,
    resolve_input_paths,
)


class TestGetIDFVersion(unittest.TestCase):
    def setUp(self) -> None:
        self.idf_name = tempfile.mktemp()

    def test_good_version_number(self) -> None:
        with open(self.idf_name, "w") as f:
            f.write("Version,8.5.0;")
        version = get_idf_version(path_to_idf=Path(self.idf_name))
        self.assertEqual(version, 8.5)

    def test_good_version_number_with_comments_and_blank_lines(self) -> None:
        with open(self.idf_name, "w") as f:
            f.write("! This is a comment\n\nVersion,  ! inline comment\n  8.5.0;")
        version = get_idf_version(path_to_idf=Path(self.idf_name))
        self.assertEqual(version, 8.5)

    def test_bad_version_number(self) -> None:
        with open(self.idf_name, "w") as f:
            f.write("Version,x.y.z;")
        with self.assertRaises(ValueError):
            get_idf_version(path_to_idf=Path(self.idf_name))

    def test_missing_version_number(self) -> None:
        with open(self.idf_name, "w") as f:
            f.write("x,y;")
        version = get_idf_version(path_to_idf=Path(self.idf_name))
        self.assertIsNone(version)


class TestResolveInputPaths(unittest.TestCase):
    def test_plain_idf_files(self) -> None:
        paths = [Path("/some/file.idf"), Path("/other/file.imf")]
        self.assertEqual(resolve_input_paths(paths), paths)

    def test_lst_file_relative_paths(self) -> None:
        with TemporaryDirectory() as tmp:
            lst_dir = Path(tmp)
            idf_a = lst_dir / "a.idf"
            idf_b = lst_dir / "b.idf"
            lst_file = lst_dir / "files.lst"
            lst_file.write_text("a.idf\nb.idf\n")
            result = resolve_input_paths([lst_file])
            self.assertEqual(result, [idf_a, idf_b])

    def test_lst_file_absolute_paths(self) -> None:
        with TemporaryDirectory() as tmp:
            lst_dir = Path(tmp)
            abs_path = Path("/absolute/path/file.idf")
            lst_file = lst_dir / "files.lst"
            lst_file.write_text(str(abs_path) + "\n")
            result = resolve_input_paths([lst_file])
            self.assertEqual(result, [abs_path])

    def test_lst_file_ignores_blank_lines(self) -> None:
        with TemporaryDirectory() as tmp:
            lst_dir = Path(tmp)
            lst_file = lst_dir / "files.lst"
            lst_file.write_text("a.idf\n\n  \nb.idf\n")
            result = resolve_input_paths([lst_file])
            self.assertEqual(result, [lst_dir / "a.idf", lst_dir / "b.idf"])


class TestGetSelectedInputFiles(unittest.TestCase):
    def test_valid_file(self) -> None:
        with TemporaryDirectory() as tmp:
            idf = Path(tmp) / "test.idf"
            idf.write_text("Version,8.5.0;")
            messages: list[str] = []
            result = get_selected_input_files([idf], on_msg=messages.append)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0].path, idf)
            self.assertEqual(result[0].version, 8.5)
            self.assertEqual(messages, [])

    def test_missing_file_skipped(self) -> None:
        messages: list[str] = []
        result = get_selected_input_files([Path("/nonexistent/file.idf")], on_msg=messages.append)
        self.assertEqual(result, [])
        self.assertEqual(len(messages), 1)
        self.assertIn("not found", messages[0])


class TestCleanupTransitionArtifacts(unittest.TestCase):
    def test_removes_artifacts(self) -> None:
        with TemporaryDirectory() as tmp:
            idf = Path(tmp) / "test.idf"
            idf.write_text("Version,24.1;")
            for suffix in (".idfnew", ".idfold", ".imfnew", ".imfold", ".rvinew", ".rviold"):
                idf.with_suffix(suffix).write_text("artifact")
            cleanup_transition_artifacts(idf)
            for suffix in (".idfnew", ".idfold", ".imfnew", ".imfold", ".rvinew", ".rviold"):
                self.assertFalse(idf.with_suffix(suffix).exists())
            self.assertTrue(idf.exists())

    def test_no_artifacts_present(self) -> None:
        with TemporaryDirectory() as tmp:
            idf = Path(tmp) / "test.idf"
            idf.write_text("Version,24.1;")
            cleanup_transition_artifacts(idf)  # should not raise
            self.assertTrue(idf.exists())
