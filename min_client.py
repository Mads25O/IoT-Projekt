from socket import *

serverName = '192.168.13.128'
serverPort = 12000
clientSocket = socket(AF_INET, SOCK_DGRAM)

print ()
print ("-------------------------------")
print ("Klienten er klar til at sende")
print ("-------------------------------")
print()
print()

navn = 0
connected = " har connected!"

while True:
    if navn == 0:
        navn = input('Hvad er dit navn?: ')
        clientSocket.sendto(navn.encode()+connected.encode(), (serverName, serverPort))
        navn = navn + ": "
    else:
        message = input('Skriv noget til serveren: ')
        clientSocket.sendto(navn.encode()+message.encode(), (serverName, serverPort))
