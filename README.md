# EnergyPlusTransitionTools

A library of transition functionality.
Currently it is a super simple Python Tk-based IDFVersionUpdater tool.
Soon it will hopefully contain the actual transition mechanics.

# Documentation [![Documentation Status](https://readthedocs.org/projects/energyplustransitiontools/badge/?version=latest)](https://energyplustransitiontools.readthedocs.io/en/latest/?badge=latest)

Project is documented on ReadTheDocs.

# Testing

[![Flake8](https://github.com/Myoldmopar/EnergyPlusTransitionTools/actions/workflows/flake8.yml/badge.svg)](https://github.com/Myoldmopar/EnergyPlusTransitionTools/actions/workflows/flake8.yml)
[![Run Tests](https://github.com/Myoldmopar/EnergyPlusTransitionTools/actions/workflows/unit_tests.yml/badge.svg)](https://github.com/Myoldmopar/EnergyPlusTransitionTools/actions/workflows/unit_tests.yml)

Project is continually tested using GitHub Actions

# Releases

[![Release_to_PyPi](https://github.com/Myoldmopar/EnergyPlusTransitionTools/actions/workflows/pypi.yml/badge.svg)](https://github.com/Myoldmopar/EnergyPlusTransitionTools/actions/workflows/pypi.yml)

Project is built into a wheel and pushed to pypi for each tag: https://pypi.org/project/ep-transition-tools/.
To install, it will be `pip install energyplus-transition-tools`.
This will (eventually) install 2 binaries into the python environment: `energyplus_transition_gui` and `energyplus_transition_cli`. 
