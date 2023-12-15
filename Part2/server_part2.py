from base64 import encode
from collections import OrderedDict
from socketserver import TCPServer, UDPServer
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
cacheSize =5

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

data_dict =LRUCache(5)
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

#recv chunk from client
def recvChunksFromClient(clientNo):
    UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    UDPServerSocket.bind((serverIP, serverAddressPortUDP[clientNo]))
    while True:
        btr = UDPServerSocket.recvfrom(bufferSize)
        data_recv = btr[0].decode()
        
        chunkNo = int(data_recv[:8])
        message = data_recv[8:]
        if data_dict.get(chunkNo)==0:
            data_dict.put(chunkNo,message)

        UDPServerSocket.sendto(str(1).encode(),btr[1])

#broadcasting requests to all clients
def chunkReq(chunkNo,clientNo):     
    message = str(chunkNo).encode()
    TCPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
    try:

        TCPServerSocket.connect((clientIP[clientNo],clientAddressPortTCP[clientNo]))
        TCPServerSocket.send(message)
        foundCh =int(TCPServerSocket.recv(bufferSize).decode())
        TCPServerSocket.close()
        return foundCh
    except:
        None

        

def broadCast(chunkNo):

    for i in range(n):   
        if chunkReq(chunkNo,i) ==1:
            break
    
#sending already captured chunk to the client
def sendChunkToClient(clientNo,chunkNo,message):
    global sendChunkToClientOn
    global clientsFinished
    if sendChunkToClientOn[clientNo]==1:
        data_send = (cts(chunkNo)+message).encode()
        UDPServerSocket =socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        done =0
        while done==0 :
            UDPServerSocket.sendto(data_send,(clientIP[clientNo],clientAddressPortUDP[clientNo]))
            ready = select.select([UDPServerSocket], [], [], 1)
            if ready[0]:
                closingmsg=int(UDPServerSocket.recvfrom(bufferSize)[0].decode())
                done =1
                if closingmsg==-1:
                    sendChunkToClientOn[clientNo]=0
                    clientsFinished+=1

                    
    
#receiving chunk requests from the client
def recvChunkReqFromClient(clientNo):
    global sendCounter
    TCPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
    TCPServerSocket.bind((serverIP,serverAddressPortTCP[clientNo]))
    TCPServerSocket.listen(1)
    while sendChunkToClientOn[clientNo]==1:
        connectionSocket, addr = TCPServerSocket.accept()
        bytesAddressPair = connectionSocket.recv(bufferSize).decode()


        chunkNo= int(bytesAddressPair)
        
        dataav=0
        with lock:
            dataav=data_dict.get(chunkNo)
            if dataav==0 :
                broadCast(chunkNo)
                dataav=data_dict.get(chunkNo)

        sendChunkToClient(clientNo,chunkNo,dataav)
        connectionSocket.send(str(1).encode())
        connectionSocket.close()

for i in range(noOfThreads):  
    x = threading.Thread(target=recvChunksFromClient, args=(i,))
    recvChunkThreads.append(x)
    x.start()

for i in range(noOfThreads):  
    x = threading.Thread(target=recvChunkReqFromClient, args=(i,))
    recvReqThreads.append(x)
    x.start()


