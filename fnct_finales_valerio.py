import csv
import os
import re
import serial
import time
from datetime import datetime

##########################################################################
#fonctions envoie et reception messages

def envoie_commande(ser,cmd,id):
    commande = f"{id}{cmd}\r\n"
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

############################################################################
#fonctions csv



def donnee_valide(donnee : str) -> bool:
    return("flags" in donnee)
    

def ajouter_donnees(nom : str, donnees : str):

    if not donnee_valide(donnees):
       raise ValueError("Format invalide")
    

    #quand c'est a la racine

    # if not nom.endswith(".csv"):    
    #     nom_fichier = f"{nom}.csv"
    # else:
    #     nom_fichier = nom

    # Construire le chemin vers le dossier record
    dossier = os.path.join(os.path.dirname(__file__), "record")

    #quand c'est dans le fichier record

    if not nom.endswith(".csv"):
        nom_fichier = os.path.join(dossier, f"{nom}.csv")
    else:
        nom_fichier = os.path.join(dossier, nom)


    parametres = donnees.split() #on transforme la chaine de charactere en tableau de str
    

    #["heure","date","o3","cellA","cellB","benchT","lampT","o3lamp","flowA","flowB","pression"]
    #14:14 05-26-26 flags 0C100000 o3 7.469 hio3 0.000 cellai 115685 cellbi 117893 bncht 31.6 lmpt 52.8 o3lt 67.3 flowa 0.751 flowb 0.717 pres 751.8

    parametres.pop(22)#pres
    parametres.pop(20)#flowb
    parametres.pop(18)#flowa
    parametres.pop(16)#o3lt
    parametres.pop(14)#lmpt
    parametres.pop(12)#bncht
    parametres.pop(10)#cellbi
    parametres.pop(8)#cellai
    parametres.pop(7)#val hio3
    parametres.pop(6)#hio3
    parametres.pop(4)#o3
    parametres.pop(3)#val flag
    parametres.pop(2)#flags

    #convertion des floats en int

    # for i in range(2,len(parametres)):
    #     parametres[i] = str(int(float(parametres[i])))

    # Récupérer l'heure et la date actuelles
    date_heure = datetime.now()


    parametres[0] = date_heure.strftime("%H:%M:%S")
    parametres[1] = date_heure.strftime("%m-%d-%Y")
    

    #on conserve date et heure pour l'affichage sur les graphs

    if not os.path.exists(nom_fichier):
        raise FileNotFoundError(f"Le fichier '{nom_fichier}' n'existe pas. Créez-le d'abord.")
    
    with open(nom_fichier, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(parametres)

    return nom_fichier


###########################################FIN DES FONCTIONS AUXILIAIRES##############################################

#commandes finales

def creer_csv(): #créer un fichier csv dont le nom est hh-mm-ss_jj-mm-aaaa et le place dans un dossier record existant ou le creer s'il n'existe pas à la meme racine que le programme

    # Récupérer l'heure et la date actuelles
    date_heure = datetime.now()

    # Formater en hh-mm-ss_jj-mm-aaaa
    nom = date_heure.strftime("%H-%M-%S_%d-%m-%Y")

     # Dossier de destination
    dossier = os.path.join(os.path.dirname(__file__), "record")
    os.makedirs(dossier, exist_ok=True)  # Crée le dossier s'il n'existe pas

    nom_fichier = os.path.join(dossier, f"{nom}.csv")


    with open(nom_fichier, mode="w",newline="",encoding="utf-8") as f:
        writer = csv.writer(f)
        #entete
        writer.writerow(["heure","date","o3","cellA","cellB","benchT","lampT","o3lamp","flowA","flowB","pression"])

    print(f"Fichier '{nom_fichier}' créé avec succès")
    return nom_fichier

def connexion(port : str, baudrate : int , id_analyseur : int):
    id_analyseur = id_analyseur  + 128
    
    id = chr(id_analyseur)

    #établissement connexion série

    try:

        ser = serial.Serial(port,baudrate=baudrate,timeout=1)
        print("connexion ser réussie")

    except serial.SerialException as e:

        print(f"Erreur connexion serial: {e}")
        return False
    

    #set mode remote

    envoie_commande(ser,"set mode remote",id)

    #vérification du set mode remote

    i = 0

    reponse = lire_reponse(ser)


    while(not reponse.__contains__("set mode remote ok") and i<10):

        reponse = lire_reponse(ser)
        i = i+1
    
    if(i>=10):
        raise ValueError("set mode remote échoué")
        return False
    

    print("Connecté")
    
    return ser


def recuperation_donnees(ser : int, csv : str, delais_relevé : int, id : int):

    #boucle infinie

    id2 = chr(id + 128)

    while(True):

        compte = 0
        envoie_commande(ser,"lrec 1 1",id2)

        reponse=lire_reponse(ser)

        while( (not donnee_valide(reponse)) and compte<10):
            compte = compte+1
            reponse=lire_reponse(ser)
        
        # if(compte<10):
        ajouter_donnees(csv,reponse)

        time.sleep(delais_relevé)







# def main():
#     csv = creer_csv()
#     rec1 = "09:53 03-02-26 flags 0C105004 o3 0.000 hio3 0.000 cellai 0 cellbi 7 bncht 20.2 lmpt 46.5 o3lt 63.6 flowa 0.754 flowb 0.721 press 747.0"
#     rec2 = "14:14 05-26-26 flags 0C100000 o3 7.469 hio3 0.000 cellai 115685 cellbi 117893 bncht 31.6 lmpt 52.8 o3lt 67.3 flowa 0.751 flowb 0.717 pres 751.8"
#     print(csv)
#     ajouter_donnees(csv,rec1)
#     ajouter_donnees(csv,rec2)


# def main():
#     ser = connexion("/dev/ttyUSB0",9600,49)
#     print("fin connexion")
#     csv = creer_csv()
#     print("debut rec")
#     recuperation_donnees(ser,csv,5,49)

# # def main():
    
# #     print(donnee_valide("bonjours"))
# #     print(donnee_valide("14:14 05-26-26 flags 0C100000 o3 7.469 hio3 0.000 cellai 115685 cellbi 117893 bncht 31.6 lmpt 52.8 o3lt 67.3 flowa 0.751 flowb 0.717 pres 751.8"))

# main()