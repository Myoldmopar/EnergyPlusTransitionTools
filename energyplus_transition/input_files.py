from dataclasses import dataclass
from pathlib import Path
from typing import Callable


def resolve_input_paths(input_paths: list[Path]) -> list[Path]:
    """Expand any .lst files into their constituent paths, resolving relative entries against the .lst's directory."""
    file_paths: list[Path] = []
    for path in input_paths:
        if path.suffix == ".lst":
            lst_dir = path.parent
            file_paths.extend(
                (lst_dir / p) if not (p := Path(line.strip())).is_absolute() else p
                for line in path.read_text().splitlines()
                if line.strip()
            )
        else:
            file_paths.append(path)
    return file_paths


@dataclass
class InputFile:
    path: Path
    version: float | None


def get_selected_input_files(input_paths: list[Path], on_msg: Callable[[str], None]) -> list[InputFile]:
    """Return a list of InputFile objects for the given input paths, which may include .lst files.

    Skips any paths that do not exist, printing a message for each skipped
    file.

    :param input_paths: A list of paths to input files, which may include .lst files
    :param on_msg: A callback function for printing messages about skipped files
    :rtype: A list of InputFile objects for the valid input files found at the given paths
    """
    resolved_paths = resolve_input_paths(input_paths=input_paths)
    input_files = []
    for idf_path in resolved_paths:
        if not idf_path.is_file():
            on_msg(f"File not found, skipping: {idf_path}")
            continue

        version = get_idf_version(path_to_idf=idf_path)

        input_files.append(InputFile(path=idf_path, version=version))
    return input_files


def get_idf_version(path_to_idf: Path) -> float | None:
    """Return the current version of a given input file.

    Uses a simplified parsing approach; only works for valid syntax files with no specialized error handling.

    :param path_to_idf: Absolute path to a EnergyPlus input file
    :rtype: A floating point version number for the input file, for example 8.5 for an 8.5.0 input file
    """
    # phase 1: read in lines of file
    lines = path_to_idf.read_text(errors="ignore").split("\n")
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
            else:  # exclamation > 0:
                this_line = line_text[:exclamation]
            if not this_line == "":
                lines_a.append(this_line)
    # phase 3: join entire array and re-split by semicolon
    idf_data_joined = "".join(lines_a)
    idf_object_strings = idf_data_joined.split(";")
    # phase 4: break each object into an array of object name and field values
    for this_object in idf_object_strings:
        tokens = this_object.split(",")
        if tokens[0].upper() == "VERSION":
            version_string = tokens[1]
            version_string_tokens = version_string.split(".")  # might be 2 or 3...
            version_number = float("%s.%s" % (version_string_tokens[0], version_string_tokens[1]))
            return version_number
    return None
