Scope:
This code is intended to automate latest version of Android app installation to local mobile devices form the AppCenter.

Prerequisites:
- platform-tools should be installed and added to path, code is using adb.exe 
- connect your devices using USB cable
- verify that adb has access to connected devices: > adb devices
- in case the list of devices is empty, or device is marked 'unauthorized' fix it using Developer Options on specific device
- check the modules are installed (file: requirements.txt)
- check your .env file includes correct data per each of your Apps from AppCenter (app secret from App Overview section in AppCenter)
- check your User's Token in AppCenter. Token and secrets, should not be exposed. Hide them both in CI/CD
