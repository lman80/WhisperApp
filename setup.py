"""
setup.py for building WhisperApp as a native macOS .app bundle.
Run: python setup.py py2app
"""
from setuptools import setup
import os

# Get the assets directory
ASSETS_DIR = os.path.join(os.path.dirname(__file__), 'whisperapp', 'assets')

APP = ['whisperapp/__main__.py']
DATA_FILES = [
    ('assets', [
        os.path.join(ASSETS_DIR, 'drop.mp3'),
        os.path.join(ASSETS_DIR, 'AppIcon.png'),
        os.path.join(ASSETS_DIR, 'MenuBarIcon.png'),
    ])
]

OPTIONS = {
    'argv_emulation': False,
    'iconfile': os.path.join(ASSETS_DIR, 'AppIcon.png'),
    'plist': {
        'CFBundleName': 'WhisperApp',
        'CFBundleDisplayName': 'WhisperApp',
        'CFBundleIdentifier': 'com.lman80.whisperapp',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'LSUIElement': True,  # Menu bar app - no dock icon
        'NSMicrophoneUsageDescription': 'WhisperApp needs microphone access for voice transcription.',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '12.0',
    },
    'packages': [
        'whisperapp',
        'rumps',
        'pyperclip',
        'sounddevice',
        'scipy',
        'pynput',
        'mlx',
        'mlx_lm',
        'parakeet_mlx',
    ],
    'includes': [
        'AppKit',
        'Foundation',
        'Cocoa',
        'Quartz',
        'PyObjCTools',
        'objc',
    ],
    'excludes': [
        'tkinter',
        'matplotlib',
        'PIL',
        'numpy.distutils',
    ],
    'resources': [ASSETS_DIR],
}

setup(
    name='WhisperApp',
    version='1.0.0',
    description='macOS voice-to-text dictation with local AI models',
    author='lman80',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
