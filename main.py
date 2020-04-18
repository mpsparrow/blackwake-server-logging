import datetime
import threading, time
import mysql.connector as mysql
from mysql.connector import errorcode
import json
import requests

checkTime = 30 # x seconds between updates
steamkey = "" # regular Steam API key
ipkey = "" # ipgeolocation.io

# mySQL connection
username = ""
password = ""
host = "localhost"
database = ""

# always running thread
def thread():
    checkEvent = threading.Event()
    while not checkEvent.wait(checkTime):
        update()

# database updater
def update():
    q = """UPDATE `servers` SET online = false, players = 0"""
    queryDB(q)
    # print("offline")

    servers = getServers()
    now = datetime.datetime.utcnow()
    formatted_date = now.strftime('%Y-%m-%d %H:%M:%S')

    for server in servers:
        q = f"""SELECT COUNT(1) FROM `servers` WHERE steamid = {server['steamid']}"""
        existsVal = returnDB(q)[0][0]

        if existsVal == 1:
            commitUpdateDB(server['steamid'], server['name'], server['name'].split(' ', 1)[1], server['addr'], True, server['players'], server['max_players'], formatted_date)
            # print("update")
        else:
            region = getRegion(server['addr'].split(':', 1)[0])
            q = (server['steamid'], server['name'], server['name'].split(' ', 1)[1])
            q += (server['addr'], True, server['players'], server['max_players'])
            q += (region[0], region[1], formatted_date, formatted_date, formatted_date)
            commitNewDB(q)
            # print("new")

    q = f"""UPDATE `servers` SET last_offline = '{formatted_date}' WHERE online = false"""
    queryDB(q)
    # print("offline update")
        
# Blackwake server API
def getServers():
    url = f"https://api.steampowered.com/IGameServersService/GetServerList/v1/?key={steamkey}&format=json&filter=\\appid\\420290"
    r = requests.get(url)
    data = r.json()
    return data['response']['servers']

# IP location API
def getRegion(ip: str):
    url = f"https://api.ipgeolocation.io/ipgeo?apiKey={ipkey}&ip={ip}"
    r = requests.get(url)
    data = r.json()
    return (data['continent_name'], data['country_name'])

# query commit to db
def commitNewDB(values):
    try:
        cnx = mysql.connect(user=username, password=password, host=host, database=database)
    except mysql.Error as err:
        print(err)
    else:
        cursor = cnx.cursor()
        query = f"""INSERT INTO `servers` (
            steamid, name, clean_name, ip, online, players, max_players,
            continent, country, first_online, last_offline, last_online
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        cursor.execute(query, values)
        cnx.commit()
        cnx.close()

# query update to db
def commitUpdateDB(steamid, name, clean_name, ip, online, players, max_players, last_online):
    try:
        cnx = mysql.connect(user=username, password=password, host=host, database=database)
    except mysql.Error as err:
        print(err)
    else:
        cursor = cnx.cursor()
        query = f"""INSERT INTO `servers` (
            steamid, name, clean_name, ip, online, players, max_players, last_online
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) 
            ON DUPLICATE KEY UPDATE 
            steamid = VALUES(steamid), name = VALUES(name), clean_name = VALUES(clean_name),
            ip = VALUES(ip), online = VALUES(online), players = VALUES(players),
            max_players = VALUES(max_players), last_online = VALUES(last_online)"""
        values = (steamid, name, clean_name, ip, online, players, max_players, last_online)
        cursor.execute(query, values)
        cnx.commit()
        cnx.close()

# query to db
def queryDB(query):
    try:
        cnx = mysql.connect(user=username, password=password, host=host, database=database)
    except mysql.Error as err:
        print(err)
    else:
        cursor = cnx.cursor()
        cursor.execute(query)
        cnx.commit()
        cnx.close()

# query to db with return
def returnDB(query):
    try:
        cnx = mysql.connect(user=username, password=password, host=host, database=database)
    except mysql.Error as err:
        print(err)
    else:
        cursor = cnx.cursor()
        cursor.execute(query)
        returnData = cursor.fetchall()
        cnx.commit()
        cnx.close()
        return returnData

thread() # start thread