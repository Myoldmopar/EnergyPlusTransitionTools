from queue import Queue
from pathlib import Path
import subprocess
from sys import platform
from typing import Optional

from tkinter import (
    Tk, StringVar, messagebox, Menu, Button, Frame, Entry, SUNKEN, S, LEFT, BOTH, Label, BooleanVar, Checkbutton,
    ACTIVE, DISABLED, filedialog, NSEW, EW
)

from ep_transition import NAME, VERSION
from ep_transition.energyPlus_path import EnergyPlusPath
from ep_transition.transition_run_thread import TransitionRunThread
from ep_transition.international import translate as _, Language, set_language
from ep_transition.settings import Keys, load_settings, save_settings


# TODO: Add progress bar to status bar
# TODO: Get UI looking right
# TODO: Allow selecting E+ install version
# TODO: Work on CLI
# TODO: Unit test
# TODO: Package

class VersionUpdaterWindow(Tk):
    """ The main window, or wx.Frame, for the IDFVersionUpdater program.
    This initializer function creates instance variables, sets up threading, and builds the GUI"""

    def __init__(self):
        super().__init__()
        self.minsize(600, 183)

        self._gui_queue = Queue()
        self._check_queue()

        # load the settings here very early; the tilde is cross-platform thanks to Python
        self.settings_file_name = Path.home() / ".idfversionupdater.json"
        self.settings = load_settings(self.settings_file_name)

        # initialize some class-level "constants"
        self.pad = {'padx': 3, 'pady': 3}

        # reset the restart flag
        self.doing_restart = False
        self.running_transition_thread: Optional[TransitionRunThread] = None

        # try to load the settings very early since it includes initialization
        set_language(self.settings[Keys.language])

        # connect signals for the GUI
        self.protocol('WM_DELETE_WINDOW', self.on_closing_form)

        # build up the GUI itself
        self._define_tk_variables()
        self._build_gui()

        # update the list of E+ versions
        self.ep_run_folder = EnergyPlusPath()
        ep_version = TransitionRunThread.get_ep_version(self.ep_run_folder.installation_path / 'energyplus')
        self.title(f"{NAME} ({VERSION}) - {ep_version}")

        self._tk_var_status.set(_("Program Initialized"))

        # check the validity of the idf versions once at load time to initialize the action availability
        self._on_update_for_new_file()

    def _check_queue(self):
        """Checks the GUI queue for actions and sets a timer to check again each time"""
        while True:
            # noinspection PyBroadException
            try:
                task = self._gui_queue.get(block=False)
                self.after_idle(task)
            except Exception:
                break
        self.after(100, self._check_queue)

    def _define_tk_variables(self):
        self._tk_var_status = StringVar(value="<status>")
        self._tk_var_idf_path = StringVar(value="<idf_path>")
        self._tk_var_keep_intermediate = BooleanVar(value=True)
        self._tk_var_old_version = StringVar(value=_('Old Version'))

    def _build_gui(self):
        """
        This function manages the window construction, including position, title, and presentation
        """
        menu_bar = Menu(self)
        menu_file = Menu(menu_bar, tearoff=False)
        menu_file.add_command(label="Change language to English", command=lambda: self._language(Language.English))
        menu_file.add_command(label="Change language to Spanish", command=lambda: self._language(Language.Spanish))
        menu_file.add_command(label="Change language to French", command=lambda: self._language(Language.French))
        menu_file.add_separator()
        menu_file.add_command(
            label="About...",
            command=lambda: messagebox.showinfo(title="About", message=_("ABOUT_DIALOG"))
        )
        menu_file.add_command(label="Exit", command=self.on_close)
        menu_bar.add_cascade(label="File", menu=menu_file)
        self.config(menu=menu_bar)

        main_frame_area = Frame(self)
        self.button_select_idf = Button(main_frame_area, text=_('Choose File to Update...'), command=self.on_choose_idf)
        self.button_select_idf.grid(row=0, column=0, **self.pad)
        self.label_path = Entry(main_frame_area, textvariable=self._tk_var_idf_path)
        self.label_path.grid(row=0, column=1, sticky=EW, **self.pad)
        if self.settings[Keys.last_idf] is not None:
            self._tk_var_idf_path.set(self.settings[Keys.last_idf])
        self.lbl_old_version = Label(main_frame_area, textvariable=self._tk_var_old_version)
        self.lbl_old_version.grid(row=0, column=2, sticky=EW, **self.pad)
        self.chk_create_inter_versions = Checkbutton(
            main_frame_area, variable=self._tk_var_keep_intermediate, text=_('Keep Intermediate Versions of Files?')
        )
        self.chk_create_inter_versions.grid(row=1, column=0, **self.pad)
        self.button_update_file = Button(main_frame_area, text=_('Update File'), command=self.on_update_idf)
        self.button_update_file.grid(row=2, column=0, **self.pad)
        self.button_cancel = Button(main_frame_area, text=_('Cancel Run'), command=self.on_cancel)
        self.button_cancel.grid(row=2, column=1, **self.pad)
        self.button_open_run_dir = Button(main_frame_area, text=_('Open Run Directory'), command=self.on_open_run_dir)
        self.button_open_run_dir.grid(row=2, column=2, **self.pad)
        self.button_exit = Button(main_frame_area, text=_('Close'), command=self.on_close)
        self.button_exit.grid(row=2, column=3, **self.pad)
        main_frame_area.grid(row=0, column=0, sticky=NSEW)

        status_frame = Frame(self)
        Label(status_frame, relief=SUNKEN, anchor=S, textvariable=self._tk_var_status).pack(
            side=LEFT, fill=BOTH, expand=True
        )
        status_frame.grid(row=1, column=0, sticky=NSEW, **self.pad)

    def set_buttons_for_running(self, enabled):
        """
        This function sets the state of different buttons on the main window while a background task is running
        The list of controls to be enabled/disabled is hardcoded in an array in this function
        :param enabled: True if the main controls are to be enabled, false otherwise
        :return:
        """
        to_enable = ACTIVE if enabled else DISABLED
        to_disable = DISABLED if enabled else ACTIVE
        self.button_update_file['state'] = to_enable
        self.button_select_idf['state'] = to_enable
        self.button_exit['state'] = to_enable
        self.button_cancel['state'] = to_disable

    def _language(self, new_language: Language):
        """
        This function handles the request to change languages, where the language identifier is passed in with the event
        an item in the :py:class:`Languages <International.Languages>` enumeration class
        """
        self.settings[Keys.language] = new_language
        response = messagebox.askyesnocancel(
            "Language Confirmation",
            "You must restart the app to make the language change take effect.  Would you like to restart now?"
        )
        if response is None or not response:
            return
        else:  # YES
            self.doing_restart = True
            self.destroy()

    def _on_update_for_new_file(self):
        """
        This function handles the request to update for a new file, including updating program settings,
        gui button state, and updating the file version label if the file exists
        """
        idf = self._tk_var_idf_path.get()
        self.settings[Keys.last_idf] = idf
        idf_path = Path(idf)
        if idf_path.exists():
            self.on_msg(_("IDF File exists, ready to go"))
            self.idf_version = self.get_idf_version(idf_path)
            self._tk_var_old_version.set(f"{_('Old Version')}: {self.idf_version}")
            self.button_update_file['state'] = ACTIVE
        else:
            self.on_msg(_("IDF File doesn't exist at path given; cannot transition"))
            self.button_update_file['state'] = DISABLED

    def on_open_run_dir(self):
        """
        This function handles the request to open the current run directory in the default application (Finder...)
        """
        try:
            if platform.startswith("linux"):
                open_cmd = "xdg-open"
            elif platform == "darwin":
                open_cmd = "open"
            else:  # assuming windows  platform.startswith("win32"):
                open_cmd = "explorer"
            subprocess.Popen([open_cmd, self.ep_run_folder.transition_directory], shell=False)
        except Exception as e:
            messagebox.showerror("Error opening directory: " + str(e))

    def on_closing_form(self):
        """
        This function handles the request to close the form, first trying to save program settings
        """
        # noinspection PyBroadException
        try:
            save_settings(self.settings, self.settings_file_name)
        except Exception:
            pass
        self.destroy()

    def on_choose_idf(self):
        """
        This function handles the request to choose a new idf, opening a dialog, and updating settings if applicable
        """
        cur_folder = str(Path.home())
        if self.settings[Keys.last_idf_folder] is not None:
            cur_folder = self.settings[Keys.last_idf_folder]
        cur_idf = filedialog.askopenfilename(
            title=_("Open File for Transition"),
            initialdir=cur_folder,
            filetypes=(
                ("EnergyPlus Input Files", "*.idf"),
                ("EnergyPlus Macro Files", ";*.imf")
            )
        )
        if cur_idf is None:
            return
        self.settings[Keys.last_idf] = cur_idf
        cur_idf_path = Path(cur_idf)
        self.settings[Keys.last_idf_folder] = str(cur_idf_path.parent)
        self._tk_var_idf_path.set(value=cur_idf)
        self._on_update_for_new_file()

    def on_update_idf(self):
        """
        This function handles the request to run Transition itself, building up the list of transitions,
        creating a new thread instance, prepping the gui, and running it
        """
        if self.idf_version not in [tr.source_version for tr in self.ep_run_folder.transitions_available]:
            self.on_msg(_("Cannot find a matching transition tool for this idf version"))
        # we need to build up the list of transition steps to perform
        transitions_to_run = []
        for tr in self.ep_run_folder.transitions_available:
            if tr.source_version < self.idf_version:
                continue  # skip this older version
            transitions_to_run.append(tr)
        self.running_transition_thread = TransitionRunThread(
            transitions_to_run,
            self.ep_run_folder.transition_directory,
            Path(self.settings[Keys.last_idf]),
            self._tk_var_keep_intermediate.get(),
            self.callback_on_msg,
            self.callback_on_done
        )
        self.running_transition_thread.start()
        self.set_buttons_for_running(enabled=False)

    def on_cancel(self):
        self.button_cancel['state'] = DISABLED
        self.running_transition_thread.stop()

    def on_close(self):
        """
        This function handles the request to close the form, simply calling Close
        Note this does not destroy the form, allowing the owning code to still access the form settings
        """
        self.destroy()

    # Callback functions and delegates to be called on MainLoop thread

    def callback_on_msg(self, message):
        self._gui_queue.put(lambda: self.on_msg(message))

    def on_msg(self, message):
        self._tk_var_status.set(message)

    def callback_on_done(self, message):
        self._gui_queue.put(lambda: self.on_done(message))

    def on_done(self, message):
        self._tk_var_status.set(message)
        self.set_buttons_for_running(enabled=True)

    # Utilities

    @staticmethod
    def get_idf_version(path_to_idf: Path):
        """
        This function returns the current version of a given input file.
        The function uses a simplified parsing approach, so it only works for valid syntax files,
        and provides no specialized error handling

        :param path_to_idf: Absolute path to a EnergyPlus input file
        :rtype: A floating point version number for the input file, for example 8.5 for an 8.5.0 input file
        """
        # phase 1: read in lines of file
        lines = path_to_idf.read_text().split('\n')
        # phases 2: remove comments and blank lines
        lines_a = []
        for line in lines:
            line_text = line.strip()
            this_line = ""
            if len(line_text) > 0:
                exclamation = line_text.find("!")
                if exclamation == -1:
                    this_line = line_text
                elif exclamation == 0:
                    this_line = ""
                elif exclamation > 0:
                    this_line = line_text[:exclamation]
                if not this_line == "":
                    lines_a.append(this_line)
        # phase 3: join entire array and re-split by semicolon
        idf_data_joined = ''.join(lines_a)
        idf_object_strings = idf_data_joined.split(";")
        # phase 4: break each object into an array of object name and field values
        for this_object in idf_object_strings:
            tokens = this_object.split(',')
            if tokens[0].upper() == "VERSION":
                version_string = tokens[1]
                version_string_tokens = version_string.split('.')  # might be 2 or 3...
                version_number = float("%s.%s" % (version_string_tokens[0], version_string_tokens[1]))
                return version_number
