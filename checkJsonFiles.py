#!/usr/bin/python3
fileVersion = "1.1.0"                                       # File version

import pathlib
import os
from FF_analyzeCommand import FF_analyzeCommand

#   *****************
#   *** Main code ***
#   *****************

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
        print(F"Error: {messages}")
    else:
        if messages:
            print(F"Info: {messages}")
        understoodCommand = F"Understood command is {analyzer.command} {analyzer.deviceName}"
        if analyzer.valueToSetOriginal != None:
            understoodCommand += F" {analyzer.valueToSetOriginal}"
        elif analyzer.valueToSet != None:
            understoodCommand += F" {analyzer.valueToSet}"
        print(understoodCommand)
        result = F"Device name={analyzer.deviceName}, id={analyzer.deviceId}, idName={analyzer.deviceIdName}, command value={analyzer.commandValue} ({analyzer.commandValueText})"
        if analyzer.valueToSet != None:
            result += F", set={analyzer.valueToSet}"
            if analyzer.valueToSetOriginal != None:
                result += F"/{analyzer.valueToSetOriginal}"
            result += F", setBy={analyzer.setBy}"
        print(result)