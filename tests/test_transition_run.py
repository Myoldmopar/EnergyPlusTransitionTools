from pathlib import Path
from tempfile import mktemp
from unittest import TestCase

from energyplus_transition.transition_binary import TransitionBinary
from energyplus_transition.transition_run_thread import TransitionRun


class Test(TestCase):
    def test_thread(self) -> None:
        temp_file = Path(mktemp())
        temp_file.write_text("Hello")
        t = TransitionRun(
            input_file=temp_file,
            transition_list=[],
            keep_old=False,
            increment_callback=lambda x: x,
            msg_callback=lambda x: x,
            done_callback=lambda x: x,
        )

        p = "/Applications/EnergyPlus-25-1-0/PreProcess/IDFVersionUpdater/Transition-V24-2-0-to-V25-1-0"
        tb = TransitionBinary(Path(p))
        t.backup_file_before_transition(transition_instance=tb, input_file=temp_file)
        t.run()
        self.assertFalse(t.cancelled)
        t.stop()
        self.assertTrue(t.cancelled)
