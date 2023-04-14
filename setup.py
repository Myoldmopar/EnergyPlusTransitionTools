from pathlib import Path
from platform import system
from setuptools import setup

from energyplus_transition import NAME, VERSION


readme_file = Path(__file__).parent.resolve() / 'README.md'
readme_contents = readme_file.read_text()

install_requires = ['PLAN-Tools>=0.5']
if system() == 'Windows':
    install_requires.append('pypiwin32')

setup(
    name=NAME,
    version=VERSION,
    description='A library and tkinter-based tool for transitioning EnergyPlus input files',
    url='https://github.com/myoldmopar/EnergyPlusTransitionTools',
    license='ModifiedBSD',
    packages=['energyplus_transition'],
    package_data={"energyplus_transition": ["icons/*.png", "icons/*.ico", "icons/*.icns"],},
    include_package_data=True,
    long_description=readme_contents,
    long_description_content_type='text/markdown',
    author="Edwin Lee, for NREL, for the United States Department of Energy",
    install_requires=install_requires,
    entry_points={
        'gui_scripts': ['energyplus_transition_gui=energyplus_transition.runner:main_gui'],
        'console_scripts': ['energyplus_transition_configure=energyplus_transition.configure:configure_cli']
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Physics',
        'Topic :: Utilities',
    ],
    platforms=[
        'Linux (Tested on Ubuntu)', 'MacOSX', 'Windows'
    ],
    keywords=[
        'energyplus_launch', 'ep_launch',
        'EnergyPlus', 'eplus', 'Energy+',
        'Building Simulation', 'Whole Building Energy Simulation',
        'Heat Transfer', 'HVAC', 'Modeling',
    ]
)
