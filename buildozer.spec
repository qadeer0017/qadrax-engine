[app]
title = Qadrax Engine
package.name = qadrax_engine
package.domain = org.qadeer
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 5.2

# Mismatch se bachne ke liye requirements ko clean kar diya hai
requirements = python3,kivy==2.3.0,kivymd==1.1.1,requests,certifi,urllib3,chardet,idna

orientation = portrait
fullscreen = 0

archs = arm64-v8a

android.api = 33
android.minapi = 24
android.ndk_api = 24
android.private_storage = 1
android.accept_sdk_license = True
android.skip_bytecode = 1

# Pre-compiled environment locks
android.blacklist_recipes = libffi, openssl, sqlite3

[buildozer]
log_level = 2
warn_on_root = 0
