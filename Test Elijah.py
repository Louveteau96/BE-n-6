import serial
import time

port = "/dev/ttyUSB0"  # Remplacez par le port série de votre système (ex: "COM3" sur Windows)
baudrate = 9600       # Débit en bauds (vérifiez la documentation de l'analyseur)
id = 49 + 128
a = chr(id)
setmode = "set mode remote"
setmode_recuperation = "set mode remote"
lrec = "lrec 1 1"
lrec_recuperation = "flags"
o3 = "o3"
o3_recuperation = "o3"
precedent_expectation = "null"


def envoie_commande(ser,cmd):
    commande = f"{a}{cmd}\r\n"
    nb = ser.write(commande.encode('utf-8'))
    if nb==0:
        raise ValueError("envoie vide")

def lire_reponse(ser,expected_content):
    reponse=""
    i=0
    while (len(reponse)==0) and (i<100):
        time.sleep(0.1)
        reponse = ser.readline().decode('utf-8')
        #Ajout du if pour le contenu
        split_answer = reponse.split()
        #Si la réponse attendue est la reponse ou si une partie de la réponse est expected_content
        #Si la réponse contient la même chose qu'avant on refuse
        #Exemple pour o3 il y est dans lrec mais pour lrec on veut flag qui n'est pas présent dans la réponse de o3
        if expected_content in reponse.lower() or expected_content in split_answer and not(precedent_expectation in split_answer):
            i += 100
            #On attribue expected_content à precedent_expectation
            precedent_expectation = expected_content
        i += 1
    if(i<100):
        print(f"réponse reçu : {reponse}")
    else:
        print("aucun message reçu")
    return reponse

ser = serial.Serial(port,baudrate=baudrate,timeout=1)

#cmd = f"{a}{setmode}\r\n"

#nb = ser.write(cmd.encode('utf-8'))

envoie_commande(ser,setmode)

#reponse = ser.readline().decode('utf-8')
#print(reponse)

lire_reponse(ser,setmode_recuperation)

time.sleep(1)

#cmd2 = f"{a}lrec\r\n"
#ser.write(cmd2.encode('utf-8'))
envoie_commande(ser,lrec)
time.sleep(1)

lire_reponse(ser,lrec_recuperation)
#analyse = ser.readline().decode('utf-8')
#print(analyse)

envoie_commande(ser,o3)
lire_reponse(ser,o3_recuperation)