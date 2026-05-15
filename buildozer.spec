[app]

# App Title
title = Qadrax Engine

# Package
package.name = qadrax_engine
package.domain = org.qadrax

# Source
source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,json,txt,wav,mp3

# Exclude unnecessary files
source.exclude_dirs = tests, bin, venv, .git, __pycache__

# Version
version = 8.0

# Orientation
orientation = portrait

# Fullscreen
fullscreen = 0

# Requirements
# Optimized for Android + Pandas/Numpy support
requirements = python3,hostpython3,kivy==2.3.0,kivymd==1.1.1,numpy,pandas,yfinance,requests,certifi,plyer,pyjnius,urllib3,chardet,idna

# Permissions
android.permissions = INTERNET, VIBRATE, FOREGROUND_SERVICE, POST_NOTIFICATIONS

# Android APIs
android.api = 35
android.minapi = 29
android.sdk = 35

# NDK
android.ndk = 26b
android.ndk_api = 29

# Architectures
android.archs = arm64-v8a, armeabi-v7a

# Presplash / Icon (optional)
# presplash.filename = data/presplash.png
# icon.filename = data/icon.png

# Allow Backup
android.allow_backup = True

# Enable AndroidX
android.enable_androidx = True

# Window settings
window.softinput_mode = resize

# Faster startup
android.accept_sdk_license = True

# Logcat filters
android.logcat_filters = *:S python:D

# Entry point
entrypoint = main.py

# Theme
android.apptheme = "@android:style/Theme.NoTitleBar"

# Prevent black screen issues
android.presplash_color = #000000

# Build mode
p4a.bootstrap = sdl2

# Recommended for stability
osx.python_version = 3
osx.kivy_version = 2.3.0


[buildozer]

# Log level
log_level = 2

# Warn if root
warn_on_root = 1