import glob
from pathlib import Path
from sys import platform
from ep_transition.transition_binary import TransitionBinary


class EnergyPlusPath(object):
    """
    This class provides a summary of the latest installed version of EnergyPlus
    The constructor looks up the available installations, picks the most recent (inferred from version number),
    and sets some parameters

    :ivar installation_path: An installation path on Mac, following the form: '/Applications/EnergyPlus-?-?-?/'
    :ivar version_number: The version number suffix, in the form: '?-?-?'
    :ivar transition_directory: Absolute path to a transition run directory within the given installation directory
    :ivar transitions_available: A list of :py:class:`TransitionBinary <TransitionBinary.TransitionBinary>`
        instances available in this installation
    """

    def __init__(self):
        # get all the installed versions first, and sort them, then return the last one
        install_folders = []
        if platform.startswith("linux"):
            install_folders = glob.glob('/eplus/installs/EnergyPlus*')  # ('/usr/local/EnergyPlus*')
        elif platform == "darwin":
            install_folders = glob.glob('/Applications/EnergyPlus*')
        elif platform.startswith("win32"):
            install_folders = glob.glob('C:/EnergyPlusV*')
        ep_versions = sorted([x for x in install_folders])
        self.installation_path = Path(ep_versions[-1])
        folder_name = self.installation_path.name
        if 'EnergyPlus' not in folder_name:
            pass  # TODO: Error
        self.version_number = folder_name[11:]
        self.transition_directory = self.installation_path / 'PreProcess' / 'IDFVersionUpdater'
        binary_paths = glob.glob(str(self.transition_directory / 'Transition-V*'))
        self.transitions_available = [TransitionBinary(x) for x in binary_paths]
