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
                self.version = version_description.split('-')[0]
                self.valid_install = True
            except CalledProcessError:
                pass
            except FileNotFoundError:
                pass

    @staticmethod
    def try_to_auto_find() -> Optional[Path]:
        if platform.startswith("linux"):
            install_bases = (Path('/usr/local'), Path('/eplus/installs/'))
        elif platform == "darwin":
            install_bases = (Path('/Applications'),)
        else:  # assuming windows
            install_bases = (Path(r'C:/'),)
        eplus_install_dirs = []
        for base in install_bases:
            eplus_install_dirs.extend(list(base.glob('EnergyPlus*')))
        if len(eplus_install_dirs) == 0:
            return None
        highest_version = -1
        highest_version_instance = None
        for found_install in eplus_install_dirs:
            just_version_suffix = found_install.name[10:]
            print(f"{just_version_suffix=}")
            if just_version_suffix.startswith('V') or just_version_suffix.startswith('-'):
                just_version_suffix = just_version_suffix[1:]
            version_tokens = just_version_suffix.split('-')
            print(f"{version_tokens=}")
            if len(version_tokens) < 2:
                print(f"Skipping install at: {found_install}")
                continue
            major_dot_minor = f"{version_tokens[0]}.{version_tokens[1]}"
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
    pass
