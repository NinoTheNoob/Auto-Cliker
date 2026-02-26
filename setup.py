from setuptools import setup

APP = ['clicker_gui.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': False,
    'packages': ['PyQt6', 'pyautogui', 'rubicon'], # Added rubicon here
    'includes': ['PyQt6.QtCore', 'PyQt6.QtWidgets'],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)