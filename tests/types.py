from collections.abc import Callable
from typing import TypeAlias

from energyplus_transition.energyplus_path import EnergyPlusPath

FakeEplusInstall: TypeAlias = Callable[[list[tuple[str, str]]], EnergyPlusPath]
