from base64 import encode
from calendar import c
from email import message
from socketserver import TCPServer
import sys
import os
import socket
import hashlib
import threading
import time
import random
import socket
import select

beginTime = time.time()
n =5
serverIP = '127.0.0.51'
localPort   = 20001
bufferSize  = 1200
lock = threading.Lock()
noOfThreads = n
totalChunks =0
clientsFinished=0
recvCounter=0
cacheSize =5

clientIP   = ["127.0.0.{}".format(i+69)  for i in range(n)]
clientAddressPortTCP   = [i+20001+n  for i in range(n)]
clientAddressPortUDP   = [i+20001  for i in range(n)]
serverAddressPortTCP   = [i+20001+n  for i in range(n)]
serverAddressPortUDP   = [i+20001  for i in range(n)]

clientData =[{} for i in range(n)]
##threads
initClientThreads=[]
reqChunksThreads=[]
recvChunksThreads=[]
recvChunkReqThreads=[]

#int to string
def cts(n:int):
    s= str(n)
    leng = len(s)
    for i in range(0,8-leng):
        s= "0"+s
    return s
##sending available chunk to server
def sendChunkToServer(clientNo,chunkNo,message):
    data_send = (cts(chunkNo)+message).encode()
    TCPServerSocket =socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
    TCPServerSocket.connect((serverIP,serverAddressPortTCP[clientNo]))
    TCPServerSocket.send(data_send)
    TCPServerSocket.recv(bufferSize)
    TCPServerSocket.close()

##listening requests of the server
def recvChunkReqFromServer(clientNo):
    global clientsFinished
    global n
    global recvCounter
    UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    UDPClientSocket.bind((clientIP[clientNo],clientAddressPortUDP[clientNo]))
    while clientsFinished<n:
            ready = select.select([UDPClientSocket], [], [], 1)
            if ready[0]:
                bytesAddressPair = UDPClientSocket.recvfrom(bufferSize)

                chunkNo= int(bytesAddressPair[0])

                if haveClientData[clientNo][chunkNo]==1:
                    sendChunkToServer(clientNo,chunkNo,clientData[clientNo][chunkNo])
                    UDPClientSocket.sendto(str(1).encode(),bytesAddressPair[1])
                else:
                    UDPClientSocket.sendto(str(-1).encode(),bytesAddressPair[1])


## Receiving chunks from the server
def recvChunksFromServer(clientNo):
    global clientsFinished
    global totalChunks
    TCPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
    TCPClientSocket.bind((clientIP[clientNo], clientAddressPortTCP[clientNo]))
    TCPClientSocket.listen(1)
    while len(clientData[clientNo]) < totalChunks:
        connectionSocket, addr = TCPClientSocket.accept()

        data_recv = str(connectionSocket.recv(bufferSize).decode())   
        chunkNo = int(data_recv[:8])
        message = data_recv[8:]
        if haveClientData[clientNo][chunkNo]==0:
            haveClientData[clientNo][chunkNo]=1
            clientData[clientNo].update({chunkNo:message})
        print("client {} data size became {}".format(clientNo,len(clientData[clientNo])))
        if(len(clientData[clientNo]) >= totalChunks):
            connectionSocket.send(str(-1).encode())
            connectionSocket.recv(bufferSize)
            clientsFinished+=1
        else:
            connectionSocket.send(str(1).encode())
        connectionSocket.close()



##Requesting Chunks From Server
def reqChunksFromServer(clientNo):
    global totalChunks
    global recvCounter
    cur_req =0
    UDPClientSocket=socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    while len(clientData[clientNo]) <totalChunks:   
        if haveClientData[clientNo][cur_req]==0:
            msgFromClient = cts(clientNo)+str(cur_req)
            bytesToSend   = msgFromClient.encode()
            RTTData[clientNo][cur_req]=time.time()
            done =0
            while done==0 :
                UDPClientSocket.sendto(bytesToSend, (serverIP,serverAddressPortUDP[clientNo]))
                ready = select.select([UDPClientSocket], [], [], 1)
                if ready[0]:
                    UDPClientSocket.recvfrom(bufferSize)
                    RTTData[clientNo][cur_req]=time.time()-RTTData[clientNo][cur_req]
                    done =1
        cur_req= (cur_req+1)%totalChunks

##Initial receiving of chunks
def initRecvClient(clientNo):
    global totalChunks
    UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    UDPClientSocket.bind((clientIP[clientNo],clientAddressPortUDP[clientNo]))
    while True:
        bytesAddressPair = UDPClientSocket.recvfrom(bufferSize)
        message = (bytesAddressPair[0].decode())
        address = bytesAddressPair[1]
        if(message ==  "stop it"):
            print(clientNo," stopped")
            break
        UDPClientSocket.sendto(str(1).encode(),address)
        chunkNo = int(message[:8])
        clientData[clientNo].update({chunkNo:message[8:]})
        totalChunks+=1
    return

#threading
for i in range(noOfThreads):   
    x = threading.Thread(target=initRecvClient, args=(i,))
    initClientThreads.append(x)
    x.start()

#wait for init to complete
for i in range(noOfThreads):
    initClientThreads[i].join()
print(totalChunks)
RTTData =[[0. for i in range(totalChunks) ] for j in range(n)]

##clientDataList 
haveClientData=[[0 for i in range(totalChunks)] for i in range(n)]
for i in range(n):
    for j in clientData[i].keys():
        haveClientData[i][j]=1

for i in range(noOfThreads):  
    x = threading.Thread(target=recvChunkReqFromServer, args=(i,))
    recvChunkReqThreads.append(x)
    x.start()

for i in range(noOfThreads):   
    x = threading.Thread(target=recvChunksFromServer, args=(i,))
    recvChunksThreads.append(x)
    x.start()

for i in range(noOfThreads):  
    x = threading.Thread(target=reqChunksFromServer, args=(i,))
    reqChunksThreads.append(x)
    x.start()



for i in range(noOfThreads):
    reqChunksThreads[i].join()
print("requesting chunks finished")

final_text=["" for i in range(n)]
for j in range(n):
    lisT =[clientData[j][i] for i in range(totalChunks)]
    # print(lisT)
    final_text[j] = "".join(lisT)
endTime = time.time()
for i in range(n):
    hash = hashlib.md5(final_text[i].encode()).hexdigest()
    print("md5 sum:",hash)
print("time Taken for n = {} with cache size {}".format(n,cacheSize),endTime-beginTime)

# outtxt = open('result.txt', mode='w')
# avgRTTforAll =0
# totalNZ=0
# for i in range(totalChunks):
#     outtxt.write("chunk_no={}: ".format(i))
#     NZc=0
#     avgRTTfc=0
#     for c in range(n):
#         outtxt.write(str(RTTData[c][i])+" ")

#         if RTTData[c][i]*100000000000>0 :
#             # print(RTTData[c][i])
#             avgRTTforAll+=RTTData[c][i]
#             avgRTTfc+=RTTData[c][i]
#             totalNZ+=1
#             NZc+=1
#     if NZc>0:        
#         outtxt.write(str(avgRTTfc/NZc)+"\n")
#     else:
#         outtxt.write("nobodyRequested"+"\n")
# outtxt.write("average RTT for all chunks: "+str(avgRTTforAll/totalNZ)+"\n")
# outtxt.close()
for i in range(n):
    outtxt = open('client{}data.txt'.format(i), mode='w')
    outtxt.write(final_text[i])
    outtxt.close()

for i in range(noOfThreads):
    recvChunksThreads[i].join()
print("receiving chunks finished")









