#!/usr/bin/python3
fileVersion = "1.0.0"                                       # File version

import pathlib
import os
from FF_analyzeCommand import FF_analyzeCommand, get_overloads

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

with open('config.txt', 'wt') as outFile:
    for device in analyzer.devicesDict.keys():
        deviceName = analyzer.getValue2(analyzer.devicesDict, device, 'name')
        deviceClass = analyzer.getValue2(analyzer.deviceClassesDict, device.split(' ')[0], "deviceClass")
        deviceClassMappings = analyzer.getValue2(analyzer.mappingsDict, deviceClass, 'mapping')
        deviceValues = analyzer.getValue2(analyzer.deviceClassesDict, device.split(' ')[0], "values")
        deviceCommands = ""
        for command in analyzer.commandsDict:
            if analyzer.getValue2(analyzer.commandsDict, command, 'command') in deviceClassMappings:
                deviceCommands += "/" + command
        setValues = ""
        if deviceValues:
            for value in deviceValues.keys():
                setValues += "/" + value
            setValues = " [" + setValues[1:] + "]"
        outFile.write(deviceName+"\t"+deviceCommands[1:]+" "+device+setValues+"\n")
