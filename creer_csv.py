import csv
import os
import re


def creer_csv(nom : str):

    nom_fichier = f"{nom}.csv"
    with open(nom_fichier, mode="w",newline="",encoding="utf-8") as f:
        writer = csv.writer(f)
        #entete
        writer.writerow(["heure","date","flag","o3","cellA","cellB","benchT","lampT","o3lamp","flowA","flowB","pression"])

    print(f"Fichier '{nom_fichier}' créé avec succès")
    return nom_fichier

def donnee_valide(donnee : str) -> bool:
    return bool(re.match(r'^lrec 1 1\b',donnee))

def ajouter_donnees(nom : str, donnees : str):

    if not donnee_valide(donnees):
        raise ValueError("Format invalide")
    
    if not nom.endswith(".csv"):    
        nom_fichier = f"{nom}.csv"
    else:
        nom_fichier = nom
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

def extraire_données(nom : str):
    
    #on vérifie que le fichier existe

    nom_fichier = f"{nom}.csv"
    if not os.path.exists(nom_fichier):
        raise FileNotFoundError(f"Le fichier '{nom_fichier}' n'existe pas. Créez-le d'abord.")
    

    #on demande le nombre de données souhaitées

    while True:
        try:
            n = int(input("Entrez un le nombre de données souhaitées dans votre nouveau csv: "))
            if 1 <= n <= 12:
                break
            print("Erreur : le nombre doit être entre 1 et 12.")
        except ValueError:
            print("Erreur : veuillez entrer un entier valide.")
    

    print(f"Vous avez saisi : {n}")

    indices = []

    #on enregistre les indices des données souhaitées

    for i in range(n):

        while True:
            try:
                print("1 = heure, 2 = date, 3 = flag, 4 = o3, 5 =cellA, 6 = cellB, 7 = benchT, 8 = lampT, 9 = o3lamp, 10 = flowA, 11 = flowB, 12 = pression")
                a = int(input(f"Entrez la données souhaitées en numéro {i+1}: "))
                if 1 <= a <= 12:
                    break
                print("Erreur : le nombre doit être entre 1 et 12.")
            except ValueError:
                print("Erreur : veuillez entrer un entier valide.")

        print(f"vous avez saisi {a}")
        indices.append(a)


    #on crée un nouveau fichier


    nom_sortie = "extrait_" + nom_fichier


    #claude ma fait cadeau de ce ptit scipte pour extraire les colomnes souhaitées avec les indices demandés 

    with open(nom_fichier, newline='', encoding='utf-8') as f_in, \
         open(nom_sortie, 'w', newline='', encoding='utf-8') as f_out:
        
        lecteur = csv.reader(f_in)
        ecrivain = csv.writer(f_out)
        
        for ligne in lecteur:
            nouvelle_ligne = [ligne[i] for i in indices if i < len(ligne)]
            ecrivain.writerow(nouvelle_ligne)
    
    print(f"Fichier créé : {nom_sortie}")
    return nom_sortie
    

def main():
    csv = creer_csv("test1")
    rec1 = "lrec 1 1 09:53 03-02-26 0C105004 0.000 0.000 0 7 20.2 46.5 63.6 0.754 0.721 747.0"
    rec2 = "lrec 1 1 10:00 04-02-26 0C105004 0.002 0.999 1 7 20.2 46.5 63.6 0.754 0.721 747.0"
    print(csv)
    ajouter_donnees("test1",rec1)
    ajouter_donnees(csv,rec2)

main()