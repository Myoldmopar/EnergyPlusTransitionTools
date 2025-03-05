from pathlib import Path
from shutil import copy
from tempfile import mkdtemp, mktemp
from unittest import TestCase

from energyplus_transition.transition_binary import TransitionBinary
from energyplus_transition.transition_run_thread import TransitionRunThread


class Test(TestCase):
    def test_thread(self):
        temp_file = Path(mktemp())
        temp_file.write_text("Hello")
        temp_run_dir = Path(mkdtemp())
        copy(temp_file, temp_run_dir)
        t = TransitionRunThread(
            transitions_to_run={},
            working_directory=temp_run_dir,
            keep_old=False,
            increment_callback=lambda x: x,
            msg_callback=lambda x: x,
            done_callback=lambda x: x,
        )

        p = "/Applications/EnergyPlus-25-1-0/PreProcess/IDFVersionUpdater/Transition-V24-2-0-to-V25-1-0"
        tb = TransitionBinary(Path(p))
        t.backup_file_before_transition(tb, temp_file)
        t.run()
        self.assertFalse(t.cancelled)
        t.stop()
        self.assertTrue(t.cancelled)
