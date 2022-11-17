from pathlib import Path
from setuptools import setup

from ep_transition import NAME, VERSION


readme_file = Path(__file__).parent.resolve() / 'README.md'
readme_contents = readme_file.read_text()

setup(
    name=NAME,
    version=VERSION,
    description='A library and tkinter-based tool for transitioning EnergyPlus input files',
    url='https://github.com/myoldmopar/idfversionupdater2',
    license='',
    packages=['ep_transition'],
    package_data={},
    include_package_data=True,
    long_description=readme_contents,
    long_description_content_type='text/markdown',
    author="Edwin Lee via NREL via United States Department of Energy",
    install_requires=[],
    entry_points={
        'console_scripts': ['ep_transition_gui=ep_transition.runner:main_gui']
    }
)
