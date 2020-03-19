import datetime
import socket
import select
import sys
import os
import time
import ntplib
from _thread import *

#Variables
list_of_clients = []
list_of_players = []
ips = []
MyIp = ""
Port = 6030

#Funciones
def setDate(fechaHora):
    date = datetime.datetime.strptime(fechaHora, '%Y-%m-%d %H:%M:%S')
    os.system("sudo date -s \"" + date.strftime("%d %b %Y %H:%M:%S") + "\"")
    print("Datos establecidos...")

def updateDate():
    dateI = datetime.datetime.now()
    print("Fecha & Hora Inicial> " + str(dateI))
    dateServer = timeFromServer()
    print("Fecha & Hora Servidor> " + str(dateServer))
    dateS = datetime.datetime.strptime(dateServer, '%Y-%m-%d %H:%M:%S')
    dateS = dateS + (datetime.datetime.now()-dateI)/2
    print("Fecha & Hora Ajustada> " + str(dateS))
    os.system("sudo date -s \"" + dateS.strftime("%d %b %Y %H:%M:%S") + "\"")
    print("Datos establecidos...")

def timeFromServer():
    file = open('timeServers.txt','r')
    cadena = file.read()
    file.close()
    timeServers = cadena.strip().split(",")
    for timeServer in timeServers:
        try:
            client = ntplib.NTPClient()
            return time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(client.request(str(timeServer)).tx_time))
        except:
            print('No ha sido posible descargar la fecha desde ' + timeServer)

def tryConnection(ip):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((ip, Port))
        s.close()
        return True
    except:
        return False

def checkPorts():
    isRunning = False
    for ip in ips:
        if not (os.system('nmap '+ip+' -p '+str(Port)+'| grep open')):
            isRunning = True
    return isRunning

def startClient():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ipServer = ""
    for ip in ips:
        if (tryConnection(ip)):
            ipServer = ip
    client.connect((ipServer, Port))
    while True:
        sockets_list = [sys.stdin, client]
        read_sockets,write_socket, error_socket = select.select(sockets_list,[],[])
        for socks in read_sockets:
            if socks == client:
                message = socks.recv(2048).decode()
                print (message)
                if message.split(",")[0] == "date":
                    setDate(str(message.split(",")[1].strip()))
            else:
                message = sys.stdin.readline()
                print(message)
                client.send(message.encode())
                sys.stdout.flush()
    client.close()

def clientthread(conn, addr):
    try:
        while True:
            try:
                message = conn.recv(2048).strip().decode()
                if message:
                    if message == "update":
                        broadcast(("date," + str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))), conn)
                        print("Fecha & Hora enviada...")
                    else:
                        print("<" + addr[0] + "> " + message)
                        message_to_send = "<" + addr[0] + "> " + message
                        broadcast(message_to_send, conn)
                else:
                    remove(conn)
            except:
                continue
    except:
        print("")

def broadcast(message, connection):
    for clients in list_of_clients:
        try:
            clients.send(message.encode())
        except:
            clients.close()
            remove(clients)

def remove(connection):
    if connection in list_of_clients:
        list_of_clients.remove(connection)

# Asociar el socket con la IP y el puerto definidos anteriormente
if __name__ == "__main__":
    file = open ('ips.txt','r')
    cadena = file.read()
    file.close()
    ips = cadena.strip().split(", ")
    MyIp = str(os.system('hostname -I'))
    if checkPorts():
        print("Conectando como cliente...")
        startClient()
    else:
        try:
            updateDate()
            print("Servidor levantado...")
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((MyIp, Port))
            server.listen(100)
            while True:
                conn, addr = server.accept()
                list_of_clients.append(conn)
                print ("Conectado> " + addr[0])
                start_new_thread(clientthread,(conn,addr))
            conn.close()
            server.close()
        except:
            print("Cerrando...")
