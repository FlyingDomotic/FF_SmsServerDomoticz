#!/usr/bin/python3
fileVersion = "1.0.0"                                       # File version

import pathlib
import os
from FF_analyzeCommand import FF_analyzeCommand

#   *****************
#   *** Main code ***
#   ****************

# Set current working directory to this python file folder
currentPath = pathlib.Path(__file__).parent.resolve()
os.chdir(currentPath)

# Get this file name (w/o path & extension)
cdeFile = pathlib.Path(__file__).stem

decodeFile = os.path.join(currentPath, 'smsTables.json')
analyzer = FF_analyzeCommand()

errorText, messages = analyzer.loadData(decodeFile)
print("LoadData status: "+(errorText if errorText != "" else "Ok"))
print(messages)
if errorText:
    exit()

while (1):
    try:
        givenCommand = input("Test command: ")
    except:
        break
    if not givenCommand:
        break
    errorText, messages = analyzer.analyzeCommand(givenCommand)
    if errorText != "":
        print("Error: "+messages)
    else:
        if messages:
            print("Info: "+messages)
        print("Understood command is "+
            analyzer.command+
            " "+analyzer.deviceClass+
            " "+analyzer.deviceName+
            (" "+analyzer.valueToSet if analyzer.valueToSet != None else ""))
        print("Device name="+analyzer.deviceName +
            ", id="+str(analyzer.deviceId) +
            ", idName="+analyzer.deviceIdName +
            ", command value="+str(analyzer.commandValue)+" ("+analyzer.commandValueText+")"+
            ((", set="+analyzer.valueToSet+("/"+str(analyzer.valueToSetRemapped) if analyzer.valueToSetRemapped != None else "") if analyzer.valueToSet != None else "")))