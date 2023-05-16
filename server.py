from ast import arg
from asyncio import start_server
from bluetooth import *
from multiprocessing import Process, Value, Array
import bluetooth
import threading
import time
import tabulate
from select import *
from datetime import datetime

# node name
NODENAME = "maruf"

# keep track of mac address given a node name
activeNodeMAC = {}

# keep track of the sent and received messages
receivedMsgs = [{'id': '0', 'user': '', 'message': ''}]
sentMsgs = [{'id': '0', 'user': '', 'message': '' , 'status': '', 'time': ''}]

# keep track of where current device is active
curActiveLoc = ''

# keep track of neighbor list with sockets (gets refreshed every 5 seconds)
neighbor_list = []

# keep track of current id sequence
cid = [200]

# send incomming data packets to respective methods
def parseData(data, socket):
    print(data)
    parsedData = eval(data)
    if int(parsedData['id']) not in [int(x['id']) for x in receivedMsgs]:
        receivedMsgs.append({'id': parsedData['id'], 'user': parsedData['user'], 'message': parsedData['msg']})
    if parsedData['msg'] == 'Ack':
        parseAckMessage(parsedData, socket)
    elif parsedData['msg'] == 'Request for activation...':
        addActiveUserReqAck(socket, parsedData['user'], parsedData['id'])

# Ack or message checker for a given sequence id (with a time limit)
def parseAckMessage(parsedData, socket):
    for msg in sentMsgs:
        if int(msg['id']) == int(parsedData['id']):
            msg['status'] = 'delivered'
            activeNodeMAC[str(parsedData['user'])] = socket
    for msg in sentMsgs:
        if msg['status'] == 'sent' and (datetime.now() - msg['time']).total_seconds() > 5:
                msg['status'] = 'lost'

def ackOrMsgCheckProcess(id, timeLimit, socket): 
    socket.settimeout(timeLimit)
    
# Neighbor Refresh-------------------------------------
def testConnection(device):
    s = bluetooth.BluetoothSocket( bluetooth.RFCOMM )
    # try:
        # if device not in [x[0] for x in neighbor_list]:
        #     print('attempting connection')
        #     host = bluetooth.find_service(address=device)[0]["host"]
        #     s.connect((host, 30))
        #     neighbor_list.append((device, s))
        # else:
        #     for x in neighbor_list:
        #         if x[0] == device:
        #             x[1].send("control packet")
    # except Exception as e:
    #     print(e)
    #     if device in [x[0] for x in neighbor_list]:
    #         neighbor_list.remove([x for x in neighbor_list if neighbor_list[0] == device][0])
    #     s.close()
        
        
def neighborRefresh():
    
    return
def multiProcessNeighborMethod():
    while True:
        time.sleep(5)
        # p = Process(target=neighborRefresh)
        p = threading.Thread(target = neighborRefresh)
        p.daemon = True
        p.start()
        p.join()

# Add active user
def checkNodeForName(name):
    for neighbor in neighbor_list:
        dataPacket = "{'id': " + cid[0].Value + ", 'user': '"+ NODENAME +"', 'msg': 'Request for activation...' }"
        neighbor[1].send(dataPacket)
        sentMsgs.append({'id': cid[0].Value, 'user': name, 'message': dataPacket , 'status': 'sent', 'time': datetime.now()})
        ackOrMsgCheckProcess(cid[0].Value, 5, neighbor[1])
        cid[0].Value = cid[0].Value + 1

def addActiveUser(name):
    if(name not in activeNodeMAC.keys()):
        checkNodeForName(name)

def startAddActiveUserProcess(user): 
    # p = Process(target=addActiveUser, args=[user])
    p = threading.Thread(target =addActiveUser, args=[user])
    p.daemon = True
    p.start()

# Check/Add add active user request
def addActiveUserReqAck(socket, user, id):
    if curActiveLoc == '':
        dataPacket = "{'id': " + str(id) + ", 'user': '"+ NODENAME +"', 'msg': 'Ack' }"
        socket.send(dataPacket)
        sentMsgs.append({'id': id, 'user': user, 'message': dataPacket , 'status': 'sent', 'time': datetime.now()})
    

def listenToNeighbor(socket):
    while True:
        #print('started listening')
        data = socket.recv(1024)
        parseData(data, socket)

def sendToNeighbor(msg, user):
    if user in activeNodeMAC:
        dataPacket = "{'id': " + cid[0].Value + ", 'user': '"+ NODENAME +"', 'msg':'" + msg + "'}"
        activeNodeMAC[user].send(dataPacket)
        sentMsgs.append({'id': cid[0].Value, 'user': user, 'message': dataPacket , 'status': 'sent', 'time': datetime.now()})
        cid[0].Value = cid[0].Value + 1
    else:
        print("Please add " + user + " as an active user before sending a message.")
    
def startNeighborListeningProcess():
    while True:
        for neighbor in neighbor_list:
            listenToNeighbor(neighbor[1])

def acceptConnections():
    server_socket = BluetoothSocket( RFCOMM )
    #server_socket.setblocking(False)
    port = 30
    server_socket.bind(('', port))
    server_socket.listen(8)
    while True:
        readable, writable, excepts = select([server_socket], [], [])
        if server_socket in readable:
            client_socket, client_info = server_socket.accept()
     #       client_socket.setblocking(False)
            neighbor_list.append((client_info[0], client_socket))
           

# print messages
def printMessages():
    print("\n---------------------Sent Messages------------------------\n")
    header = sentMsgs[0].keys()
    rows =  [x.values() for x in sentMsgs]
    print(tabulate.tabulate(rows, header))
    print("\n---------------------Received Messages------------------------\n")
    header = receivedMsgs[0].keys()
    rows =  [x.values() for x in receivedMsgs]
    print(tabulate.tabulate(rows, header))

# Read CMD Line Inputs --------------------------------
def processInput():
    var = input("\nCommand > ")
    if var == "neighbor":
        print("\n70:1C:E7:82:88:49 *")
        for neighbor in neighbor_list:
            print(neighbor[0])
    elif var.split(" ")[0] == "user":
        startAddActiveUserProcess(var.split(" ")[1])
    elif var.split(" ")[0] == "show":
        printMessages()
    elif var.split(" ")[0] == "send":
        sendToNeighbor(var.split(" ")[1], var.split(' ', 2)[1])
    elif var == "quit":
        quit()

def main():
    # startServer()
    # p = Process(target=multiProcessNeighborMethod)
    p = threading.Thread(target = multiProcessNeighborMethod)
    p.start()
    # s = Process(target=acceptConnections)
    s = threading.Thread(target = acceptConnections)
    s.start()
    # t = Process(target=startServer)
    q = threading.Thread(target = startNeighborListeningProcess)
    q.start()
    while True:
        processInput()


if __name__ == '__main__':
    main()
