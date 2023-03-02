from json import loads, dumps
from queue import Queue
from pathlib import Path
import subprocess
from sys import platform
from typing import Optional

from tkinter import (
    Tk, StringVar, messagebox, Menu, Button, Frame, LabelFrame, SUNKEN, S, EW, Label, BooleanVar,
    ACTIVE, DISABLED, filedialog, NSEW, ALL, W, E, IntVar
)
from tkinter.ttk import Progressbar
from energyplus_transition import NAME, VERSION
from energyplus_transition.energyplus_path import EnergyPlusPath
from energyplus_transition.transition_run_thread import TransitionRunThread
from energyplus_transition.international import translate as _, Language, set_language


class Configuration:
    class Keys:
        last_idf_folder = 'last_idf_folder'
        last_idf = 'last_idf'
        language = 'language'
        eplus_dir = 'eplus_dir'
        keep_intermediate = 'keep_intermediate'

    def __init__(self):
        self.settings_file = Path.home() / ".idfversionupdater.json"
        self.settings = {}
        if self.settings_file.exists():
            try:
                file_contents = self.settings_file.read_text()
                self.settings = loads(file_contents)
            except Exception as e:
                print(
                    f"Could not load settings file at {str(self.settings_file)}, using blank settings, err = {str(e)}"
                )
        # initialize the last selected idf folder
        if Configuration.Keys.last_idf_folder not in self.settings:
            self.settings[Configuration.Keys.last_idf_folder] = str(Path.home())
        # initialize the last selected idf
        if Configuration.Keys.last_idf not in self.settings:
            if platform.startswith("win"):
                self.settings[Configuration.Keys.last_idf] = 'C:\\Path\\to.idf'
            else:
                self.settings[Configuration.Keys.last_idf] = '/path/to.idf'
        # initialize the last language
        if Configuration.Keys.language not in self.settings:
            self.settings[Configuration.Keys.language] = Language.English
        # initialize the last eplus install dir
        if Configuration.Keys.eplus_dir not in self.settings:
            potential_install_dir = EnergyPlusPath.try_to_auto_find()
            if potential_install_dir:  # use the auto-found version if it's not None
                self.settings[Configuration.Keys.eplus_dir] = str(potential_install_dir)
            elif platform.startswith("linux"):  # otherwise initialize to a nonexistent value
                self.settings[Configuration.Keys.eplus_dir] = '/usr/local/EnergyPlus-X-Y-Z'
            elif platform == "darwin":
                self.settings[Configuration.Keys.eplus_dir] = '/Applications/EnergyPlus-X-Y-Z'
            elif platform.startswith("win32"):
                self.settings[Configuration.Keys.eplus_dir] = 'C:/EnergyPlusVX-Y-Z'
        # initialize the keep intermediate setting
        if Configuration.Keys.keep_intermediate not in self.settings:
            self.settings[Configuration.Keys.keep_intermediate] = True

    def save_settings(self):
        try:
            self.settings_file.write_text(dumps(self.settings, indent=2))
        except Exception as e:
            print(f"Could not save settings file at {str(self.settings_file)}, config not saved, err = {str(e)}")


class VersionUpdaterWindow(Tk):
    """ The main window, or Tk(), for the IDFVersionUpdater program.
    This initializer function creates instance variables, sets up threading, and builds the GUI"""

    # region class construction and basic event/closing functions

    def __init__(self):
        super().__init__()

        self._gui_queue = Queue()
        self._check_queue()

        # load the settings here very early
        self.conf = Configuration()

        # initialize some class-level "constants"
        self.pad = {'padx': 3, 'pady': 3}

        # reset the restart flag
        self.doing_restart = False
        self.update_running = False
        self.running_transition_thread: Optional[TransitionRunThread] = None

        # try to load the settings very early since it includes initialization
        set_language(self.conf.settings[Configuration.Keys.language])

        # connect signals for the GUI
        self.protocol('WM_DELETE_WINDOW', self._close_form)

        # build up the GUI itself
        self._define_tk_variables()
        self._build_gui()
        self.title(f"{NAME} ({VERSION})")

        # update the list of E+ versions
        self._refresh_for_new_eplus_install()

        self._tk_var_status.set(_("Program Initialized"))

        # check the validity of the idf versions once at load time to initialize the action availability
        self._refresh_gui_state()

    def _close_form(self):
        # noinspection PyBroadException
        try:
            self.conf.save_settings()
        except Exception:
            pass
        finally:
            self.destroy()

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

    # endregion

    # region GUI building variable/tracing

    def _define_tk_variables(self):
        self._tk_var_status = StringVar(value="<status>")
        self._tk_var_selected_idf_version = StringVar(value=_('Old Version'))
        self._tk_var_eplus_version = StringVar(value="<eplus_version>")
        self._tk_var_progress = IntVar(value=0)

        def trace_last_idf(*_):
            self.conf.settings[Configuration.Keys.last_idf] = self._tk_var_idf_path.get()
        self._tk_var_idf_path = StringVar(value=self.conf.settings[Configuration.Keys.last_idf])
        self._tk_var_idf_path.trace('w', trace_last_idf)

        def trace_intermediate(*_):
            self.conf.settings[Configuration.Keys.keep_intermediate] = self._tk_var_keep_intermediate.get()
        self._tk_var_keep_intermediate = BooleanVar(value=self.conf.settings[Configuration.Keys.keep_intermediate])
        self._tk_var_keep_intermediate.trace('w', trace_intermediate)

        def trace_eplus_dir(*_):
            self.conf.settings[Configuration.Keys.eplus_dir] = self._tk_var_eplus_dir.get()
        self._tk_var_eplus_dir = StringVar(value=self.conf.settings[Configuration.Keys.eplus_dir])
        self._tk_var_eplus_dir.trace('w', trace_eplus_dir)

    def _build_gui(self):
        """
        This function manages the window construction, including position, title, and presentation
        """
        menu_bar = Menu(self)
        menu_file = Menu(menu_bar, tearoff=False)
        menu_file.add_command(
            label="Change language to English", command=lambda: self._on_press_change_language(Language.English)
        )
        # noinspection SpellCheckingInspection
        menu_file.add_command(
            label="Cambiar idioma a español", command=lambda: self._on_press_change_language(Language.Spanish)
        )
        # noinspection SpellCheckingInspection
        menu_file.add_command(
            label="Changer la langue en français", command=lambda: self._on_press_change_language(Language.French)
        )
        menu_file.add_separator()
        menu_file.add_checkbutton(
            label=_('Keep Intermediate Versions of Files?'), onvalue=True,
            offvalue=False, variable=self._tk_var_keep_intermediate
        )
        menu_file.add_command(
            label=_('About...'),
            command=lambda: messagebox.showinfo(title=_('About...'), message=_("ABOUT_DIALOG"))
        )
        menu_file.add_command(label=_("Exit"), command=self._close_form)
        menu_bar.add_cascade(label=_("Menu"), menu=menu_file)
        self.config(menu=menu_bar)

        # top row: E+ folder selection
        lf = LabelFrame(self, text=_("EnergyPlus Installation"))
        self.button_select_eplus_dir = Button(
            lf, text=_('Choose E+ Folder...'), command=self._on_press_choose_eplus_dir
        )
        self.button_select_eplus_dir.grid(row=0, rowspan=2, column=0, **self.pad)
        Label(lf, text=_("Selected Directory: ")).grid(row=0, column=1, sticky=E, **self.pad)
        self.label_eplus_dir = Label(lf, textvariable=self._tk_var_eplus_dir)
        self.label_eplus_dir.grid(row=0, column=2, sticky=W, **self.pad)
        Label(lf, text=_("Install Details: ")).grid(row=1, column=1, sticky=E, **self.pad)
        self.lbl_eplus_version = Label(lf, textvariable=self._tk_var_eplus_version)
        self.lbl_eplus_version.grid(row=1, column=2, sticky=W, **self.pad)
        lf.grid_rowconfigure(ALL, weight=1)
        lf.grid(row=0, column=0, sticky=NSEW, **self.pad)

        # next row: IDF selection
        lf = LabelFrame(self, text=_("IDF Selection"))
        self.button_select_idf = Button(lf, text=_('Choose File to Update...'), command=self._on_press_choose_idf)
        self.button_select_idf.grid(row=0, rowspan=2, column=0, **self.pad)
        Label(lf, text=_("Selected IDF: ")).grid(row=0, column=1, sticky=E, **self.pad)
        self.label_path = Label(lf, textvariable=self._tk_var_idf_path)
        self.label_path.grid(row=0, column=2, sticky=W, **self.pad)
        Label(lf, text=_("File Details: ")).grid(row=1, column=1, sticky=E, **self.pad)
        self.lbl_old_version = Label(lf, textvariable=self._tk_var_selected_idf_version)
        self.lbl_old_version.grid(row=1, column=2, sticky=W, **self.pad)
        lf.grid_rowconfigure(ALL, weight=1)
        lf.grid(row=1, column=0, sticky=NSEW, **self.pad)

        # next row: the button row
        lf = Frame(self)
        self.button_open_run_dir = Button(lf, text=_('Open Run Directory'), command=self._on_press_open_run_dir)
        self.button_open_run_dir.grid(row=0, column=0, **self.pad)
        self.button_update_file = Button(lf, text=_('Update File'), command=self._on_press_update_idf)
        self.button_update_file.grid(row=0, column=2, **self.pad)
        self.button_cancel = Button(lf, text=_('Cancel Run'), command=self._on_press_cancel)
        self.button_cancel.grid(row=0, column=3, **self.pad)
        lf.grid_columnconfigure(ALL, weight=1)
        lf.grid(row=2, column=0, sticky=EW, **self.pad)

        status_frame = Frame(self)
        self._progress = Progressbar(status_frame, variable=self._tk_var_progress)
        self._progress.grid(row=0, column=0, sticky=EW)
        Label(status_frame, relief=SUNKEN, anchor=S, textvariable=self._tk_var_status).grid(row=0, column=1, sticky=EW)
        status_frame.grid_columnconfigure(0, weight=1)
        status_frame.grid_columnconfigure(1, weight=3)
        status_frame.grid(row=3, column=0, sticky=EW)

        self.grid_rowconfigure(0, weight=5)
        self.grid_rowconfigure(1, weight=5)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=0)
        self.grid_columnconfigure(ALL, weight=1)

    def _refresh_gui_state(self):
        """This function sets the state of the GUI based on IDF selection and background thread running"""
        # TODO: Check self.eplus_install.valid_install to disable things
        # Update buttons based on the thread run state
        if self.update_running:
            self.button_select_eplus_dir['state'] = DISABLED
            self.button_select_idf['state'] = DISABLED
            self.button_update_file['state'] = DISABLED
            self.button_cancel['state'] = ACTIVE
        else:
            self.button_cancel['state'] = DISABLED
            self.button_select_eplus_dir['state'] = ACTIVE
            self.button_select_idf['state'] = ACTIVE
            idf = self._tk_var_idf_path.get()
            idf_path = Path(idf)
            if self.eplus_install.valid_install and idf_path.exists():
                self.on_msg(_("IDF File exists, ready to go"))
                self.idf_version = self.get_idf_version(idf_path)
                self._tk_var_selected_idf_version.set(f"{_('Old Version')}: {self.idf_version}")
                self.button_update_file['state'] = ACTIVE
            else:
                self.on_msg(_("IDF File doesn't exist at path given; cannot transition"))
                self.button_update_file['state'] = DISABLED

    def _refresh_for_new_eplus_install(self):
        self.eplus_install = EnergyPlusPath(self._tk_var_eplus_dir.get())
        if self.eplus_install.valid_install:
            self._tk_var_eplus_version.set(f"{_('EnergyPlus Version')}: {self.eplus_install.version}")
        else:
            self._tk_var_eplus_version.set(_("Invalid Version"))
        self._refresh_gui_state()

    # endregion

    # region button press handlers

    def _on_press_choose_eplus_dir(self):
        new_eplus_dir = filedialog.askdirectory(title=_("Choose EnergyPlus Install Root"), mustexist=True)
        if not new_eplus_dir:
            return
        self._tk_var_eplus_dir.set(new_eplus_dir)
        self._refresh_for_new_eplus_install()

    def _on_press_change_language(self, new_language: str):
        """
        This function handles the request to change languages, where the language identifier is passed in with the event
        an item in the :py:class:`Languages <International.Languages>` enumeration class
        """
        self.conf.settings[Configuration.Keys.language] = new_language
        response = messagebox.askyesnocancel(
            _("Language Confirmation"),
            _('You must restart the app to make the language change take effect.  Would you like to restart now?')
        )
        if response is None or not response:
            return
        else:  # YES
            self.doing_restart = True
            self.conf.save_settings()
            self.destroy()

    def _on_press_open_run_dir(self):
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
            subprocess.Popen([open_cmd, self.eplus_install.transition_directory], shell=False)
        except Exception as e:
            messagebox.showerror(_("Could not open run directory") + str(e))

    def _on_press_choose_idf(self):
        """
        This function handles the request to choose a new idf, opening a dialog, and updating settings if applicable
        """
        cur_folder = self.conf.settings[Configuration.Keys.last_idf_folder]
        cur_idf = filedialog.askopenfilename(
            title=_("Open File for Transition"),
            initialdir=cur_folder,
            filetypes=(
                ("EnergyPlus Input Files", "*.idf"),
                ("EnergyPlus Macro Files", ";*.imf")
            )
        )
        if not cur_idf:
            return
        cur_idf_path = Path(cur_idf)
        self.conf.settings[Configuration.Keys.last_idf_folder] = str(cur_idf_path.parent)
        self._tk_var_idf_path.set(value=cur_idf)
        self.conf.settings[Configuration.Keys.last_idf] = cur_idf
        self._refresh_gui_state()

    def _on_press_update_idf(self):
        """
        This function handles the request to run Transition itself, building up the list of transitions,
        creating a new thread instance, prepping the gui, and running it
        """
        if self.idf_version not in [tr.source_version for tr in self.eplus_install.transitions_available]:
            self.on_msg(_("Cannot find a matching transition tool for this idf version"))
        # we need to build up the list of transition steps to perform
        self._tk_var_progress.set(0)
        transitions_to_run = []
        for tr in self.eplus_install.transitions_available:
            if tr.source_version < self.idf_version:
                continue  # skip this older version
            transitions_to_run.append(tr)
        self.running_transition_thread = TransitionRunThread(
            transitions_to_run,
            self.eplus_install.transition_directory,
            Path(self.conf.settings[Configuration.Keys.last_idf]),
            self._tk_var_keep_intermediate.get(),
            self._callback_on_ready,
            self._callback_on_increment,
            self.callback_on_msg,
            self.callback_on_done
        )
        self.update_running = True
        self.running_transition_thread.start()
        self._refresh_gui_state()

    def _on_press_cancel(self):
        self.button_cancel['state'] = DISABLED
        self.running_transition_thread.stop()

    # endregion

    # region background thread callbacks and handlers

    def _callback_on_ready(self, num_steps: int):
        self._gui_queue.put(lambda: self._on_ready(num_steps))

    def _on_ready(self, num_steps: int):
        self._progress['maximum'] = num_steps

    def _callback_on_increment(self):
        self._gui_queue.put(self._on_increment)

    def _on_increment(self):
        self._tk_var_progress.set(self._tk_var_progress.get() + 1)

    def callback_on_msg(self, message: str):
        self._gui_queue.put(lambda: self.on_msg(message))

    def on_msg(self, message: str):
        self._tk_var_status.set(message)

    def callback_on_done(self, message: str):
        self._gui_queue.put(lambda: self.on_done(message))

    def on_done(self, message: str):
        self._tk_var_status.set(message)
        self._tk_var_progress.set(self._progress['maximum'])
        self.update_running = False
        self._refresh_gui_state()

    # endregion

    # region utility functions

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
        lines = path_to_idf.read_text(errors='ignore').split('\n')
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

    # endregion
