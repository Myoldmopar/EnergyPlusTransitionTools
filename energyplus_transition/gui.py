from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import cpu_count
from json import loads, dumps
from queue import Queue
from pathlib import Path
from platform import system
import subprocess
from sys import platform
from typing import Optional

from tkinter import (
    Tk, StringVar, messagebox, Menu, Button, Frame, LabelFrame, SUNKEN, S, EW, Label, BooleanVar,
    ACTIVE, DISABLED, filedialog, NSEW, ALL, W, E, IntVar, PhotoImage, Scrollbar
)
from tkinter.ttk import Progressbar, Treeview

from plan_tools.runtime import fixup_taskbar_icon_on_windows  # type: ignore

from energyplus_transition import NAME, VERSION
from energyplus_transition.energyplus_path import EnergyPlusPath
from energyplus_transition.transition_run_thread import TransitionRun
from energyplus_transition.international import translate as _, Language, set_language


class Configuration:
    class Keys:
        last_input_file_directory = 'last_idf_folder'
        last_input_file_name = 'last_idf'
        language = 'language'
        eplus_dir = 'eplus_dir'
        keep_intermediate = 'keep_intermediate'

    def __init__(self, called_from_ep_cli: bool):
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
        if Configuration.Keys.last_input_file_directory not in self.settings:
            self.settings[Configuration.Keys.last_input_file_directory] = str(Path.home())
        # initialize the last selected idf
        if Configuration.Keys.last_input_file_name not in self.settings:
            if platform.startswith("win"):
                self.settings[Configuration.Keys.last_input_file_name] = 'C:\\Path\\to.idf'
            else:
                self.settings[Configuration.Keys.last_input_file_name] = '/path/to.idf'
        # initialize the last language
        if Configuration.Keys.language not in self.settings:
            self.settings[Configuration.Keys.language] = Language.English
        # initialize the last eplus install dir
        potential_install_dir: Path | None
        if called_from_ep_cli:  # if we are called from E+ CLI, set the E+ dir directly from this file path
            this_file = Path(__file__).resolve()
            transition_package_dir = this_file.parent
            python_lib_dir = transition_package_dir.parent
            eplus_install_dir = python_lib_dir.parent
            potential_install_dir = eplus_install_dir
            self.settings[Configuration.Keys.eplus_dir] = str(potential_install_dir)
        elif Configuration.Keys.eplus_dir not in self.settings:
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

    def __init__(self, called_from_ep_cli: bool):
        fixup_taskbar_icon_on_windows(NAME)
        super().__init__(className=NAME)

        if system() == 'Darwin':
            self.icon_path = Path(__file__).resolve().parent / 'icons' / 'icon.icns'
            if self.icon_path.exists():
                self.iconbitmap(str(self.icon_path))
            else:
                print(f"Could not set icon for Mac, expecting to find it at {self.icon_path}")
        elif system() == 'Windows':
            self.icon_path = Path(__file__).resolve().parent / 'icons' / 'icon.png'
            img = PhotoImage(file=str(self.icon_path))
            if self.icon_path.exists():
                self.iconphoto(False, img)
            else:
                print(f"Could not set icon for Windows, expecting to find it at {self.icon_path}")
        else:  # Linux
            self.icon_path = Path(__file__).resolve().parent / 'icons' / 'icon.png'
            img = PhotoImage(file=str(self.icon_path))
            if self.icon_path.exists():
                self.iconphoto(False, img)
            else:
                print(f"Could not set icon for Windows, expecting to find it at {self.icon_path}")

        self._gui_queue: Queue = Queue()
        self._check_queue()

        # load the settings here very early
        self.conf = Configuration(called_from_ep_cli)

        # initialize some class-level "constants"
        self.pad = {'padx': 3, 'pady': 3}

        # reset the restart flag
        self.doing_restart = False
        self.update_running = False
        self.running_transition_threads: list[TransitionRun] = []
        self._threads_remaining = 0
        self.selected_input_files: list[tuple[Path, float | None]] = []

        # try to load the settings very early since it includes initialization
        set_language(self.conf.settings[Configuration.Keys.language])

        # connect signals for the GUI
        self.protocol('WM_DELETE_WINDOW', self._close_form)

        # build up the GUI itself
        self._define_tk_variables()
        self._build_gui()
        self.title(f"IDF Version Updater ({VERSION})")

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
                # noinspection PyTypeChecker
                self.after_idle(task)
            except Exception:
                break
        # noinspection PyTypeChecker
        self.after(100, self._check_queue)

    # endregion

    # region GUI building variable/tracing

    def _define_tk_variables(self):
        self._tk_var_status = StringVar(value="<status>")
        self._tk_var_eplus_version = StringVar(value="<eplus_version>")
        self._tk_var_progress = IntVar(value=0)

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
            label=_('Keep Intermediate Versions of Files?'),
            onvalue=True, offvalue=False, variable=self._tk_var_keep_intermediate
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
        self.button_select_idf = Button(
            lf, text=_('Choose File(s) to Update...'), command=self._on_press_choose_input_file
        )
        self.button_select_idf.grid(row=0, column=0, sticky=NSEW, **self.pad)
        self.tree_selected_files = Treeview(
            lf, columns=("path", "version"), show="headings", height=4, selectmode="none"
        )
        self.tree_selected_files.heading("path", text=_("IDF Path"))
        self.tree_selected_files.heading("version", text=_("Old Version"))
        self.tree_selected_files.column("path", width=500, stretch=True)
        self.tree_selected_files.column("version", width=160, stretch=False)
        scrollbar = Scrollbar(lf, orient="vertical", command=self.tree_selected_files.yview)
        self.tree_selected_files.configure(yscrollcommand=scrollbar.set)
        self.tree_selected_files.grid(row=0, column=1, sticky=NSEW, **self.pad)
        scrollbar.grid(row=0, column=2, sticky="ns")
        lf.grid_rowconfigure(0, weight=1)
        lf.grid_columnconfigure(1, weight=1)
        lf.grid(row=1, column=0, sticky=NSEW, **self.pad)

        # next row: the button row
        lf = Frame(self)
        self.button_open_run_dir = Button(lf, text=_('Open Directory'), command=self._on_press_open_input_dir)
        self.button_open_run_dir.grid(row=0, column=0, sticky=EW, **self.pad)
        self.button_update_file = Button(lf, text=_('Run Transition'), command=self._on_press_update_idf)
        self.button_update_file.grid(row=0, column=1, sticky=EW, **self.pad)
        self.button_cancel = Button(lf, text=_('Cancel Run'), command=self._on_press_cancel)
        self.button_cancel.grid(row=0, column=2, sticky=EW, **self.pad)
        lf.grid_columnconfigure(ALL, weight=1)
        lf.grid(row=2, column=0, sticky=EW, **self.pad)

        # then the status bar
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

    def _populate_files_table(self):
        for row in self.tree_selected_files.get_children():
            self.tree_selected_files.delete(row)
        for path, version in self.selected_input_files:
            version_str = str(version) if version is not None else _("Unknown")
            self.tree_selected_files.insert("", "end", values=(str(path), version_str))

    def _refresh_gui_state(self):
        """This function sets the state of the GUI based on IDF selection and background thread running"""
        if self.update_running:
            self.button_select_eplus_dir['state'] = DISABLED
            self.button_select_idf['state'] = DISABLED
            self.button_update_file['state'] = DISABLED
            self.button_cancel['state'] = ACTIVE
        else:
            self.button_cancel['state'] = DISABLED
            self.button_select_eplus_dir['state'] = ACTIVE
            self.button_select_idf['state'] = ACTIVE
            if self.eplus_install.valid_install and self.selected_input_files:
                self.on_msg(_("Files selected, ready to go"))
                self.button_update_file['state'] = ACTIVE
            else:
                self.on_msg(_("No files selected; cannot transition"))
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

    def _on_press_open_input_dir(self):
        """
        This function handles the request to open the current input file directory in the default application
        """
        if not self.selected_input_files:
            return
        try:
            if platform.startswith("linux"):
                open_cmd = "xdg-open"
            elif platform == "darwin":
                open_cmd = "open"
            else:  # assuming windows  platform.startswith("win32"):
                open_cmd = "explorer"
            subprocess.Popen([open_cmd, self.selected_input_files[0][0].parent], shell=False)
        except Exception as e:
            messagebox.showerror(_("Could not open run directory") + str(e))

    def _on_press_choose_input_file(self):
        """
        This function handles the request to choose a new input, opening a dialog, and updating settings if applicable
        """
        cur_folder = self.conf.settings[Configuration.Keys.last_input_file_directory]
        cur_input_files = filedialog.askopenfilenames(
            title=_("Open File for Transition"),
            initialdir=cur_folder,
            filetypes=(
                ("EnergyPlus Input Files", "*.idf"),
                ("EnergyPlus Macro Files", "*.imf"),
                ("EnergyPlus List File", "*.lst"),
            )
        )
        if not cur_input_files:
            return
        self.conf.settings[Configuration.Keys.last_input_file_directory] = str(Path(cur_input_files[0]).parent)
        file_paths = []
        for cur_input_file in cur_input_files:
            cur_input_path = Path(cur_input_file)
            if cur_input_path.suffix == '.lst':
                lst_dir = cur_input_path.parent
                file_paths.extend(
                    (lst_dir / p) if not (p := Path(line.strip())).is_absolute() else p
                    for line in cur_input_path.read_text().splitlines()
                    if line.strip()
                )
            else:
                file_paths.append(cur_input_path)
        self.selected_input_files = [
            (p, self.get_idf_version(p)) for p in file_paths if p.is_file()
        ]
        self._populate_files_table()
        self._refresh_gui_state()

    def _on_press_update_idf(self) -> None:
        """
        This function handles the request to run Transition itself, building up the list of transitions,
        creating a new thread instance, prepping the gui, and running it
        """
        available_versions = {tr.source_version for tr in self.eplus_install.transitions_available}
        file_paths_and_versions_to_convert: dict[Path, float] = {
            p: v for p, v in self.selected_input_files
            if v is not None and v in available_versions
        }
        if len(file_paths_and_versions_to_convert) < len(self.selected_input_files):
            self.on_msg(_("Cannot find a matching transition tool for one or more IDF versions"))
        # we need to build up the list of transition steps to perform
        self._tk_var_progress.set(0)
        num_total_transitions = 0
        file_paths_and_transition_list = defaultdict(list)
        for file, original_version in file_paths_and_versions_to_convert.items():
            for tr in self.eplus_install.transitions_available:
                if tr.source_version < original_version:
                    continue
                file_paths_and_transition_list[file].append(tr)
                num_total_transitions += 1
        self._progress['maximum'] = num_total_transitions
        self.running_transition_threads = [
            TransitionRun(
                input_file=file,
                transition_list=transitions,
                keep_old=self._tk_var_keep_intermediate.get(),
                increment_callback=self._callback_on_increment,
                msg_callback=self.callback_on_msg,
                done_callback=self.callback_on_done
            )
            for file, transitions in file_paths_and_transition_list.items()
        ]
        self._threads_remaining = len(self.running_transition_threads)
        self.update_running = True
        executor = ThreadPoolExecutor(max_workers=cpu_count())
        for thread in self.running_transition_threads:
            executor.submit(thread.run)
        executor.shutdown(wait=False)
        self._refresh_gui_state()

    def _on_press_cancel(self):
        self.button_cancel['state'] = DISABLED
        for thread in self.running_transition_threads:
            thread.stop()

    # endregion

    # region background thread callbacks and handlers

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
        self._threads_remaining -= 1
        if self._threads_remaining == 0:
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
