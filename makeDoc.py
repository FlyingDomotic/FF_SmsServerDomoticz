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
        if analyzer.classAfterDevice:
            deviceClass = device.split(' ')[len(device.split(" "))-1]
        else:
            deviceClass = device.split(' ')[0]
        deviceName = analyzer.getValue2(analyzer.devicesDict, device, 'name')
        deviceCommandClass = analyzer.getValue2(analyzer.deviceClassesDict, deviceClass, 'commandClass')
        deviceCommandClasses = analyzer.getValue2(analyzer.commandClassesDict, deviceCommandClass, 'commandValue')
        deviceClassMappings = analyzer.getValue2(analyzer.deviceClassesDict, deviceClass, "mapping")
        deviceCommands = ""
        for command in analyzer.commandsDict:
            if analyzer.getValue2(analyzer.commandsDict, command, 'commandValue') in deviceCommandClasses:
                deviceCommands += "/" + command
        setValues = ""
        if deviceClassMappings:
            for value in deviceClassMappings.keys():
                setValues += "/" + value
            setValues = " [" + setValues[1:] + "]"
        outFile.write(deviceName+"\t"+deviceCommands[1:]+" "+device+setValues+"\n")
