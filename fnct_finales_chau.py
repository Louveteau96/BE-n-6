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
    return bool(re.match(r'^lrec 1 1\b',donnee))

def ajouter_donnees(nom : str, donnees : str):

    if not donnee_valide(donnees):
        raise ValueError("Format invalide")
    
    # if not nom.endswith(".csv"):    
    #     nom_fichier = f"{nom}.csv"
    # else:
    #     nom_fichier = nom

    # Construire le chemin vers le dossier record
    dossier = os.path.join(os.path.dirname(__file__), "record")

    if not nom.endswith(".csv"):
        nom_fichier = os.path.join(dossier, f"{nom}.csv")
    else:
        nom_fichier = os.path.join(dossier, nom)


    parametres = donnees.split() #on transforme la chaine de charactere en tableau de str
    valeurs = parametres[3:] #on supprime lrec 1 1
    valeurs.pop(4) #on supprime hio3 qui n'interesse pas 

    #on conserve date et heure pour l'affichage sur les graphs

    if not os.path.exists(nom_fichier):
        raise FileNotFoundError(f"Le fichier '{nom_fichier}' n'existe pas. Créez-le d'abord.")
    
    with open(nom_fichier, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(valeurs)

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
        writer.writerow(["heure","date","flag","o3","cellA","cellB","benchT","lampT","o3lamp","flowA","flowB","pression"])

    print(f"Fichier '{nom_fichier}' créé avec succès")
    return nom_fichier

def connexion(port : str, baudrate : int , id_analyseur : int):
    id = id_analyseur  + 128


    #établissement connexion série

    try:
        ser = serial.Serial(port,baudrate=baudrate,timeout=1)
    except serial.SerialException as e:
        print(f"Erreur connexion serial: {e}")
        return False
    
    #set mode remote

    envoie_commande(ser,"set mode remote",id)

    #vérification du set mode remote

    i = 0
    
    reponse = ""

    while(reponse.strip() != "set mode remote ok" and i < 10):
        time.sleep(0.1)
        reponse = lire_reponse(ser)
        i = i+1
    
    if(i>=10):
        raise ValueError("set mode remote échoué")
    else:
        print(reponse)
    
    return ser


def recuperation_donnees(ser : int, csv : str, delais_relevé : int):

    #boucle infinie

    while(True):

        compte = 0
        envoie_commande(ser,"lrec 1 1")

        reponse=lire_reponse(ser)

        while( (not donnee_valide(reponse)) and compte<10):
            compte = compte+1
            reponse=lire_reponse(ser)
        
        if(compte<10):
            ajouter_donnees(csv,reponse)

        time.sleep(delais_relevé)


def main():
    csv = creer_csv()
    rec1 = "lrec 1 1 09:53 03-02-26 0C105004 0.000 0.000 0 7 20.2 46.5 63.6 0.754 0.721 747.0"
    rec2 = "lrec 1 1 10:00 04-02-26 0C105004 0.002 0.999 1 7 20.2 46.5 63.6 0.754 0.721 747.0"
    print(csv)
    ajouter_donnees(csv,rec1)
    ajouter_donnees(csv,rec2)

main()
