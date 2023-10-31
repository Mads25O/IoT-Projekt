from socket import *
import time

file_name = 'data.txt'

# Der bliver lavdet en funktion, som åbner en fil med filnavnet "data.txt", og hvis filen ikke findes, bliver den oprettet.
# Derefter bliver der gemt data til filen, da 'a' betyder append. 
def save_data(input_data, filename):
    with open(filename, 'a') as f:
        f.write('\n--------\n')
        f.write(input_data)

def start_af_server(input_data, filename):
    with open(filename, 'a') as f:
        f.write('\n\n!---------------------!\n')
        f.write('En ny server er startet')
        f.write('\n!---------------------!\n')


serverPort = 12000
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(('', serverPort))

print ()
print ("-----------------------------")
print ("Server er klar til at modtage")
print ("-----------------------------")
print()
print()

start = 0

while True:
    
    if start == 0:
        input("Tryk enter for at starte")
        start = 1
        
        # Time.monotonic er en monotonisk klokke (En klokke der ikke kan gå baglæns)
        # T1 sætter tiden, når serveren går i gar
        t0 = int(time.monotonic())
        print()
        print("Serveren modtager nu beskeder")
        start_af_server((),file_name)
    else:
        message, klient = serverSocket.recvfrom(2048)
        message_decode = message.decode()
        
        # T0 tager tiden fra den sidst nye besked.
        t1 = int(time.monotonic())
        # Her tager vi tiden fra den sidst nyeste besked, og substrahere tiden der blev sat, da serveren stattede.
        tid = t1 - t0
        
        # Her tager vi tiden modulus 60, så sekund viseren ikke kommer over 59.
        sekunder = int(tid % 60)
        
        # Her tager vi tiden og dividere med 60, som giver minutterne.
        # Resultatet bliver derefter modulus med 60, så minut viseren ikke gå over 59.
        minutter = int(tid / 60) % 60
        
        # Her tager vi tiden og dividere med 3600, som er antallet af sekunder på en time.
        # Da vi ikke har noget efter time, behøver det ikke bliver modulus med 60.
        timer = int(tid / 3600)
        
        # Her bliver der printet en f string. Som er en string med funktioner i.
        print(f'{timer:02}:{minutter:02}:{sekunder:02}',message_decode)
        print ()
        
        # Saver vores data til en tekst fil.
        save_data(str(f'{timer:02}:{minutter:02}:{sekunder:02} '+message_decode), file_name)
