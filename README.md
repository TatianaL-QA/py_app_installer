Scope:

This code is intended to automate latest version of Android app installation to local mobile devices form the AppCenter.


Prerequisites:

- platform-tools should be installed and added to path, code is using adb.exe 
- connect your devices using USB cable
- verify that adb has access to connected devices: > adb devices
- in case the list of devices is empty, or device is marked 'unauthorized' fix it using Developer Options on specific device
- check the modules are installed (file: requirements.txt)
- check your .env file includes correct data per each of your Apps from AppCenter (app secret from App Overview section in AppCenter)
- check your User's Token in AppCenter. Token, app's url(s), other secrets are located in the .env file

Structure of the .env file:

APPCENTER_URL1= // appcenter url as is for the first app (if you work with several, add urls and change the code
accordingly)
APPCENTER_URL2=

APPCENTER_TOKEN=

API_BASE_URL = "https://api.appcenter.ms/v0.1/apps" // please note the url is in quoutes
OWNER_NAME=
APP_NAME=
DEBUG=False // set to True if needed

DESTINATION_LOCAL=E:\destnation // default foulder to download the latest files from your device for PULL module


