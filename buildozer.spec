[app]
title = Qadrax Engine
package.name = qadrax_engine
package.domain = org.qadeer
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 5.2

# Requirements ko minimal pre-built package standard par rakh rahe hain
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

# P4A core framework ko completely block karne ke liye strict lines
android.blacklist_recipes = libffi, openssl, sqlite3
android.meta_data = com.google.android.gms.version=@integer/google_play_services_version

[buildozer]
log_level = 2
warn_on_root = 0
