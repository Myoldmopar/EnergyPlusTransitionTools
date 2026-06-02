import stat
import textwrap
from collections.abc import Generator
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from energyplus_transition.energyplus_path import EnergyPlusPath
from energyplus_transition.international import Language, set_language
from energyplus_transition.transition_binary import TransitionBinary

FAKE_TRANSITION_SCRIPT = textwrap.dedent(
    """\
    #!/usr/bin/env python3
    import sys
    import re
    from pathlib import Path

    idf_path = Path(sys.argv[1])

    # Determine target version from this script's name: Transition-VX-X-X-to-VY-Y-Y
    # (done early so we can use it in the audit content)
    script_name = Path(sys.argv[0]).name
    source_token = script_name.split('-V')[1].split('-to-')[0].split('-')
    target_token = script_name.split('-to-V')[1].split('-')
    source_version_str = f"{source_token[0]}.{source_token[1]}"
    target_version_str = f"{target_token[0]}.{target_token[1]}"

    # Write transition artifacts to cwd (the run_dir)
    audit_content = (
        f"Conversion {source_version_str} => {target_version_str}\\n"
        f" Starting new Transition.audit\\n"
        f" Will create new full IDFs\\n"
        f" Will create new IDF lines with units where applicable\\n"
        f" Will create new IDF lines leaving blank incoming fields as blank (no default fill)\\n"
        f" Processing IDF -- {sys.argv[1]}\\n"
    )
    Path('Transition.audit').write_text(audit_content)
    Path('Energy+.ini').write_text('[Program]\\nResultsFile=audit\\n')

    # Read and bump the VERSION object in the IDF
    content = idf_path.read_text()
    new_content = re.sub(
        r'(Version\\s*,\\s*)[\\d.]+(\\s*;)',
        lambda m: f"{m.group(1)}{target_version_str}{m.group(2)}",
        content,
        flags=re.IGNORECASE,
    )

    idf_path.with_suffix('.idfold').write_text(content)
    idf_path.with_suffix('.idfnew').write_text(new_content)
    idf_path.write_text(new_content)
"""
)


def _make_fake_transition_binary(transition_dir: Path, source_ver: str, target_ver: str) -> TransitionBinary:
    binary_path = transition_dir / f"Transition-V{source_ver}-to-V{target_ver}"
    binary_path.write_text(FAKE_TRANSITION_SCRIPT)
    binary_path.chmod(binary_path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    tb = TransitionBinary(full_path=binary_path)
    tb.source_version_idd_path.write_text(f"V{source_ver}-Energy+.idd")
    tb.target_version_idd_path.write_text(f"V{target_ver}-Energy+.idd")
    tb.report_variables_path.write_text(f"Report Variables {source_ver} to {target_ver}.csv")
    return tb


@pytest.fixture
def fake_eplus_install() -> Generator:
    tmp_dirs: list[TemporaryDirectory] = []

    def _make(versions: list[tuple[str, str]]) -> EnergyPlusPath:
        tmp = TemporaryDirectory()
        tmp_dirs.append(tmp)
        install_dir = Path(tmp.name)

        energyplus_exe = install_dir / "energyplus"
        energyplus_exe.write_text("#!/bin/sh\necho 'EnergyPlus, Version 25.1.0-abc123'\n")
        energyplus_exe.chmod(energyplus_exe.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

        transition_dir = install_dir / "PreProcess" / "IDFVersionUpdater"
        transition_dir.mkdir(parents=True)

        for source_ver, target_ver in versions:
            _make_fake_transition_binary(transition_dir, source_ver, target_ver)

        return EnergyPlusPath(install_root=install_dir)

    yield _make

    for tmp in tmp_dirs:
        tmp.cleanup()


@pytest.fixture(autouse=True)
def reset_language() -> None:
    set_language(Language.English)
