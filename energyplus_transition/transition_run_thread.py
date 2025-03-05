from pathlib import Path
import shutil
import subprocess
import threading
from typing import Callable

from energyplus_transition.international import translate as _
from energyplus_transition.transition_binary import TransitionBinary


class TransitionRunThread(threading.Thread):
    """
    This class allows easily running a series of EnergyPlus Transition program versions in a separate thread

    :param transitions_to_run: A dict of Path to list of matching
                               :py:class:`TransitionBinary <TransitionBinary.TransitionBinary>` instances
    :param working_directory: The transition working directory to run transitions in
    :param keep_old: A flag for whether to keep an extra backup of the original file to be transitioned in the run dir
    :param msg_callback: A Python function to be called back by this thread when a message can be displayed
    :param done_callback: A Python function to be called back by this thread when the transition process is complete

    :ivar std_out: The standard output from the transition process
    :ivar std_err: The standard error output from the transition process
    """

    def __init__(self, transitions_to_run: dict[Path, list[TransitionBinary]],
                 copy_to_idf_dir: bool, working_directory: Path,
                 keep_old: bool, increment_callback: Callable,
                 msg_callback: Callable, done_callback: Callable):
        self.p = None
        self.std_out = None
        self.std_err = None
        self.transitions = transitions_to_run
        self.run_dir = working_directory
        self.keep_old = keep_old
        self.copy_to_idf_dir = copy_to_idf_dir
        self.increment_callback = increment_callback
        self.msg_callback = msg_callback
        self.done_callback = done_callback
        self.cancelled = False
        threading.Thread.__init__(self)

    def backup_file_before_transition(self, transition_instance: TransitionBinary, input_file: Path) -> bool:
        input_file_name = input_file.name
        source_file_path = self.run_dir / input_file_name
        input_name_base = input_file.with_suffix('').name
        input_name_suffix = input_file.suffix
        target_backup_file_name = input_name_base + "_" + str(transition_instance.source_version) + input_name_suffix
        target_backup_file_path = self.run_dir / target_backup_file_name
        target_backup_file_path.unlink(missing_ok=True)
        try:
            shutil.copyfile(source_file_path, target_backup_file_path)
        except Exception as e:  # pragma: no cover
            print("Cannot copy file, permission problem? " + str(e))
            return False
        return True

    def run(self):
        """
        This function runs the instantiated thread based on the parameters passed into the constructor.
        The function intermittently calls the msg_callback class instance function variable to alert the calling thread
        of status updates.  When the function is complete it calls the done_callback class instance function variable to
        alert the calling thread.
        """
        self.cancelled = False
        failed = False
        # this whole loop is going to require actually running subprocesses and such, I'm not covering it for now
        for file, transition_list in self.transitions.items():  # pragma: no cover
            original_idf_dir = file.parent
            shutil.copy(file, self.run_dir)
            ext_fixed = file.name.replace(".idf", ".idfnew").replace(".imf", ".imfnew")
            expected_output_file = self.run_dir / ext_fixed
            base_file_name = file.name
            for tr in transition_list:
                if self.keep_old:
                    backup_success = self.backup_file_before_transition(tr, file)
                    if not backup_success:
                        failed = True
                        break
                command_line_tokens = [
                    tr.full_path_to_binary,
                    base_file_name,
                ]
                self.p = subprocess.Popen(
                    command_line_tokens,
                    shell=False,
                    cwd=self.run_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE)
                self.msg_callback(
                    _("Running Transition") + " " + file.name + " " + str(tr.source_version) + " -> " + str(
                        tr.target_version)
                )
                self.std_out, self.std_err = self.p.communicate()
                if self.cancelled:
                    self.msg_callback(_("Transition Cancelled"))
                    break
                else:
                    if self.p.returncode == 0:
                        self.msg_callback(
                            _("Completed Transition") + " " + file.name + " " + str(tr.source_version) + " -> " + str(
                                tr.target_version))
                    else:
                        self.msg_callback(
                            _("Failed Transition") + " " + file.name + " " + str(tr.source_version) + " -> " + str(
                                tr.target_version))
                        failed = True
                        break
                self.increment_callback()
            if not self.cancelled and not failed:
                if self.copy_to_idf_dir:
                    shutil.copy(expected_output_file, original_idf_dir / ext_fixed)
        # I cannot imagine how to wedge in a cancel or failure here during a unit test, so not covering those
        if self.cancelled:  # pragma: no cover
            self.done_callback(_("Transition cancelled"))
        elif failed:  # pragma: no cover
            self.done_callback(_("Transition Failed! - Open run directory to read latest audit/error/etc"))
        else:
            self.done_callback(_("All transitions completed successfully - Open run directory for transitioned file"))

    def stop(self):
        """Sets the cancelled flag to attempt to kill the transition at the next step"""
        self.msg_callback(_("Attempting to cancel simulation ..."))
        self.cancelled = True
