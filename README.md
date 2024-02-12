# FF_SmsServer interface to Domoticz/Interface FF_SmsServer pour Domoticz
(English and French version in same file/Versions anglaises et françaises dans le même fichier)

Allow users to send SMS containing commands to be executer on Domoticz.

Execute des commandes envoyées par SMS à Domoticz

## What's for?/A quoi ça sert ?

This python code reads all SMS received by a (FF) SMS server. If first command's word is equal to a given prefix, rest of command is analyzed as a valid command. Errors during analysis are returned as SMS to command's sender. If no errors, command is sent to Domoticz and result sent back to sender, still by SMS.

Ce code python lit les SMS reçus par un serveur (FF) SMS. Si le premier mot de la commande est égal à un préfixe donné, le reste de la commande est analysée. Les erreurs sont renvoyées à l'expéditeur par SMS. Si la commande est ccorecte, elle est envoyée à Domoticz, et le résultat est retourné à l'expéditeur, toujours par SMS.

## Note
There are 2 versions of this code:
- https://github.com/FlyingDomotic/FF_SmsServerDomoticz.git (this code), which is a Linux service implementation
- https://github.com/FlyingDomotic/domoticz-ff_smsserver-plugin.git, which runs as Domoticz's plug-in

You may choose version best suited for you.

Il y a 2 versions de ce code :
- https://github.com/FlyingDomotic/FF_SmsServerDomoticz.git (ce code), implémenté sous forme de service Linux
- https://github.com/FlyingDomotic/domoticz-ff_smsserver-plugin.git, qui tourne en tant que plugin Domoticz

Choisissez la version qui vous va le mieux.

## Prerequisites/Prérequis

You must have a (FF) SMS server (https://github.com/FlyingDomotic/FF_SmsServer.git) properly configured and running somewhere on your network.

Vous devez avoir un serveur (FF) SMS (https://github.com/FlyingDomotic/FF_SmsServer.git) correctement configuré et tournant quelque part dans votre réseau.

## Installation

Clone repository somewhere on your disk.
```
cd [where_you_want_to_install_it]
git clone https://github.com/FlyingDomotic/FF_SmsServerDomoticz.git FF_SmsServerDomoticz
```

Clonez le code quelque part sur votre disque.
```
cd [là_ou_vous_voulez_l'installer]
git clone https://github.com/FlyingDomotic/FF_SmsServerDomoticz.git FF_SmsServerDomoticz
```

## Update/Mise à jour

Go to code folder and pull new version:
```
cd [where_you_installed_FF_SmsServerDomoticz]
git pull
```

Note: if you did any changes to files and `git pull` command doesn't work for you anymore, you could stash all local changes using:
```
git stash
```
or
```
git checkout [modified file]
```

Allez dans le répertoire où vous avez installé le code et mettez-le à jour :
```
cd [là_où_vous_avez_installé_FF_SmsServerDomoticz]
git pull
```

Note: si vous avez modifié des fichiers et que la commande `git pull` ne fonctionne pas, vous pouvez annuler les changements par :
```
git stash
```
ou
```
git checkout [fichier modifié]
```

## Principle/Principe

General command organization is: [prefix] [command] [device name] [device type] [value to set].

For example: "domoticz turn kitchen light on", "domoticz open living room shutter", "domoticz set living room air conditioning to 21", ...

Code allows to work with UTF-8 data. You may optionally restrict comparison and/or output to 7 bits ASCII equivalent to help processing, allowing to remove accentuated characters (even if useful for 

La structure de la commande est : [préfixe] [command] [device type] [device name] [value to set].

Par exemple : `domotique allume la lampe de la cuisine`, `domotique ouvre le volet du salon`, `domotique règle la consigne de la clim du séjour sur 21`, ...

Le code utilise du texte codé en UTF-8. Vous pouvez restreindre la comparaison et/ou l'affichage en mode 7 bits ASCII, ce qui éliminera les caractères accentués.

## Files/Fichiers
- smsTables.json: configuration file describing devices, classes and commands.
- FF_analyzeCommand.py: contains common code used to parse smsTables.json, and parse SMS commands against them.
- checkJsonFiles.py: check syntax and relationships of smsTables.json and allows you to test legality of commands (without executing them).
- makeDoc.py: generate a list of commands supported by your configuration.
- domoticzSms.py: reads SMS message, check for prefix, parse command and execute it if legal.
- domoticsSsm.service: service configuration file to run domoticzSms.py as service.

- smsTables.json: fichier de configuration décrivant les dispositifs, classes et commandes.
- FF_analyzeCommand.py: contient le code utilisé pour lire smsTables.json, et vérifier/décoder les commandes SMS.
- checkJsonFiles.py: vérifie la syntaxe et les relations du fichier smsTables.json. Permet aussi de vérifier le format des commandes (sans les exécuter).
- makeDoc.py: génére une liste des commandes supportées par votre configuration.
- domoticzSms.py: lit les SMS, vérifie le préfixe, analyse la commande et l'exécute si elle est correcte.
- domoticsSsm.service: fichier de configuration pour lancer domoticzSms.py en tant que service.

## smsTables.json content/Contenu du fichier smsTables.json

This json configuration file contains the following parts (in any order):

- "settings": contains settings parameters. `"classAfterDevice": true` indicates that class is given after device, as with English language.
- "ignores": contains keywords to be ignored (like `the`, `of`, `to`...). All these keywords will be removed from message before parsing.
- "commandValues": contains binary values of the different commands. Typical implementation could be like:
	- "cdeOff":{"codeValue":2}, to turn a device off,
	- "cdeSet":{"codeValue":8,"set":true}, to set a device to any numerical or string value,
	- "cdeShow":{"codeValue":4}, to show current value of a device.
- "commandClasses": define classes and maps them to `commandValues`. Typical implementation could be like:
	- "classOnOff":{"commandValue":["cdeOn","cdeOff","cdeShow"]} for any on/off device,
	- "classSet":{"commandValue":["cdeSet","cdeShow"]}  for any device with value to be set,
	- "classShow":{"commandValue":["cdeShow"]}  for all devices you won't change value.

- "commands": contains the commands to implement. Same action can be supported by multiple values (i.e. `light`, `open` to set a device on). `Commands` maps to `mappingValues`.
- "deviceClasses": associate device classes with classes.
- "devices": define supported Domoticz devices (not necessarily with their real names). As a device could have multiple sensors, they're postfixed by a device class. It also specify Domoticz idx. It could contain Domoticz device name (useful to compare given device name with Domoticz one).

Here's an example of smsTables.json (English version):
```
{
	"settings": {
		"classAfterDevice": true
	},
	"ignores": [
		"of",
		"the",
		"=",
		"to"
	],
	"commandValues": {
		"cdeOn":{"codeValue":1},
		"cdeOff":{"codeValue":2},
		"cdeShow":{"codeValue":4},
		"cdeSet":{"codeValue":8,"set":true}
	},
	"commandClasses": {
		"classOnOff":{"commandValue":["cdeOn","cdeOff","cdeShow"]},
		"classSet":{"commandValue":["cdeSet","cdeShow"]},
		"classShow":{"commandValue":["cdeShow"]}
	},
	"commands": {
		"turn":{"commandValue":"cdeSet"},
		"arm":{"commandValue":"cdeOn"},
		"open":{"commandValue":"cdeOn"},
		"disarm":{"commandValue":"cdeOff"},
		"close":{"commandValue":"cdeOff"},
		"state":{"commandValue":"cdeShow"},
		"display":{"commandValue":"cdeShow"},
		"set":{"commandValue":"cdeSet"},
		"define":{"commandValue":"cdeSet"}
	},
	"deviceClasses": {
		"heating":{"commandClass":"classSet","setType":"level","mapping":{"warm":10,"cold":20,"dehumidification":30}},
		"ac":{"commandClass":"classOnOff"},
		"reference":{"commandClass":"classSet","setType":"setPoint","minValue":6,"maxValue":25},
		"contact":{"commandClass":"classShow"},
		"light":{"commandClass":"classSet","setType":"level","mapping":{"off":0,"on":100}},
		"radiator":{"commandClass":"classSet","setType":"level","mapping":{"off":0,"comfort":10,"eco":40,"nofrost":50}},
		"temperature":{"commandClass":"classShow"}
	},
	"devices": {
		"south bedroom ac":{"index":12,"name":"South bedroom air conditioning - Power"},
		"south bedroom heating":{"index":23,"name":"South bedroom air conditioning - Mode"},
		"south bedroom reference":{"index":34,"name":"South bedroom air conditioning - SetPoint"},
		"kitchen light":{"index":45,"name":"Kitchen"},
		"living room temperature":{"index":56,"name":"Living temperature"},
		"north bathroom radiator":{"index":67,"name":"North bedroom radiator mode"},
		"main door contact":{"index":78,"name":"Main door contact"}
	}
}
```

Le fichier de configuration json contient les éléments suivants (dans n'importe quel ordre) :

- "settings": contient les paramètres de configuration. `"classAfterDevice": false` indique que la classe est données avant le nom du dispositif (comme en français),
- "ignores": contient les mots clef à ignorer (comme `le`, `la`, `de`...). Tous ces mots clef seront supprimés du message avant traitement,
- "commandValues": contient les valeurs binaires des différentes commandes. Par exemple :
	- "cdeOff":{"codeValue":2}, pour éteindre un dispositif,
	- "cdeSet":{"codeValue":8,"set":true}, pour définir une valeur numérique ou chaine sur un dispositif,
	- "cdeShow":{"codeValue":4}, pour afficher la valeur associée à un dispositif,
- "commandClasses": definit les classes et les associe aux `commandValues`. Par exemple :
	- "classOnOff":{"commandValue":["cdeOn","cdeOff","cdeShow"]} pour des dispositifs on/off,
	- "classSet":{"commandValue":["cdeSet","cdeShow"]} pour des dispositifs dont on souhaite régler la valeur,
	- "classShow":{"commandValue":["cdeShow"]} pour les dispositifs dont on ne veut pas changer la valeur.

- "commands": contient les commandes à implementer. La même action peut être définie de plusieurs façons (par exemple `allume`, `ouvre` pour mettre un dispositif sur on). `Commands` pointe vers `mappingValues`.
- "deviceClasses": associe les classes de dispositifs avec les classes,
- "devices": definit les dispositifs Domoticz utilisés (pas forcement sous leur nom original). Comme un dispositif peut avoir plusieurs capteurs, ils sont préfixés par la classe du dispositif. Contient également l'idx Domoticz. Il peut également contenir le nom oroginal Domoticz, pour aider aux recoupements.

Voici un exemple de fichier smsTables.json (version française) :

```
{
	"settings": {
		"smsServerReceiveTopic": "smsServer/received",
		"smsServerSendTopic": "smsServer/toSend",
		"smsServerLwtTopic": "smsServer/LWT",
		"smsServerPrefix": "test",
		"domoticzInTopic": "domoticz/in",
		"domoticzOutTopic": "domoticz/out",
		"domoticzAddress": "127.0.0.1",
		"domoticzPort": "8080",
		"classAfterDevice": false
	},
	"ignores": [
		"de",
		"du",
		"des",
		"d'",
		"le",
		"la",
		"les",
		"l'",
		"à",
		"a",
		"=",
		"sur"
	],
	"commandValues": {
		"cdeOn":{"codeValue":1},
		"cdeOff":{"codeValue":2},
		"cdeShow":{"codeValue":4},
		"cdeSet":{"codeValue":8,"set":true}
	},
	"commandClasses": {
		"classOnOff":{"commandValue":["cdeOn","cdeOff","cdeShow"]},
		"classSet":{"commandValue":["cdeSet","cdeShow"]},
		"classShow":{"commandValue":["cdeShow"]}
	},
	"commands": {
		"allume":{"commandValue":"cdeOn"},
		"arme":{"commandValue":"cdeOn"},
		"ouvre":{"commandValue":"cdeOn"},
		"éteins":{"commandValue":"cdeOff"},
		"désarme":{"commandValue":"cdeOff"},
		"ferme":{"commandValue":"cdeOff"},
		"état":{"commandValue":"cdeShow"},
		"affiche":{"commandValue":"cdeShow"},
		"règle":{"commandValue":"cdeSet"},
		"définis":{"commandValue":"cdeSet"}
	},
	"deviceClasses": {
		"chaleur":{"commandClass":"classSet","setType":"level","mapping":{"chaud":10,"froid":20,"déshumidification":30}},
		"clim":{"commandClass":"classOnOff"},
		"consigne":{"commandClass":"classSet","setType":"setPoint","minValue":6,"maxValue":25},
		"contact":{"commandClass":"classShow"},
		"lampe":{"commandClass":"classOnOff"},
		"radiateur":{"commandClass":"classSet","setType":"level","mapping":{"off":0,"confort":10,"eco":40,"horsgel":50}},
		"température":{"commandClass":"classShow"}
	},
	"devices": {
		"clim chambre sud":{"index":12,"name":"Clim chambre Sud - Power"},
		"chaleur chambre sud":{"index":23,"name":"Clim chambre Sud - Mode"},
		"consigne chambre sud":{"index":34,"name":"Clim chambre Sud - Thermostat"},
		"lampe cuisine":{"index":45,"name":"Cuisine"},
		"température sejour":{"index":56,"name":"Température air séjour"},
		"radiateur SdB nord":{"index":67,"name":"Mode radiateur SdB nord"},
		"contact porte entrée":{"index":78,"name":"Contact porte entrée"}
	}
}
```

## How to get list of commands supported by your implementation?/Comment obtenir une liste des commandes ?

Just run `makeDoc.py` and have a look at `config.txt` it'll generate. Here's an example of the configuration listed in the previous paragraph. First column is Domoticz device name while second one list all commands available for the device:
```
South bedroom air conditioning - Power	arm/open/disarm/close/state/display south bedroom ac
South bedroom air conditioning - Mode	turn/state/display/set/define south bedroom heating [warm/cold/dehumidification]
South bedroom air conditioning - SetPoint	turn/state/display/set/define south bedroom reference
Kitchen	turn/state/display/set/define kitchen light [off/on]
Living temperature	state/display living room temperature
North bedroom radiator mode	turn/state/display/set/define north bathroom radiator [off/comfort/eco/nofrost]
Main door contact	state/display main door contact
```
Lancer simplement `makeDoc.py` pour générer un fichier `config.txt`. Voici un exemple à partir de la configuration donnée dans le paragraphe précédent. La première colonne indique le nom du dispositif Domoticz, la seconde la liste de toutes les commandes disponibles pour le dispositif :

```
Clim chambre Sud - Power	allume/arme/ouvre/éteins/désarme/ferme/état/affiche clim chambre sud
Clim chambre Sud - Mode	état/affiche/règle/définis chaleur chambre sud [chaud/froid/déshumidification]
Clim chambre Sud - Thermostat	état/affiche/règle/définis consigne chambre sud
Cuisine	allume/arme/ouvre/éteins/désarme/ferme/état/affiche lampe cuisine
Température air séjour	état/affiche température sejour
Mode radiateur SdB nord	état/affiche/règle/définis radiateur SdB nord [off/confort/eco/horsgel]
Contact porte entrée	état/affiche contact porte entrée
```

## How to install domoticzSms.service?/Comment installer le service domoticzSms?
- cd [where you installed FF_SmsServerDomoticz]
- chmod +x *.py
- nano domoticzSms.service
	- locate `User=` line and replace `pi` by user you want to run domoticzSms.service (if not `pi`)
	- locate `ExecStart=` line and replace `/home/pi` by location where you installed domoticzSms.service
	- save modified file
- sudo mv domoticzSms.service /lib/systemd/system/
- sudo chmod 644 /lib/systemd/system/domoticzSms.service
- sudo systemctl enable domoticzSms.service
- sudo systemctl start domoticzSms.service

- cd [là où vous avez installé FF_SmsServerDomoticz]
- chmod +x *.py
- nano domoticzSms.service
	- trouvez la ligne `User=` line et replacer `pi` par l'utilisateur qui doit faire tourner le service domoticzSms.service (si différent),
	- trouvez la ligne `ExecStart=` et remplacer `/home/pi` par le répertoire où vous avez installé domoticzSms.service (si différent),
	- sauvegarder le fichier modifié.
- sudo mv domoticzSms.service /lib/systemd/system/
- sudo chmod 644 /lib/systemd/system/domoticzSms.service
- sudo systemctl enable domoticzSms.service
- sudo systemctl start domoticzSms.service
