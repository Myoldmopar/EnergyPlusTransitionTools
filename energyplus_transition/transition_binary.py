import shutil
import tempfile
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path


class TransitionBinary(object):
    """
    Describe a single transition binary in the installation.

    Constructed from the full path to the binary; source and target versions are parsed from the path and filenames.

    :param full_path: Full path object to the transition binary itself

    :ivar full_path_to_binary: Copy of the full path to binary passed into the constructor
    :ivar binary_name: This is just the filename portion of the binary executable
    :ivar source_version: This is the source version of this particular transition, for example,
                          in V8-5-0-to-8-6-0, this will be 8.5
    :ivar target_version: This is the target version of this particular transition, for example,
                          in V8-5-0-to-8-6-0, this will be 8.6
    """

    def __init__(self, full_path: Path):
        self.full_path_to_binary = full_path
        self.binary_name = self.full_path_to_binary.stem
        split_by_v = self.binary_name.split("V")
        source_token = split_by_v[1].split("-")
        source_string = f"{source_token[0]}.{source_token[1]}"
        target_token = split_by_v[2].split("-")
        target_string = f"{target_token[0]}.{target_token[1]}"
        self.source_version = float(source_string)
        self.target_version = float(target_string)
        idd_dir = self.full_path_to_binary.parent
        source_ver_str = "-".join(source_token[:3])
        target_ver_str = "-".join(target_token[:3])
        self.source_version_idd_path = idd_dir / f"V{source_ver_str}-Energy+.idd"
        self.target_version_idd_path = idd_dir / f"V{target_ver_str}-Energy+.idd"
        self.report_variables_path = idd_dir / f"Report Variables {source_ver_str} to {target_ver_str}.csv"

    def has_support_files(self) -> bool:
        """Return True if both IDD files and the report variables CSV are present alongside the binary."""
        return (
            self.source_version_idd_path.is_file()
            and self.target_version_idd_path.is_file()
            and self.report_variables_path.is_file()
        )

    def __repr__(self) -> str:
        return f"TransitionBinary ({self.source_version} -> {self.target_version})"

    def __str__(self) -> str:
        return f"TransitionBinary ({self.source_version} -> {self.target_version}) - {self.full_path_to_binary}"


@contextmanager
def prepare_transition_directory(transitions: list[TransitionBinary]) -> Generator[Path, None, None]:
    """Create a temporary directory with all support files needed for the given transitions, deduplicating copies."""
    with tempfile.TemporaryDirectory() as tmp:
        run_dir = Path(tmp)
        copied: set[str] = set()
        for tr in transitions:
            for f in (tr.source_version_idd_path, tr.target_version_idd_path, tr.report_variables_path):
                if f.name not in copied and f.is_file():
                    shutil.copy(f, run_dir / f.name)
                    copied.add(f.name)
        yield run_dir
