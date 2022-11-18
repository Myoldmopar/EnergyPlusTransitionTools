from pathlib import Path
from subprocess import check_output, CalledProcessError
from sys import platform
from typing import List, Optional
from ep_transition.transition_binary import TransitionBinary


class EnergyPlusPath(object):
    """
    This class provides some meaningful variables about an EnergyPlus install tree

    :ivar install_root: An installation path object, as in /Applications/EnergyPlus-9-6-0/
    :ivar version: The version number suffix, in the form: '?.?.?'
    :ivar transition_directory: Absolute path to a transition run directory within the given installation directory
    :ivar transitions_available: A list of :py:class:`TransitionBinary <TransitionBinary.TransitionBinary>`
        instances available in this installation
    """

    def __init__(self, install_root: str):
        self.install_root = Path(install_root)
        # initialize values assuming it is broken
        self.valid_install = False
        self.transition_directory: Optional[Path] = None
        self.transitions_available: List[TransitionBinary] = []
        self.version: str = "Unknown.Ep.Version"
        # then overwrite if possible
        if self.install_root.exists():
            self.transition_directory = self.install_root / 'PreProcess' / 'IDFVersionUpdater'
            binary_paths = list(self.transition_directory.glob('Transition-V*'))
            self.transitions_available = [TransitionBinary(x) for x in binary_paths]
            self.transitions_available.sort(key=lambda tb: tb.source_version)
            try:
                raw_version_output = check_output([str(self.install_root / 'energyplus'), '-v'], shell=False)
                string_version_output = raw_version_output.decode('utf-8')
                version_token = string_version_output.split(',')[1].strip()
                version_description = version_token.split(' ')[1]
                just_version_number = version_description.split('-')[0]
                self.version = just_version_number
            except CalledProcessError:
                pass
            except FileNotFoundError:
                pass
            else:
                self.valid_install = True

    @staticmethod
    def try_to_auto_find() -> Optional[Path]:
        if platform.startswith("linux"):
            install_base = Path('/eplus/installs/')  # ('/usr/local/EnergyPlus*')
        elif platform == "darwin":
            install_base = Path('/Applications/EnergyPlus*')
        else:  # assuming windows
            install_base = Path('C:/EnergyPlusV*')
        eplus_install_dirs = list(install_base.glob('EnergyPlus*'))
        if len(eplus_install_dirs) == 0:
            return None
        highest_version = -1
        highest_version_instance = None
        for found_install in eplus_install_dirs:
            version_tokens = found_install.name.split('-')
            major_dot_minor = f"{version_tokens[-3]}.{version_tokens[-2]}"
            this_version = float(major_dot_minor)
            if this_version > highest_version:
                highest_version = this_version
                highest_version_instance = found_install
        return highest_version_instance

    def __str__(self) -> str:
        return f"E+Install ({'valid' if self.valid_install else 'invalid'}) : {self.install_root}"


if __name__ == "__main__":
    default = EnergyPlusPath.try_to_auto_find()
    instance = EnergyPlusPath(str(EnergyPlusPath.try_to_auto_find()))
