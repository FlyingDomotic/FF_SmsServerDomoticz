"""
This code analyzes a command and try to decode a command against a given list.

It was originally designed to get (French) SMS messages to remotely manage automation system.

General command organization is: [command] [device type] [device name] [value to set].

For example: "allume la lampe de la cuisine", "ouvre le volet du salon", "règle la consigne de la clim du séjour sur 21", ...

Again, this structure is French oriented, and should be adapted to other languages/grammar if needed.
For example, to turn a bulb on, French is "Allume lampe cuisine", word to word translated into "turn on bulb kitchen",
while English people would better say "turn kitchen bulb on".
A new version could implement different grammars, users' requests may speed-up the process ;-)

Code allows to work with UTF-8 data. You may optionally restrict comparison and output to 7 bits ASCII equivalent to help processing.

More details on README.md

Author: Flying Domotic
License: GNU GPL V3
"""

import pathlib
import os
import json
from re import A, search
from typing_extensions import get_overloads
import unidecode

class FF_analyzeCommand:
    # Class initialization 
    def __init__(self):
        self.fileVersion = "1.0.0"                          # File version
        self.errorSeen = False;                             # Do we seen an error ?
        self.convertUtf8ToAscii7Input = True;               # Convert input to Ascii7?
        self.convertUtf8ToAscii7Output = True;              # Convert saved output to Ascii7?
        self.firstErrorMessage = ""                         # First error message seen
        self.allMessages = ""                               # All messages to be printed
        self.ignoresList = []                               # List of keywords to be ignored
        self.mappingValueDict = {}                          # Dictionary of mappingValues
        self.commandsDict = {}                              # Dictionary of commands
        self.mappingsDict = {}                              # Dictionary of mappings
        self.deviceClassesDict = {}                         # Dictionary of deviceClasses
        self.devicesDict = {}                               # Dictionary of devices
        self.checkFile = ""                                 # File being scanned
        self.checkPhase = ""                                # Scan phase
        self.command = ""                                   # Command
        self.commandValue = 0                               # Command value in numeric format
        self.commandValueText = ""                          # Command value in text format
        self.deviceName = ""                                # Device name
        self.deviceId = 0                                   # DeviceId
        self.deviceIdName = ""                              # Name of deviceId
        self.deviceClass = ""                               # Device class to select in filterClass
        self.valueToSet = None                              # Value to set
        self.valueToSetRemapped = None                      # Value to set remapped

    # Filter class to a given value
    def filterClass(self, pair):
        key, value = pair
        classValue = key.split(" ")[0]
        if classValue == self.deviceClass:
            return True
        return False

    # Prints an error message, saving it and setting error flag
    def printError(self, message):
        self.allMessages += (self.utf8ToAscii7(message) if self.convertUtf8ToAscii7Output else message)+"\r\n"
        # Save message under required format
        if self.firstErrorMessage == "":
            self.firstErrorMessage = self.utf8ToAscii7(message) if self.convertUtf8ToAscii7Output else message
        self.errorSeen = True

    # Prints an info message
    def printInfo(self, message):
        self.allMessages += (self.utf8ToAscii7(message) if self.convertUtf8ToAscii7Output else message)+"\r\n"

    # Load a dictionary to a file
    def loadDictionary(self, file):
        # Print dupplicates on dictionnary
        def dict_print_duplicates(ordered_pairs):
            d = {}
            for k, v in ordered_pairs:
                if k in d:
                    print ("Warning: You have duplicate definition of %r in JSON declaration" % (k,))
                d[k] = v
            return d
        if os.path.exists(file):
            with open(file) as f:
                try:
                    return json.loads(f.read(), object_pairs_hook=dict_print_duplicates)
                except Exception as e:
                    self.printError(str(e)+" when loading "+file)
                    return None
        else:
            return {}

    # Returns a dictionary value giving a key or default value if not existing
    def getValue(self, dict, key, default=None):
        if dict != None:
            if key in dict:
                return dict[key]
        return default

    # Returns a dictionary value giving a couple of keys or default value if not existing
    def getValue2(self, dict, key1, key2, default=None):
        if dict != None:
            if key1 in dict and key2 in dict[key1]:
                return dict[key1][key2]
        return default

    # Converts an UTF-8 string to ASCII 7 bits equivalent (remove accents and more)
    def utf8ToAscii7(self, variable):
        if type(variable).__name__ == "str":
            return unidecode.unidecode(variable)
        return variable

    # Compare 2 values on shortest size with minimal length and eventual UTF-8 to ASCII 7 conversion
    #   at user's disposal to make external tests with same behavior than this function
    def compare(self, value1, value2, minLength=-1):
        val1 = self.convertUserData(value1)
        val2 = self.convertUserData(value2)
        lenToTest = len(val1) if len(val1) <= len(val2) else len(val2)
        if minLength >= 1:
            if minLength > lenToTest: lenToTest = minLength

        return val1[:lenToTest].lower() == val2[:lenToTest].lower()

    # Converts data from UTF-8 to ASCII 7 if requested by user
    def convertUserData(self, variable):
        if self.convertUtf8ToAscii7Input:
            # Data to convert could be string, list of string or dict
            if type(variable).__name__ == "list":
                # This is list of strings
                newList = []
                for item in variable:
                    newList.append(self.utf8ToAscii7(item).lower())
                return newList
            if type(variable).__name__ == "dict":
                # This is dict, get keys
                newList = []
                for item in variable.keys():
                    newList.append(self.utf8ToAscii7(item).lower())
                return newList
            elif type(variable).__name__ == "str":
                # This is a string
                return self.utf8ToAscii7(variable).lower()
        # No conversion needed or type not list or string, return original value
        return variable

    # Compare 2 values, puts an error message and returns false if not equal, true else
    def compareValue(self, msg, valueIs, valueShouldBe, context=None):
        isOk = False
        if type(valueShouldBe).__name__ in ["list","dict"]:
            isOk = (self.convertUserData(valueIs) in self.convertUserData(valueShouldBe))
        else:
            isOk = (self.convertUserData(valueIs) == self.convertUserData(valueShouldBe))
        if not isOk:
            self.printError("Error analyzing "+self.checkFile+", when "+self.checkPhase+": "+msg+" is "+str(valueIs)+", should be "+str(valueShouldBe.keys()).replace("dict_keys(","")[:-1] if type(valueShouldBe).__name__ == "dict" else valueShouldBe)
            if context != None:
                self.printInfo("Context is "+str(context))
            return False
        return True

    # Compare 2 values, puts an error message and returns false if equal, true else
    def compareNotValue(self, msg, valueIs, valueShouldBe, context=None):
        isOk = False
        if type(valueShouldBe).__name__ in ["list","dict"]:
            isOk = (self.convertUserData(valueIs) not in self.convertUserData(valueShouldBe))
        else:
            isOk = (self.convertUserData(valueIs) != self.convertUserData(valueShouldBe))
        if not isOk:
            self.printError("Error analyzing "+self.checkFile+", when "+self.checkPhase+": "+msg+" should not be "+str(valueShouldBe.keys()).replace("dict_keys(","")[:-1] if type(valueShouldBe).__name__ == "dict" else valueShouldBe)
            if context != None:
                self.printInfo("Context is "+str(context))
            return False
        return True

    # Compare 2 types, puts an error message and returns false if not equal, true else
    def compareType(self, msg, variableIs, typeShouldBe, context = None):
        isOk = False
        if type(typeShouldBe).__name__ in ["list", "dict"]:
            isOk = (type(variableIs).__name__ in typeShouldBe)
        else:
            isOk = (type(variableIs).__name__ == typeShouldBe)
        if not isOk:
            self.printError("Error analyzing "+self.checkFile+", when "+self.checkPhase+": "+msg+" is "+type(variableIs).__name__+", should be "+str(typeShouldBe))
            self.printInfo("Content is "+str(variableIs))
            if context:
                self.printInfo('Context is '+str(context))
            return False
        return True

    # Find keyword in dictionary, checking for multiple matches
    #   List can contain values with spaces. In this case, as many keywords as word count in list element are compared
    def findInDict(self, keywords, startPtr, dict, text):
        matchingList = []
        # For each item in search list
        for item in dict.keys():
            # Split item using space as separator
            itemParts = item.split(" ")
            matchFound = True
            # For each keyword in item
            for ptr in range(0, len(itemParts)):
                # Check that we're still within keyword count
                if len(keywords) <= startPtr + ptr:
                    # No, this is not correct
                    matchFound = False
                else:
                    # Are the keyword chars same as item?
                    if self.convertUserData(itemParts[ptr][:len(keywords[startPtr+ptr])]) != self.convertUserData(keywords[startPtr+ptr]):
                        # No, this is not correct
                        matchFound = False
            # If we got a match
            if matchFound:
                # Add item to the list
                matchingList.append(item)
        if len(matchingList) == 0:
            self.printError(str(keywords[startPtr:])+' is not a known '+text+', use '+str(dict.keys()).replace("dict_keys(","")[:-1])
            return ""
        elif len(matchingList) > 1:
            self.printError(str(keywords[startPtr:])+' is ambiguous '+text+', could be '+str(matchingList))
            return ""
        else:
            return matchingList[0]

    def loadData(self, fileName):
        # Check data file
        self.checkFile = pathlib.Path(fileName).name
        self.checkPhase = "checking file"
        decodeData = self.loadDictionary(fileName)

        if self.compareType("decodeData type", decodeData, "dict"):
            self.checkPhase = "checking ignores"
            # Extract all "ignores" list
            self.ignoresList = self.getValue(decodeData,"ignores")
            if self.compareType("self.ignoresList type", self.ignoresList, "list"):
                pass

            self.checkPhase = "checking mapping values"
            # Extract all "mappingValues"
            self.mappingValueDict =  self.getValue(decodeData,"mappingValues")
            if self.compareType("self.mappingValueDict type", self.mappingValueDict, "dict"):
                # For each item in self.mappingValueDict
                for key in self.mappingValueDict.keys():
                    mappingValueItem = self.mappingValueDict[key]
                    if self.compareType("mappingValueItem type", mappingValueItem, "dict"):
                        # Get the "mappingValue"
                        mappingValueValue = self.getValue(mappingValueItem, "mappingValue")
                        if self.compareType("mappingValueValue type", mappingValueValue, "int", mappingValueItem):
                            pass

            self.checkPhase = "checking mappings"
            # Extract all "mappings"
            self.mappingsDict =  self.getValue(decodeData,"mappings")
            if self.compareType("mappingList type", self.mappingsDict, "dict"):
                # For each item in self.mappingsDict
                for key in self.mappingsDict.keys():
                    mappingItem = self.mappingsDict[key]
                    if self.compareType("mappingItem type", mappingItem, "dict"):
                        # Get the "mapping"
                        mappingMapping = self.getValue(mappingItem, "mapping")
                        # Check mapping keyword
                        if self.compareType("mappingMapping type", mappingMapping, "list", mappingItem):
                            # Scan all elements in list
                            for element in mappingMapping:
                                # Element should be in valueKeywords
                                if self.compareValue("mapping value", element , self.mappingValueDict, mappingItem):
                                    pass

            self.checkPhase = "checking commands"
            # Extract all "commands" list
            self.commandsDict =  self.getValue(decodeData,"commands")
            if self.compareType("commandList type", self.commandsDict, "dict"):
                # For each item in self.commandsDict
                for key in self.commandsDict.keys():
                    commandItem = self.commandsDict[key]
                    if self.compareType("commandItem type", commandItem, "dict"):
                        # Get the first "command"
                        commandCommand = self.getValue(commandItem, "command")
                        # Check command keyword
                        if self.compareType("commandCommand type", commandCommand, "str", commandItem):
                            # Value should be in self.mappingValueDict
                            if self.compareValue("command value", commandCommand , self.mappingValueDict, commandItem):
                                pass

            self.checkPhase = "checking device classes"
            # Extract all "deviceClasses"
            self.deviceClassesDict =  self.getValue(decodeData,"deviceClasses")
            if self.compareType("deviceClassesDict type", self.deviceClassesDict, "dict"):
                # For each item in deviceClassesDict
                for key in self.deviceClassesDict.keys():
                    deviceClassItem = self.deviceClassesDict[key]
                    if self.compareType("deviceClassItem type", deviceClassItem, "dict"):
                        # Get the first "deviceClass"
                        deviceClassClass = self.getValue(deviceClassItem, "deviceClass")
                        # Check deviceClassClass keyword
                        if self.compareType("deviceClassClass type", deviceClassClass, "str", deviceClassItem):
                            # deviceClass should be in mappinKeywords
                            if self.compareValue("deviceClass value", deviceClassClass , self.mappingsDict, deviceClassItem):
                                deviceClassValues = self.getValue(deviceClassItem, "values")
                                # If values are given, this should be a list
                                if self.compareType("deviceClassValues type", deviceClassValues, ["NoneType", "dict"], deviceClassItem):
                                    pass

            self.checkPhase = "checking devices"
            # Extract all "devices"
            self.devicesDict =  self.getValue(decodeData,"devices")
            if self.compareType("self.devicesDict type", self.devicesDict, "dict"):
                # For each item in self.devicesDict
                for key in self.devicesDict.keys():
                    deviceItem = self.devicesDict[key]
                    if self.compareType("deviceItem type", deviceItem, "dict"):
                        # Extract deviceClass item
                        self.deviceClass = key.split(" ")[0]
                        if self.compareNotValue("device class", self.deviceClass, "", deviceItem):
                            # Check for deviceClass in known list of deviceClasses
                            if self.compareValue("device class value", self.deviceClass , self.deviceClassesDict, deviceItem):
                                pass
                        # Extract index
                        deviceIndex = self.getValue(deviceItem, "index")
                        if self.compareType("device index", deviceIndex, ["str", "int"]):
                            # Index should not be empty or zero
                            self.compareNotValue("device index", deviceIndex, "", deviceItem)
                            self.compareNotValue("device index", deviceIndex, 0, deviceItem)

        if self.errorSeen:
            return "Error detected, please check "+fileName+" file!", self.allMessages
        else:
            return "", self.allMessages

    def analyzeCommand(self, givenCommand):
        # Init error seen and last message
        self.errorSeen = False
        self.firstErrorMessage = ""
        self.allMessages= ""
        self.command = ""                                   # Command
        self.commandValue = 0                               # Command value in numeric format
        self.commandValueText = ""                          # Command value in text format
        self.deviceName = ""                                # Device name
        self.deviceId = 0                                   # DeviceId
        self.deviceIdName = ""                              # Name of deviceId
        self.deviceClass = ""                               # Device class to select in filterClass
        self.valueToSet = None                              # Value to set
        self.valueToSetRemapped = None                      # Value to set remapped

        # Split each word of message, replacing tabs by spaces  
        keywords = givenCommand.replace("\t"," ").split(" ")

        # Remove words to ignore
        for ptr in range(len(keywords)):
            if keywords[ptr] in self.ignoresList:
                keywords[ptr] = ""

        # Rebuild command and clean leading/trailing spaces
        cleanCommand = " ".join(keywords).strip()

        # Remove double spaces
        while cleanCommand.find("  ") != -1:
            cleanCommand = cleanCommand.replace("  ", " ")
        
        # Split each word of cleaned message
        keywords = cleanCommand.split(" ")

        # Isolate command in first keyword
        keywordIndex = 0
        self.command = self.findInDict(keywords, keywordIndex, self.commandsDict, "command")
        if self.command != "":
            ##self.printInfo("Command is "+self.command)
            # move index into keywords
            keywordIndex += len(self.command.split(" "))
            # Isolate deviceClass in second keyword
            if len(keywords) < keywordIndex + 1:
                self.printError("No device class given!")
            else:
                self.deviceClass = self.findInDict(keywords, keywordIndex, self.deviceClassesDict, "deviceClass")
                if self.deviceClass != "":
                    ##printInfp("Device class is "+self.deviceClass)
                    # Don't move index into keywords as devices also include deviceClass
                    # keywordIndex += len(self.deviceClass.split(" "))
                    if len(keywords) < keywordIndex + 2 :
                        self.printError("No device given!")
                    else:
                        # Get deviceClass class
                        deviceClassClass = self.getValue2(self.deviceClassesDict, self.deviceClass, "deviceClass")
                        if not deviceClassClass:
                            self.printError("Can't find "+self.deviceClass+" device class...")
                        else:
                            ##self.printInfo(self.deviceClass+" device class is "+deviceClassClass)
                            # Get deviceClass mapping
                            mappingMapping = self.getValue2(self.mappingsDict, deviceClassClass, "mapping")
                            if not mappingMapping:
                                self.printError("Can't find "+deviceClassClass+" device class mapping...")
                            else:
                                ##self.printInfo(deviceClassClass+" mapping is "+str(mappingMapping))
                                # Get command command
                                commandCommand = self.getValue2(self.commandsDict, self.command, "command")
                                if not commandCommand:
                                    self.printError("Can't find "+self.command+" command command...")
                                else:
                                    ##self.printInfo(self.command+" command is "+commandCommand)
                                    if commandCommand not in mappingMapping:
                                        self.printError("Can't do command "+self.command+" on device class "+self.deviceClass)
                                    else:
                                        restrictedDevicesDict = dict(filter(self.filterClass, self.devicesDict.items()))
                                        self.deviceName = self.findInDict(keywords, keywordIndex, restrictedDevicesDict, "device")
                                        if self.deviceName != "":
                                            ##self.printInfo("Device is "+self.deviceName)
                                            # Compute next index
                                            keywordIndex += len(self.deviceName.split(" "))
                                            # Is command set enabled?
                                            commandSet = self.getValue2(self.mappingValueDict, commandCommand, "set", False)
                                            ##self.printInfo(command+" set is "+str(commandSet))
                                            # Is this a set command?
                                            if commandSet:
                                                # Do we have an available keyword?
                                                if keywordIndex < len(keywords):
                                                    # Do we have a list of values associated with class?
                                                    deviceClassValues = self.getValue2(self.deviceClassesDict, self.deviceClass, "values")
                                                    if deviceClassValues:
                                                        self.valueToSet = self.findInDict(keywords, keywordIndex, deviceClassValues, "value")
                                                        if self.valueToSet != "":
                                                            # Load remapped value
                                                            self.valueToSetRemapped = self.getValue(deviceClassValues, self.valueToSet)
                                                            keywordIndex += len(self.valueToSet)
                                                            # Do we have remaining keywords?
                                                            if keywordIndex + 1 < len(keywords):
                                                                self.printError("Can't understand "+str(keywords[keywordIndex:])+" after "+self.valueToSet)
                                                    else:
                                                        # Extract all remaining keywords in value to set
                                                        self.valueToSet = ""
                                                        for ptr in range(keywordIndex, len(keywords)):
                                                            self.valueToSet += keywords[ptr]+ " "
                                                        self.valueToSet = self.valueToSet.strip()
                                                    ##self.printInfo("Value to set is "+self.valueToSet)
                                                else:
                                                    self.printError("Value to set is missing")
                                            else:
                                                # Do we have an available keyword?
                                                if keywordIndex < len(keywords):
                                                    self.printError("Can't understand "+str(keywords[keywordIndex:])+" after "+self.deviceName)
                                            if not self.errorSeen:
                                                self.deviceId = self.getValue2(self.devicesDict,self.deviceName, "index")
                                                self.deviceIdName = self.getValue2(self.devicesDict, self.deviceName, "name")
                                                self.commandValue = self.getValue2(self.mappingValueDict,commandCommand, "mappingValue")
                                                self.commandValueText = commandCommand
        return self.firstErrorMessage, self.allMessages
