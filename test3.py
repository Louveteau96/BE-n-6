import serial
import time

class Appareil: #(int,string,int,int) -> numéro du port, OS, timeout; id machine
    def __init__(self,port,os,timeout,id):
        self.ser = self._connexion_(port,os,timeout)
        self.id = id

    def _connexion_(port_serie,os,timeout):
        if(os=="linux"):
            port = "/dev/ttyUSB"
        elif(os=="windows"):
            port = "COM"
        else:
            raise ValueError("cet os n'est pas reconnu. Merci de choisir linux ou windows")
        port = port + str(port_serie)
        ser = serial.Serial(port=port, baudrate=9600, timeout=timeout)
        if ser.is_open:
            print(f"port {port} ouvert avec succès")
        else:
            raise ValueError(f"échec de l'ouverture du port {port}")
        return ser

def envoie_commande(app,cmd):
    a=chr(app.id)
    commande = f"{a}{cmd}\r\n"
    nb = app.ser.write(commande.encode('utf-8'))
    if nb==0:
        raise ValueError("envoie vide")
    
def supprimer_connexion(app):
    app.ser.close()
    del app

def lire_reponse(app):
    reponse=""
    i=0
    while (len(reponse)==0) and (i<100):
        time.sleep(0.1)
        reponse = app.ser.readline().decode('utf-8')
        i += 1
    if(i<100):
        print(f"réponse reçu : {reponse}")
    else:
        print("aucun message reçu")
    return reponse

def set_mode_remote(app):
    envoie_commande("set mode remote",app)
    reponse = lire_reponse(app)
    if reponse != "set mode remote ok":
        raise ValueError("échec de mise en mode remote")

def recuperation_donnees(app):
    envoie_commande("lrec 1 1",app)
    reponse = lire_reponse(app)
    print(reponse)
    return reponse

def main1():
    analyseur = Appareil(0,"linux",1,47)
    set_mode_remote(analyseur)
    reponse=recuperation_donnees(analyseur)
    supprimer_connexion(analyseur)
