from base64 import encode
from collections import OrderedDict
import sys
import os
import socket
import hashlib
import threading
import time
import random
import socket
import select

n =5
serverIP = '127.0.0.51'
localPort   = 20001
bufferSize  = 1200
lock = threading.Lock()
noOfThreads = n
totalChunks =0
clientsFinished=0
sendCounter=0
cacheSize = 5

clientIP   = ["127.0.0.{}".format(i+69)  for i in range(n)]
clientAddressPortTCP   = [i+20001+n  for i in range(n)]
clientAddressPortUDP   = [i+20001  for i in range(n)]
serverAddressPortTCP   = [i+20001+n  for i in range(n)]
serverAddressPortUDP   = [i+20001  for i in range(n)]

sendChunkToClientOn =[1 for i in range(n)]

#Cache
class LRUCache:
 
    def __init__(self, capacity: int):
        self.cache = OrderedDict()
        self.capacity = capacity
 
    def get(self, key: int) -> int:
        if key not in self.cache:
            return 0
        else:
            self.cache.move_to_end(key)
            return self.cache[key]

    def put(self, key: int, value: str) -> None:
        self.cache[key] = value
        self.cache.move_to_end(key)
        if len(self.cache) > self.capacity:
            self.cache.popitem(last = False)

data_dict =LRUCache(cacheSize)
#threads
recvReqThreads=[]
recvChunkThreads=[]

def cts(n:int):
    s= str(n)
    leng = len(s)
    for i in range(0,8-leng):
        s= "0"+s
    return s

##Initialization
##sending chunks to the client over TCP
file = open("./A2_small_file.txt", 'r')
bfile = file.read(1024)

UDPDistributer = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
UDPDistributer.bind((serverIP,10001))
while(bfile):
    clientNo = totalChunks%n
    bytesToSend   = (cts(totalChunks)+ bfile).encode()
    UDPDistributer.sendto(bytesToSend,(clientIP[clientNo],clientAddressPortUDP[clientNo]))
    ack=UDPDistributer.recvfrom(bufferSize)
    bfile = file.read(1024)
    totalChunks+=1

for i in range(n):
    bytesToSend   = str.encode("stop it")
    UDPDistributer.sendto(bytesToSend,(clientIP[i],clientAddressPortUDP[i]))


print("total Chunks sent by the server are ",totalChunks,"\n")
PendingReq =[[0 for i in range(n)] for j in range(totalChunks)]
#recv chunk from client
def recvChunksFromClient(clientNo):
    TCPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
    TCPServerSocket.bind((serverIP, serverAddressPortTCP[clientNo]))
    TCPServerSocket.listen(1)
    while True:
        connectionSocket, addr = TCPServerSocket.accept()
        while True:
            data_recv = str(connectionSocket.recv(bufferSize).decode())
            
            chunkNo = int(data_recv[:8])
            message = data_recv[8:]
            if data_dict.get(chunkNo)==0:
                data_dict.put(chunkNo,message)
            connectionSocket.send(str(1).encode())
            connectionSocket.close()
            break

#broadcasting requests to all clients
def chunkReq(chunkNo,clientNo):
        message = str(chunkNo).encode()
        UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        done =0
        while done ==0:
            UDPServerSocket.sendto(message,(clientIP[clientNo],clientAddressPortUDP[clientNo]))
            ready = select.select([UDPServerSocket], [], [], 1)
            if ready[0]:
                foundCh =int(UDPServerSocket.recvfrom(bufferSize)[0].decode())
                return foundCh

        

def broadCast(chunkNo):
    for i in range(n):   
        if chunkReq(chunkNo,i)==1:
            break
    
#sending already captured chunk to the client
def sendChunkToClient(clientNo,chunkNo,message):
    global sendChunkToClientOn
    global clientsFinished
    if sendChunkToClientOn[clientNo]==1:
        data_send = str(cts(chunkNo)+message).encode()
        TCPServerSocket =socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        TCPServerSocket.connect((clientIP[clientNo],clientAddressPortTCP[clientNo]))
        TCPServerSocket.send(data_send)
        closingmsg=int(TCPServerSocket.recv(bufferSize).decode())
        if closingmsg==-1:
            sendChunkToClientOn[clientNo]=0
            clientsFinished+=1
            TCPServerSocket.send("fin".encode())
            # print("ruk gaya")
        TCPServerSocket.close()
    
#receiving chunk requests from the client
def recvChunkReqFromClient(portNo):
    global sendCounter
    UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    UDPServerSocket.bind((serverIP,serverAddressPortUDP[portNo]))
    while True:
        bytesAddressPair = UDPServerSocket.recvfrom(bufferSize)

        clientNo = int(bytesAddressPair[0].decode()[:8])
        chunkNo= int(bytesAddressPair[0].decode()[8:])
        address = bytesAddressPair[1]
        dataav=0
        with lock:
            dataav =data_dict.get(chunkNo)
            if dataav==0 :
                broadCast(chunkNo)
                dataav=data_dict.get(chunkNo)

        sendChunkToClient(clientNo,chunkNo,dataav)
        UDPServerSocket.sendto(str(1).encode(),address)

for i in range(noOfThreads):  
    x = threading.Thread(target=recvChunksFromClient, args=(i,))
    recvChunkThreads.append(x)
    x.start()

for i in range(noOfThreads):  
    x = threading.Thread(target=recvChunkReqFromClient, args=(i,))
    recvReqThreads.append(x)
    x.start()


