from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from pytest import CaptureFixture, MonkeyPatch

from energyplus_transition.cli import Runner, main
from energyplus_transition.input_files import get_idf_version
from tests.types import FakeEplusInstall


def test_runner_defaults() -> None:
    r = Runner()
    assert not r.verbose
    assert not r.progress
    assert r.jobs > 0


def test_runner_on_msg_silent_without_verbose(capsys: CaptureFixture[str]) -> None:
    Runner(verbose=False).on_msg("hello")
    assert capsys.readouterr().out == ""


def test_runner_on_msg_prints_when_verbose(capsys: CaptureFixture[str]) -> None:
    Runner(verbose=True).on_msg("hello")
    assert "hello" in capsys.readouterr().out


def test_runner_on_increment_tracks_progress() -> None:
    r = Runner()
    r.on_increment()
    r.on_increment()
    assert r.progress_transitions == 2


def test_runner_on_done_tracks_files() -> None:
    r = Runner()
    r.num_total_files = 2
    r.on_done("done")
    assert r.progress_files == 1


def test_runner_on_done_verbose(capsys: CaptureFixture[str]) -> None:
    r = Runner(verbose=True)
    r.num_total_files = 1
    r.num_total_transitions = 2
    r.on_done("all done")
    out = capsys.readouterr().out
    assert "Done:" in out
    assert "1/1" in out


def test_runner_collect_runs(fake_eplus_install: FakeEplusInstall) -> None:
    eplus = fake_eplus_install([("24-1-0", "24-2-0"), ("24-2-0", "25-1-0")])
    with TemporaryDirectory() as tmp:
        idf = Path(tmp) / "test.idf"
        idf.write_text("Version,24.1;")
        r = Runner()
        r.collect_runs(eplus_install=eplus, input_paths=[idf], save_intermediate=False)
        assert len(r.runs) == 1
        assert r.num_total_files == 1
        assert r.num_total_transitions == 2


def test_runner_collect_runs_skips_unknown_version(fake_eplus_install: FakeEplusInstall) -> None:
    eplus = fake_eplus_install([("24-1-0", "24-2-0")])
    with TemporaryDirectory() as tmp:
        idf = Path(tmp) / "test.idf"
        idf.write_text("Version,23.1;")
        msgs: list[str] = []
        r = Runner(verbose=True)
        r.on_msg = lambda m: msgs.append(m)  # type: ignore[assignment]
        r.collect_runs(eplus_install=eplus, input_paths=[idf], save_intermediate=False)
        assert len(r.runs) == 0
        assert any("not supported" in m for m in msgs)


def test_runner_collect_runs_version_none(fake_eplus_install: FakeEplusInstall) -> None:
    eplus = fake_eplus_install([("24-1-0", "24-2-0")])
    with TemporaryDirectory() as tmp:
        idf = Path(tmp) / "test.idf"
        idf.write_text("no version here")
        msgs: list[str] = []
        r = Runner(verbose=True)
        r.on_msg = lambda m: msgs.append(m)  # type: ignore[assignment]
        r.collect_runs(eplus_install=eplus, input_paths=[idf], save_intermediate=False)
        assert len(r.runs) == 0
        assert any("Could not determine version" in m for m in msgs)


def test_runner_collect_runs_save_intermediate(fake_eplus_install: FakeEplusInstall) -> None:
    eplus = fake_eplus_install([("24-1-0", "24-2-0")])
    with TemporaryDirectory() as tmp:
        idf = Path(tmp) / "test.idf"
        idf.write_text("Version,24.1;")
        r = Runner()
        r.collect_runs(eplus_install=eplus, input_paths=[idf], save_intermediate=True)
        assert len(r.runs) == 1
        assert r.runs[0].keep_old is True


def test_main_no_eplus_dir_found(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr("energyplus_transition.cli.EnergyPlusPath.try_to_auto_find", lambda: None)
    with pytest.raises(RuntimeError, match="Could not find"):
        main(["some.idf"])


def test_main_invalid_eplus_dir() -> None:
    with pytest.raises(ValueError, match="Invalid EnergyPlus"):
        main(["some.idf", "--eplus-dir", "/nonexistent/path"])


def test_main_no_valid_files(capsys: CaptureFixture[str], fake_eplus_install: FakeEplusInstall) -> None:
    eplus = fake_eplus_install([("24-1-0", "24-2-0")])
    main(["nonexistent.idf", "--eplus-dir", str(eplus.install_root)])
    assert "No valid input files" in capsys.readouterr().out


def test_main_to_version_no_matching_transitions(
    capsys: CaptureFixture[str], fake_eplus_install: FakeEplusInstall
) -> None:
    eplus = fake_eplus_install([("24-1-0", "24-2-0")])
    main(["some.idf", "--eplus-dir", str(eplus.install_root), "--to-version", "23.1"])
    assert "No transitions available" in capsys.readouterr().out


def test_main_auto_detect(monkeypatch: MonkeyPatch, fake_eplus_install: FakeEplusInstall) -> None:
    eplus = fake_eplus_install([("24-1-0", "24-2-0")])
    monkeypatch.setattr("energyplus_transition.cli.EnergyPlusPath.try_to_auto_find", lambda: eplus.install_root)
    with TemporaryDirectory() as tmp:
        idf = Path(tmp) / "test.idf"
        idf.write_text("Version,24.1;")
        main([str(idf)])
        assert get_idf_version(idf) == 24.2


def test_main_full_run(fake_eplus_install: FakeEplusInstall) -> None:
    eplus = fake_eplus_install([("24-1-0", "24-2-0"), ("24-2-0", "25-1-0")])
    with TemporaryDirectory() as tmp:
        idf = Path(tmp) / "test.idf"
        idf.write_text("Version,24.1;")
        main([str(idf), "--eplus-dir", str(eplus.install_root)])
        assert get_idf_version(idf) == 25.1


def test_main_to_version_limits_transitions(fake_eplus_install: FakeEplusInstall) -> None:
    eplus = fake_eplus_install([("24-1-0", "24-2-0"), ("24-2-0", "25-1-0")])
    with TemporaryDirectory() as tmp:
        idf = Path(tmp) / "test.idf"
        idf.write_text("Version,24.1;")
        main([str(idf), "--eplus-dir", str(eplus.install_root), "--to-version", "24.2"])
        assert get_idf_version(idf) == 24.2


def test_main_with_progress(fake_eplus_install: FakeEplusInstall) -> None:
    eplus = fake_eplus_install([("24-1-0", "24-2-0"), ("24-2-0", "25-1-0")])
    with TemporaryDirectory() as tmp:
        idf = Path(tmp) / "test.idf"
        idf.write_text("Version,24.1;")
        main([str(idf), "--eplus-dir", str(eplus.install_root), "--progress"])
        assert get_idf_version(idf) == 25.1


def test_main_with_progress_and_verbose(fake_eplus_install: FakeEplusInstall) -> None:
    eplus = fake_eplus_install([("24-1-0", "24-2-0"), ("24-2-0", "25-1-0")])
    with TemporaryDirectory() as tmp:
        idf = Path(tmp) / "test.idf"
        idf.write_text("Version,24.1;")
        main([str(idf), "--eplus-dir", str(eplus.install_root), "--progress", "--verbose"])
        assert get_idf_version(idf) == 25.1
