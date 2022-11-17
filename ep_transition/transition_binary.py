from pathlib import Path


class TransitionBinary(object):
    """
    This class describes a single transition binary in the installation
    The class is constructed from the full path to the binary, then source and target versions are parsed from this path
    and the filenames

    :param full_path: Full path to the transition binary itself

    :ivar full_path_to_binary: Copy of the full path to binary passed into the constructor
    :ivar binary_name: This is just the filename portion of the binary executable
    :ivar source_version: This is the source version of this particular transition, for example,
                          in V8-5-0-to-8-6-0, this will be 8.5
    :ivar target_version: This is the target version of this particular transition, for example,
                          in V8-5-0-to-8-6-0, this will be 8.6
    """

    def __init__(self, full_path: str):
        self.full_path_to_binary = Path(full_path)
        self.binary_name = self.full_path_to_binary.name
        self.source_version = float(self.binary_name[12:15].replace('-', '.'))
        self.target_version = float(self.binary_name[22:25].replace('-', '.'))
