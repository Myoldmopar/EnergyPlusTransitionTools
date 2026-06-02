import argparse
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import cpu_count
from pathlib import Path

from energyplus_transition.energyplus_path import EnergyPlusPath
from energyplus_transition.input_files import cleanup_transition_artifacts, get_selected_input_files
from energyplus_transition.transition_run import TransitionRun

try:
    from tqdm import tqdm

    TQDM_AVAILABLE = True
except ImportError:  # pragma: no cover
    TQDM_AVAILABLE = False


def get_parser() -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser(description="Transition EnergyPlus IDF files to a newer version")
    parser.add_argument("idf_files", nargs="+", type=Path, metavar="IDF_FILE", help="IDF/IMF/lst file(s) to transition")
    parser.add_argument(
        "-e",
        "--eplus-dir",
        type=Path,
        default=None,
        metavar="DIR",
        help="EnergyPlus installation directory (auto-detected if omitted)",
    )
    parser.add_argument(
        "-s", "--save-intermediate", action="store_true", help="Save intermediate versions during transitioning"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("-p", "--progress", action="store_true", help="Show a tqdm progress bar (requires tqdm)")
    parser.add_argument(
        "-j", "--jobs", type=int, default=None, metavar="N", help="Number of parallel workers (default: number of CPUs)"
    )
    parser.add_argument(
        "-t",
        "--to-version",
        type=float,
        default=None,
        metavar="VERSION",
        help="Stop transitioning at this target version (e.g. 24.2)",
    )

    return parser


class Runner:
    def __init__(self, verbose: bool = False, progress: bool = False, jobs: int | None = None):
        self.verbose = verbose
        if progress and not TQDM_AVAILABLE:  # pragma: no cover
            print("Warning: --progress requires tqdm (`pip install tqdm`), continuing without progress bar.")
            progress = False
        self.progress = progress
        self.jobs = jobs if jobs is not None else cpu_count()
        self.pbar: "tqdm | None" = None
        # Number of Individual Transitions to run across all files, used for progress tracking
        self.progress_transitions = 0
        self.num_total_transitions = 0
        # Number of IDF Files to transition, used for progress tracking
        self.progress_files = 0
        self.num_total_files = 0
        self.runs: list[TransitionRun] = []

    def _print_or_write(self, message: str) -> None:
        if self.progress:
            tqdm.write(message)
        else:
            print(message)

    def on_increment(self) -> None:
        self.progress_transitions += 1
        if self.pbar is not None:
            self.pbar.update(1)

    def on_msg(self, message: str) -> None:
        if self.verbose:
            self._print_or_write(message)

    def on_done(self, message: str) -> None:
        self.progress_files += 1
        if self.verbose:
            self._print_or_write(
                f"Done: {message} ({self.progress_files}/{self.num_total_files} files, "
                f"{self.progress_transitions}/{self.num_total_transitions} transitions)"
            )

    def collect_runs(self, eplus_install: EnergyPlusPath, input_paths: list[Path], save_intermediate: bool) -> None:
        available_versions = {tr.source_version for tr in eplus_install.transitions_available}
        selected_input_files = get_selected_input_files(input_paths=input_paths, on_msg=self.on_msg)

        self.num_total_files = 0
        self.num_total_transitions = 0
        self.runs = []
        for input_file in selected_input_files:
            if input_file.version is None:
                self.on_msg(f"Could not determine version for: {input_file.path}, skipping")
                continue
            if input_file.version not in available_versions:
                self.on_msg(
                    f"Version {input_file.version} for file {input_file.path} is not supported "
                    "by available transitions, skipping"
                )
                continue
            transitions = [tr for tr in eplus_install.transitions_available if tr.source_version >= input_file.version]
            if not transitions:  # pragma: no cover
                self.on_msg(f"No transitions needed for: {input_file.path}, skipping")
                continue

            self.num_total_files += 1
            self.num_total_transitions += len(transitions)

            # Still backup the original one
            if not save_intermediate:
                TransitionRun.backup_file_before_transition(
                    transition_instance=transitions[0], input_file=input_file.path
                )
            self.runs.append(
                TransitionRun(
                    input_file=input_file.path,
                    transition_list=transitions,
                    keep_old=save_intermediate,
                    increment_callback=self.on_increment,
                    msg_callback=self.on_msg,
                    done_callback=self.on_done,
                )
            )

    def _make_tqdm_callbacks(
        self, run: TransitionRun
    ) -> tuple[Callable[[], None], Callable[[], None], Callable[[str], None]]:
        file_bar = None

        def on_started() -> None:
            nonlocal file_bar
            file_bar = tqdm(total=len(run.transition_list), leave=False, desc=run.input_file.name)

        def on_increment() -> None:
            self.on_increment()
            if file_bar is not None:  # pragma: no cover
                file_bar.update(1)

        def on_done(message: str) -> None:
            if file_bar is not None:  # pragma: no cover
                file_bar.close()
            self.on_done(message)
            cleanup_transition_artifacts(idf_path=run.input_file)

        return on_started, on_increment, on_done

    def execute(self) -> None:
        print(
            f"Starting transitions with {self.jobs} parallel workers: "
            f"{self.num_total_files} files, {self.num_total_transitions} transitions"
        )
        if self.progress:
            self.pbar = tqdm(total=self.num_total_transitions, position=0, leave=True, desc="Total")
            for run in self.runs:
                run.started_callback, run.increment_callback, run.done_callback = self._make_tqdm_callbacks(run)
        try:
            executor = ThreadPoolExecutor(max_workers=self.jobs)
            futures = [executor.submit(run.run) for run in self.runs]
            executor.shutdown(wait=True)
            for future in futures:
                future.result()  # re-raise any exceptions
        finally:
            if self.pbar:
                self.pbar.close()
                self.pbar = None


def main(args_: list[str] | None = None) -> None:

    parser = get_parser()
    args = parser.parse_args(args_)

    runner = Runner(verbose=args.verbose, progress=args.progress, jobs=args.jobs)

    if args.eplus_dir:
        eplus_dir = args.eplus_dir
    else:
        eplus_dir = EnergyPlusPath.try_to_auto_find()
        if eplus_dir is None:
            raise RuntimeError("Could not find an EnergyPlus installation. Use --eplus-dir to specify one.")

    eplus_install = EnergyPlusPath(install_root=eplus_dir)
    if not eplus_install.valid_install:
        raise ValueError(f"Invalid EnergyPlus installation at: {eplus_dir}")
    print(f"Using EnergyPlus {eplus_install.version} at {eplus_install.install_root}")

    if args.to_version:
        print(f"Will transition up to version {args.to_version}")
        # Chck that the to_version is in transitions_available to begin with
        if not any(tr.target_version <= args.to_version for tr in eplus_install.transitions_available):
            print(f"No transitions available up to version {args.to_version}, exiting.")
            return
        # Now we filter the newer ones out
        eplus_install.transitions_available = [
            tr for tr in eplus_install.transitions_available if tr.target_version <= args.to_version
        ]

    runner.collect_runs(
        eplus_install=eplus_install, input_paths=args.idf_files, save_intermediate=args.save_intermediate
    )
    if not runner.runs:
        print("No valid input files to transition, exiting.")
        return

    runner.execute()


if __name__ == "__main__":  # pragma: no cover
    main()
