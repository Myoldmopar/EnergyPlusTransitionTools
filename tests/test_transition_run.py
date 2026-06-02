from pathlib import Path
from tempfile import TemporaryDirectory, mktemp
from unittest.mock import MagicMock, patch

from energyplus_transition.input_files import get_idf_version
from energyplus_transition.transition_binary import TransitionBinary
from energyplus_transition.transition_run import TransitionRun
from tests.types import FakeEplusInstall


def test_backup_file_before_transition() -> None:
    temp_file = Path(mktemp())
    temp_file.write_text("Hello")
    tb = TransitionBinary(
        Path("/Applications/EnergyPlus-25-1-0/PreProcess/IDFVersionUpdater/Transition-V24-2-0-to-V25-1-0")
    )
    TransitionRun.backup_file_before_transition(transition_instance=tb, input_file=temp_file)
    backup = temp_file.parent / f"{temp_file.stem}_24.2{temp_file.suffix}"
    assert backup.exists()
    assert backup.read_text() == "Hello"


def test_cancelled_flag() -> None:
    t = TransitionRun(
        input_file=Path(mktemp()),
        transition_list=[],
        keep_old=False,
        increment_callback=lambda: None,
        msg_callback=lambda x: None,
        done_callback=lambda x: None,
    )
    t.run()
    assert not t.cancelled
    t.stop()
    assert t.cancelled


def test_callbacks(fake_eplus_install: FakeEplusInstall) -> None:
    eplus = fake_eplus_install([("24-1-0", "24-2-0"), ("24-2-0", "25-1-0")])

    started_calls = []
    increment_calls = []
    messages = []
    done_calls = []

    with TemporaryDirectory() as tmp:
        idf = Path(tmp) / "test.idf"
        idf.write_text("Version,24.1;")

        t = TransitionRun(
            input_file=idf,
            transition_list=eplus.transitions_available,
            keep_old=False,
            started_callback=lambda: started_calls.append(True),
            increment_callback=lambda: increment_calls.append(True),
            msg_callback=lambda m: messages.append(m),
            done_callback=lambda m: done_calls.append(m),
        )
        t.run()

    assert len(started_calls) == 1
    assert len(increment_calls) == 2  # one per transition step
    assert len(done_calls) == 1
    assert "successfully" in done_calls[0]
    assert any("24.1" in m and "24.2" in m for m in messages)
    assert any("24.2" in m and "25.1" in m for m in messages)


def test_run_transitions(fake_eplus_install: FakeEplusInstall) -> None:
    eplus = fake_eplus_install([("24-1-0", "24-2-0"), ("24-2-0", "25-1-0")])
    assert eplus.valid_install
    assert len(eplus.transitions_available) == 2

    with TemporaryDirectory() as tmp:
        idf = Path(tmp) / "test.idf"
        idf.write_text("Version,24.1;")

        t = TransitionRun(
            input_file=idf,
            transition_list=eplus.transitions_available,
            keep_old=False,
            increment_callback=lambda: None,
            msg_callback=lambda x: None,
            done_callback=lambda x: None,
        )
        t.run()

        assert get_idf_version(idf) == 25.1
        assert idf.with_suffix(".idfold").exists()


def test_keep_old(fake_eplus_install: FakeEplusInstall) -> None:
    eplus = fake_eplus_install([("24-1-0", "24-2-0"), ("24-2-0", "25-1-0")])
    with TemporaryDirectory() as tmp:
        idf = Path(tmp) / "test.idf"
        idf.write_text("Version,24.1;")
        t = TransitionRun(
            input_file=idf,
            transition_list=eplus.transitions_available,
            keep_old=True,
            increment_callback=lambda: None,
            msg_callback=lambda x: None,
            done_callback=lambda x: None,
        )
        t.run()
        assert (idf.parent / "test_24.1.idf").exists()
        assert (idf.parent / "test_24.2.idf").exists()


def _make_mock_run(t: TransitionRun, returncode: int = 0, cancel: bool = False) -> MagicMock:
    mock_proc = MagicMock()
    mock_proc.returncode = returncode
    if cancel:

        def communicate_and_cancel() -> tuple[bytes, bytes]:
            t.stop()
            return b"", b""

        mock_proc.communicate.side_effect = communicate_and_cancel
    else:
        mock_proc.communicate.return_value = (b"", b"")
    return mock_proc


def test_cancelled_mid_transition(fake_eplus_install: FakeEplusInstall) -> None:
    eplus = fake_eplus_install([("24-1-0", "24-2-0"), ("24-2-0", "25-1-0")])
    with TemporaryDirectory() as tmp:
        idf = Path(tmp) / "test.idf"
        idf.write_text("Version,24.1;")
        done_calls = []
        t = TransitionRun(
            input_file=idf,
            transition_list=eplus.transitions_available,
            keep_old=False,
            increment_callback=lambda: None,
            msg_callback=lambda x: None,
            done_callback=lambda m: done_calls.append(m),
        )
        with patch(
            "energyplus_transition.transition_run.subprocess.Popen", return_value=_make_mock_run(t, cancel=True)
        ):
            t.run()
        assert t.cancelled
        assert "cancelled" in done_calls[0].lower()


def test_failed_transition(fake_eplus_install: FakeEplusInstall) -> None:
    eplus = fake_eplus_install([("24-1-0", "24-2-0"), ("24-2-0", "25-1-0")])
    with TemporaryDirectory() as tmp:
        idf = Path(tmp) / "test.idf"
        idf.write_text("Version,24.1;")
        done_calls = []
        t = TransitionRun(
            input_file=idf,
            transition_list=eplus.transitions_available,
            keep_old=False,
            increment_callback=lambda: None,
            msg_callback=lambda x: None,
            done_callback=lambda m: done_calls.append(m),
        )
        with patch(
            "energyplus_transition.transition_run.subprocess.Popen", return_value=_make_mock_run(t, returncode=1)
        ):
            t.run()
        assert "Failed" in done_calls[0]
