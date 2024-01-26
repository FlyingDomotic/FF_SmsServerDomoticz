"""
This code analyzes a command and tries to decode a command against a given list.

It is both adapted to get French or English SMS messages to remotely manage automation system.

General command organization is:
    For French: [command] [device type] [device name] [value to set].
    For English: [command] [device name] [device type] [value to set].

For example:
    For French:  "allume la lampe de la cuisine", "ouvre le volet du salon", "règle la consigne de la clim du séjour sur 21", ...
    For English: "turn kitchen light on", "open living room shutter", "set living room air conditioning to 21", ...

Code allows to work with UTF-8 data. You may optionally restrict comparison and output to 7 bits ASCII equivalent to help processing.

More details on README.md

Author: Flying Domotic
License: GNU GPL V3
"""

import pathlib
import os
import json
from re import A, match, search
from typing_extensions import get_overloads
import unidecode

class FF_analyzeCommand:
    # Class initialization 
    def __init__(self):
        self.fileVersion = "1.1.0"                          # File version
        self.errorSeen = False;                             # Do we seen an error ?
        self.convertUtf8ToAscii7Input = True;               # Convert input to Ascii7?
        self.convertUtf8ToAscii7Output = False;             # Convert saved output to Ascii7?
        self.firstErrorMessage = ""                         # First error message seen
        self.allMessages = ""                               # All messages to be printed
        self.ignoresList = []                               # List of keywords to be ignored
        self.commandValuesDict = {}                         # Dictionary of commandValues
        self.commandsDict = {}                              # Dictionary of commands
        self.commandClassesDict = {}                        # Dictionary of commandClasses
        self.deviceClassesDict = {}                         # Dictionary of deviceClasses
        self.devicesDict = {}                               # Dictionary of devices
        self.checkFile = ""                                 # File being scanned
        self.checkPhase = ""                                # Scan phase
        self.command = ""                                   # Command
        self.commandValue = 0                               # Command value in numeric format
        self.commandValueText = ""                          # Command value in text format
        self.deviceAndClass = ""                            # Device with class name
        self.deviceName = ""                                # Device with class name (for compatibility)
        self.deviceId = 0                                   # DeviceId
        self.deviceIdName = ""                              # Name of deviceId
        self.deviceClass = ""                               # Device class
        self.valueToSetType = None                          # Value to set type ()
        self.valueToSet = None                              # Value to set
        self.valueToSetOriginal = None                      # Original value to set (for mapping)
        self.setBy = None                                   # Value to be set by 'user' or 'plugIn'
        self.french = "French"                              # Language is French
        self.english = "English"                            # Language is English
        self.language = self.english                        # Force language to English
        self.classAfterDevice = False                       # Is class after device (True for English like languages)

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
        # Print duplicates on dictionary
        def dict_print_duplicates(ordered_pairs):
            d = {}
            for k, v in ordered_pairs:
                if k in d:
                    print (F"Warning: You have duplicate definition of >{k}< in JSON declaration")
                    print (F"    {d[k]}")
                    print (F"    {v}")
                d[k] = v
            return d
        if os.path.exists(file):
            with open(file, encoding="UTF-8") as f:
                try:
                    return json.loads(f.read(), object_pairs_hook=dict_print_duplicates)
                except Exception as e:
                    self.printError(F"{e} when loading {file}")
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
            self.printError(F"Error analyzing {self.checkFile}, when {self.checkPhase}: {msg} is {valueIs}, should be "+str(valueShouldBe.keys()).replace("dict_keys(","")[:-1] if type(valueShouldBe).__name__ == "dict" else str(valueShouldBe))
            if context != None:
                self.printInfo(F"Context is {context}")
            return False
        return True

    # Compare 2 values, puts an error message and returns false if equal, true else
    def notInIgnoreList(self, msg, valueIs, context=None):
        isOk = (self.convertUserData(valueIs) not in self.ignoresList)
        if not isOk:
            self.printError(F"Error analyzing {self.checkFile} when {self.checkPhase}: {msg} should not be in ignore list")
            if context != None:
                self.printInfo(F"Context is {context}")
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
            self.printError(F"Error analyzing {self.checkFile}, when {self.checkPhase}: {msg} should not be "+str(valueShouldBe.keys()).replace("dict_keys(","")[:-1] if type(valueShouldBe).__name__ == "dict" else str(valueShouldBe))
            if context != None:
                self.printInfo(F"Context is {context}")
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
            self.printError(F"Error analyzing {self.checkFile}, when {self.checkPhase}: {msg} ({variableIs}) is {type(variableIs).__name__}, should be {typeShouldBe}")
            if context:
                self.printInfo(F"Context is {context}")
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
            self.printError(F"{keywords[startPtr:]} is not a known {text}, use "+str(dict.keys()).replace("dict_keys(","")[:-1])
            return ""
        elif len(matchingList) > 1:
            self.printError(F"{keywords[startPtr:]} is ambiguous {text}, could be {matchingList}")
            return ""
        else:
            return matchingList[0]

    # Lookup keyword in dictionary, stopping on first match
    #   List can contain values with spaces. In this case, as many keywords as word count in list element are compared
    def lookupInDict(self, keywords, startPtr, dict):
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
                # Return item
                return item
        return ""

    def loadData(self, fileName):
        # Load JSON file
        self.checkFile = pathlib.Path(fileName).name
        self.checkPhase = "checking file"
        decodeData = self.loadDictionary(fileName)

        if decodeData:
            ### Checking  decodeData (dict)
            if self.compareType("decodeData type", decodeData, "dict"):
                ### Loading classAfterDevice (True for English like languages, where device name is before device type)
                self.classAfterDevice = self.getValue2(decodeData, "settings", "classAfterDevice", False)
                ### Checking "ignores": ["of", "the", ...]
                self.checkPhase = "checking ignores"
                self.ignoresList = self.getValue(decodeData,"ignores")
                # Extract all "ignores" (list)
                if self.compareType("self.ignoresList type", self.ignoresList, "list"):
                    pass
            ### Checking "commandValues": {	"cdeOn":{"codeValue":1}, ...}
            self.checkPhase = "checking command values"
            self.commandValuesDict =  self.getValue(decodeData,"commandValues")
            # Extract all "commandValues" (dict)
            if self.compareType("commandValuesDict type", self.commandValuesDict, "dict"):
                # For each item in self.commandValuesDict
                for key in self.commandValuesDict.keys():
                    # Key should not be in ignore list
                    if self.notInIgnoreList("key", key):
                        # Check codeValue (dict)
                        codeValueItem = self.commandValuesDict[key]
                        if self.compareType("codeValueItem type", codeValueItem, "dict"):
                            # Get the "codeValue" (int)
                            codeValue = self.getValue(codeValueItem, "codeValue")
                            if self.compareType("codeValue type", codeValue, "int", codeValueItem):
                                pass

            ### Checking "commandClasses"
            self.checkPhase = "checking commandClasses"
            # Extract all "commandClasses": {"classOnOff":{"commandValue":["cdeOn","cdeOff","cdeShow"]}, ...}
            self.commandClassesDict =  self.getValue(decodeData,"commandClasses")
            if self.compareType("commandClass type", self.commandClassesDict, "dict"):
                # For each item in self.commandClassesDict
                for key in self.commandClassesDict.keys():
                    # Key should not be in ignore list
                    if self.notInIgnoreList("key", key):
                        commandClass = self.commandClassesDict[key]
                        if self.compareType("commandClass type", commandClass, "dict"):
                            # Get the commandValue
                            commandClassCommandValue = self.getValue(commandClass, "commandValue")
                            # Check commandValue keyword
                            if self.compareType("commandClass commandValue type", commandClassCommandValue, "list", commandClass):
                                # Scan all elements in list
                                for element in commandClassCommandValue:
                                    # Element should be in valueKeywords
                                    if self.compareValue("commandValue", element , self.commandValuesDict, commandClass):
                                        pass

            ### Checking "commands": {"turn":{"commandValue":"cdeSet"}, ...}
            self.checkPhase = "checking commands"
            # Extract all "commands" list
            self.commandsDict =  self.getValue(decodeData,"commands")
            if self.compareType("commandList type", self.commandsDict, "dict"):
                # For each item in self.commandsDict
                for key in self.commandsDict.keys():
                    # Key should not be in ignore list
                    if self.notInIgnoreList("key", key):
                        commandItem = self.commandsDict[key]
                        if self.compareType("commandItem type", commandItem, "dict"):
                            # Get the first "command"
                            commandCommandValue = self.getValue(commandItem, "commandValue")
                            # Check command keyword
                            if self.compareType("commandCommandValue type", commandCommandValue, "str", commandItem):
                                # Value should be in self.commandValuesDict
                                if self.compareValue("command commandValue", commandCommandValue , self.commandValuesDict, commandItem):
                                    pass

            ### Checking "deviceClasses": {"boiler":{"commandClass":"classSet","setType":"level","mapping":{"off":0,"on":100}}, ...}
            self.checkPhase = "checking device classes"
            # Extract all "deviceClasses"
            self.deviceClassesDict =  self.getValue(decodeData,"deviceClasses")
            if self.compareType("deviceClassesDict type", self.deviceClassesDict, "dict"):
                # For each item in deviceClassesDict
                for key in self.deviceClassesDict.keys():
                    # Key should not be in ignore list
                    if self.notInIgnoreList("key", key):
                        deviceClassItem = self.deviceClassesDict[key]
                        if self.compareType("deviceClassItem type", deviceClassItem, "dict"):
                            # Load "commandClass"
                            deviceCommandClass = self.getValue(deviceClassItem, "commandClass")
                            # Check deviceCommandClass keyword
                            if self.compareType("deviceCommandClass type", deviceCommandClass, "str", deviceClassItem):
                                # deviceCommandClass should be in commandClasses
                                if self.compareValue("deviceClass value", deviceCommandClass , self.commandClassesDict, deviceClassItem):
                                    # Does the deviceCommandClass have one commandValue with a set attribute?
                                    commandSet = False
                                    # Scan all commandValues for this deviceCommandClass
                                    for item in self.getValue2(self.commandClassesDict, deviceCommandClass, 'commandValue'):
                                        # Does this commandValue have the set flag set?
                                        if self.getValue2(self.commandValuesDict, item, "set", False):
                                            # Yes, set flag
                                            commandSet = True
                                            break
                                    # Check other elements giving commandSet flag
                                    if commandSet:
                                        # Command has a set flag, get mandatory setType value
                                        self.valueToSetType = self.getValue(deviceClassItem, "setType")
                                        # Check setType value as string
                                        if self.compareType("setType type", self.valueToSetType, "str", deviceClassItem):
                                            # Check for valid setType given
                                            if self.compareValue("setType", self.valueToSetType, ['level','setPoint', 'integer', 'float','string']):
                                                pass
                                        # Set min/max value depending on setType
                                        if self.valueToSetType == 'level':
                                            minValue = 0
                                            maxValue = 100
                                        else:
                                            minValue = None
                                            maxValue = None
                                        # Set authorized data type(s) depending on setType
                                        if self.valueToSetType == 'level' or self.valueToSetType == 'integer':
                                            allowedDataTypes = 'int'
                                        elif self.valueToSetType == 'float' or self.valueToSetType == 'setPoint':
                                            allowedDataTypes = ['int', 'float']
                                        else:
                                            allowedDataTypes = 'str'
                                        # Scan all items in deviceClass item
                                        for item in deviceClassItem.keys():
                                                # Get item value
                                                itemValue = deviceClassItem[item]
                                                if item == "mapping":
                                                    deviceClassMap = self.getValue(deviceClassItem, "mapping")
                                                    # This should be a list of mapping value (dict)
                                                    if self.compareType("deviceClassMap type", deviceClassMap, "dict", deviceClassItem):
                                                        ## Check each value type against authorized ones
                                                        for mappingKey in itemValue.keys():
                                                            if self.compareType("mapping value type", itemValue[mappingKey], allowedDataTypes, deviceClassItem):
                                                                pass
                                                elif item == "minValue":
                                                    if self.compareType("minValue type", itemValue, allowedDataTypes, deviceClassItem):
                                                        minValue = itemValue
                                                elif item == "maxValue":
                                                    if self.compareType("minValue type", itemValue, allowedDataTypes, deviceClassItem):
                                                        maxValue = itemValue
                                                elif item == "list":
                                                    # Check type as list
                                                    if self.compareType("list type", itemValue, "list", deviceClassItem):
                                                        # Check each item in list
                                                        for item in itemValue:
                                                            if self.compareType("list value type", item, allowedDataTypes, deviceClassItem):
                                                                pass
                                                elif item == "setBy":
                                                    if self.compareValue("setBy", itemValue, ['plugIn', 'user']):
                                                        pass
                                                elif item != "commandClass" and item != "setType":
                                                    # And unknown item has been specified
                                                    self.printError(F"Can't understand {item} in {deviceClassItem} for {key}")
                                        # Check for min/max values
                                        if minValue != None and maxValue != None:
                                            # Min should be <= to max
                                            if minValue > minValue:
                                                self.printError(F"minValue ({minValue}) should be less or equal to maxValue ({maxValue})")
                                    else:
                                        # Scan all items in deviceClass item
                                        for item in deviceClassItem.keys():
                                            if item != "commandClass":
                                                self.printError(F"Can't understand {item} in {deviceClassItem} for {key}")

            ### Checking "devices": {"south bedroom ac":{"index":19,"name":"South Bedroom A/C - Power"}, ...}
            self.checkPhase = "checking devices"
            # Extract all "devices"
            self.devicesDict =  self.getValue(decodeData,"devices")
            if self.compareType("self.devicesDict type", self.devicesDict, "dict"):
                # For each item in self.devicesDict
                for key in self.devicesDict.keys():
                    deviceItem = self.devicesDict[key]
                    if self.compareType("deviceItem type", deviceItem, "dict"):
                        # Extract deviceClass item (first or last item)
                        if self.classAfterDevice:
                            self.deviceClass = key.split(" ")[len(key.split(" "))-1]
                        else:
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
                        # Extract each part of device name
                        deviceAndClass = key.split(" ")
                        for element in deviceAndClass:
                            # element should not be in ignore list
                            if self.notInIgnoreList("part of key", element, F"Key is : {key}"):
                                pass
        else:
            self.printError(F"Can't load {fileName}")
        # Set final check status (first value is short error message, second one all detected errors)
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
        self.deviceAndClass = ""                            # Device with class name
        self.deviceName = ""                                # Device with class name (for compatibility)
        self.deviceId = 0                                   # DeviceId
        self.deviceIdName = ""                              # Name of deviceId
        self.deviceClass = ""                               # Device class to select in filterClass
        self.valueToSet = None                              # Value to set
        self.valueToSetType = None                          # Value to set type
        self.valueToSetOriginal = None                      # Original Value to set (for mapping)
        self.setBy = None                                   # Value to be set by 'user' or 'plugIn'

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
            ##self.printInfo(F"Command is {self.command}")
            # move index into keywords
            keywordIndex += len(self.command.split(" "))
            # Isolate deviceClass in second keyword
            #if len(keywords) < keywordIndex + 1:
            #    self.printError("No device class given!")
            #else:
            # Does the full device name/device class exists?
            self.deviceAndClass = self.findInDict(keywords, keywordIndex, self.devicesDict, "device")
            self.deviceClass = ""
            if self.deviceAndClass != "":
                if self.classAfterDevice:
                    localIndex = keywordIndex + len(self.deviceAndClass.split(" ")) - 1
                    self.deviceClass = self.findInDict(keywords, localIndex, self.deviceClassesDict, "commandClass")
                else:
                    self.deviceClass = self.findInDict(keywords, keywordIndex, self.deviceClassesDict, "commandClass")
            if self.deviceClass != "":
                keywordIndex += len(self.deviceAndClass.split(" "))
                ##printInfp(F"Device class is {self.deviceClass}")
                # Get commandClass class
                deviceCommandClass = self.getValue2(self.deviceClassesDict, self.deviceClass, "commandClass")
                if not deviceCommandClass:
                    self.printError(F"Can't find {self.deviceClass} command class...")
                else:
                    ##self.printInfo(F"{self.deviceClass} device class is {deviceCommandClass}")
                    # Get deviceClass commandValue
                    commandClassCommandValue = self.getValue2(self.commandClassesDict, deviceCommandClass, "commandValue")
                    if not commandClassCommandValue:
                        self.printError(F"Can't find {deviceCommandClass} device commandClass commandValue...")
                    else:
                        ##self.printInfo(F"{deviceCommandClass} commandValue is {commandClassCommandValue}")
                        # Get command commandValue
                        commandCommandValue = self.getValue2(self.commandsDict, self.command, "commandValue")
                        if not commandCommandValue:
                            self.printError(F"Can't find {self.command} command commandValue...")
                        else:
                            ##self.printInfo(F"{self.command} command is {commandCommandValue}")
                            if commandCommandValue not in commandClassCommandValue:
                                self.printError(F"Can't do command {self.command} on device class {self.deviceClass}")
                            else:
                                if self.deviceAndClass != "":
                                    ##self.printInfo(F"Device is {self.deviceAndClass}"")
                                    # Is command set enabled?
                                    commandSet = self.getValue2(self.commandValuesDict, commandCommandValue, "set", False)
                                    ##self.printInfo(F"{command} set is {commandSet}")
                                    # Is this a set command?
                                    if commandSet:
                                        # Extract all remaining keywords in value to set
                                        self.valueToSet = ""
                                        for ptr in range(keywordIndex, len(keywords)):
                                            self.valueToSet += keywords[ptr]+ " "
                                        self.valueToSet = self.valueToSet.strip()
                                        ##self.printInfo(F"Value to set is {self.valueToSet}")
                                        # Do we have a value to set?
                                        if self.valueToSet != "":
                                            # Extract setType value
                                            self.valueToSetType = self.getValue2(self.deviceClassesDict, self.deviceClass, "setType")
                                            # Do we have mapping associated with class?
                                            deviceClassMap = self.getValue2(self.deviceClassesDict, self.deviceClass, "mapping")
                                            if deviceClassMap:
                                                # Substitute first val  ue to set to mapped value
                                                self.valueToSetOriginal = self.findInDict(keywords, keywordIndex, deviceClassMap, "mapping")
                                                if self.valueToSetOriginal != "":
                                                    # Load remapped value
                                                    self.valueToSet = self.getValue(deviceClassMap, self.valueToSetOriginal)
                                                    keywordIndex += len(self.valueToSetOriginal)
                                                    # Do we have remaining keywords?
                                                    if keywordIndex + 1 < len(keywords):
                                                        self.printError(F"Can't understand {keywords[keywordIndex:]} after {self.valueToSet}")
                                            # Do we have a list associated with class?
                                            deviceClasslist = self.getValue2(self.deviceClassesDict, self.deviceClass, "list")
                                            if deviceClasslist and self.compareValue("value", self.valueToSet, deviceClasslist, givenCommand):
                                                pass
                                            # Do we have a minValue or maxValue?
                                            deviceClassMinValue = self.getValue2(self.deviceClassesDict, self.deviceClass, "minValue", None)
                                            deviceClassMaxValue = self.getValue2(self.deviceClassesDict, self.deviceClass, "maxValue")
                                            # Set authorized data type(s) depending on setType
                                            if self.valueToSetType == 'level':
                                                try:
                                                    dummy = int(self.valueToSet)
                                                except ValueError:
                                                    self.printError(F"({self.valueToSet}) is not a valid number")
                                                    return
                                                if deviceClassMinValue == None:
                                                    deviceClassMinValue = 0
                                                if deviceClassMaxValue == None:
                                                    deviceClassMaxValue = 100
                                                if dummy < int(deviceClassMinValue):
                                                    self.printError(F"Given value ({dummy}) should not be less than {deviceClassMinValue}")
                                                    return
                                                if dummy > int(deviceClassMaxValue):
                                                    self.printError(F"Given value ({dummy}) should not be greater than {deviceClassMaxValue}")
                                                    return
                                            elif self.valueToSetType == 'integer':
                                                try:
                                                    dummy = int(self.valueToSet)
                                                except ValueError:
                                                    self.printError(F"({self.valueToSet}) is not a valid number")
                                                    return
                                                if deviceClassMinValue != None and dummy < int(deviceClassMinValue):
                                                    self.printError(F"Given value ({dummy}) should not be less than {deviceClassMinValue}")
                                                    return
                                                if deviceClassMaxValue != None and dummy > int(deviceClassMaxValue):
                                                    self.printError(F"Given value ({dummy}) should not be greater than {deviceClassMaxValue}")
                                                    return
                                            elif self.valueToSetType == 'float' or self.valueToSetType == 'setPoint':
                                                try:
                                                    dummy = float(self.valueToSet)
                                                except ValueError:
                                                    self.printError(F"({self.valueToSet}) is not a valid floating point")
                                                    return
                                                if deviceClassMinValue != None and dummy < float(deviceClassMinValue):
                                                    self.printError(F"Given value ({dummy}) should not be less than {deviceClassMinValue}")
                                                    return
                                                if deviceClassMaxValue != None and dummy > float(deviceClassMaxValue):
                                                    self.printError(F"Given value ({dummy}) should not be greater than {deviceClassMaxValue}")
                                                    return
                                            else:
                                                if deviceClassMinValue != None and self.valueToSet < deviceClassMinValue:
                                                    self.printError(F"Given value ({self.valueToSet}) should not be less than {deviceClassMinValue}")
                                                    return
                                                if deviceClassMaxValue != None and self.valueToSet > deviceClassMaxValue:
                                                    self.printError(F"Given value ({self.valueToSet}) should not be greater than {deviceClassMaxValue}")
                                                    return
                                            # Load setBy
                                            self.setBy = self.getValue2(self.deviceClassesDict, self.deviceClass, "setBy", "plugIn")
                                        else:
                                            self.printError("Value to set is missing")
                                    else:
                                        # Do we have an available keyword?
                                        if keywordIndex < len(keywords):
                                            self.printError(F"Can't understand {keywords[keywordIndex:]} after {self.deviceAndClass}")
                                    if not self.errorSeen:
                                        self.deviceName = self.deviceAndClass
                                        self.deviceId = self.getValue2(self.devicesDict,self.deviceAndClass, "index")
                                        self.deviceIdName = self.getValue2(self.devicesDict, self.deviceAndClass, "name")
                                        self.commandValue = self.getValue2(self.commandValuesDict,commandCommandValue, "codeValue")
                                        self.commandValueText = commandCommandValue
        return self.firstErrorMessage, self.allMessages
