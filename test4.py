import serial
import time

port = "/dev/ttyUSB0"  # Remplacez par le port série de votre système (ex: "COM3" sur Windows)
baudrate = 9600       # Débit en bauds (vérifiez la documentation de l'analyseur)
id = 49 + 128
a = chr(id)
setmode = "set mode remote"


def envoie_commande(ser,cmd):
    commande = f"{a}{cmd}\r\n"
    nb = ser.write(commande.encode('utf-8'))
    if nb==0:
        raise ValueError("envoie vide")

def lire_reponse(ser):
    reponse=""
    i=0
    while (len(reponse)==0) and (i<100):
        time.sleep(0.1)
        reponse = ser.readline().decode('utf-8')
        i += 1
    if(i<100):
        print(f"réponse reçu : {reponse}")
    else:
        print("aucun message reçu")
    return reponse

ser = serial.Serial(port,baudrate=baudrate,timeout=1)

#cmd = f"{a}{setmode}\r\n"

#nb = ser.write(cmd.encode('utf-8'))

envoie_commande(ser,"set mode remote")

#reponse = ser.readline().decode('utf-8')
#print(reponse)

lire_reponse(ser)

time.sleep(1)

#cmd2 = f"{a}lrec\r\n"
#ser.write(cmd2.encode('utf-8'))
envoie_commande(ser,"lrec 1 1")
time.sleep(1)

lire_reponse(ser)
#analyse = ser.readline().decode('utf-8')
#print(analyse)

envoie_commande(ser,"o3")
lire_reponse(ser)