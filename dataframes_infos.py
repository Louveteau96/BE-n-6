import datetime
import os

import pandas as pd

def ajouter_infos (dataframe,infos):
    splited_infos = infos.split()
    match splited_infos[0]:
        case "lrec" :
            new_row = pd.DataFrame({"o3" : [splited_infos[6]],
                                    "cellA" : [splited_infos[8]],
                                    "cellB" : [splited_infos[9]],
                                    "benchT" : [splited_infos[10]],
                                    "lampT" : [splited_infos[11]],
                                    "o3lamp" : [splited_infos[12]],
                                    "flowA" : [splited_infos[13]],
                                    "flowB" : [splited_infos[14]],
                                    "pression" : [splited_infos[15]]})
            dataframe = pd.concat([dataframe,new_row], ignore_index=True)
            return dataframe
        case _ :
            print("les infos ne correspondent pas au format : " + infos)
            return dataframe

def init_csv (filePath):
    #Comment est fait le dataframe pour l'instant
    # Créer un DataFrame avec les bonnes colonnes
    df = pd.DataFrame(columns=[
        "o3", "cellA", "cellB", "benchT", "lampT",
        "o3lamp", "flowA", "flowB", "pression"
    ])

    # Créer le dossier s'il n'existe pas
    os.makedirs("records", exist_ok=True)
    df.to_csv(filePath,index=False)



def main():
    #Création du csv
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%Hh%Mm%Ss")
    filePath = f"records/{timestamp}_resultat.csv"
    init_csv(filePath)

    #Ajout des infos
    infos = "lrec 1 1 09:53 03-02-26 0C105004 0.000 0.000 0 7 20.2 46.5 63.6 0.754 0.721 747.0"
    df = ajouter_infos(pd.read_csv(filePath),infos)
    df.to_csv(filePath,index=False)
    
    infos = "lrec 1 1 09:53 03-02-26 0C105004 0.000 0.000 0 7 20.2 46.5 63.6 0.754 0.721 748.0"

    #Il faut faire comme ça et ça marche
    #un pd.read_csv
    df = ajouter_infos(pd.read_csv(filePath),infos)
    df.to_csv(filePath,index=False)
    print(df)

main()

#lrec 1 1 09:53 03-02-26 0C105004 0.000 0.000 0 7 20.2 46.5 63.6 0.754 0.721 747.0
#lrec 1 1 heure date flag o3 hio3 cellA cellB benchT lampT o3lamp flowA, flowB, pression

#hi03 est sans intérêt. Date et heures également. Les autres paramètres m'intéressent.
#cellA et cellB sont les fréquences des lampes A et B. 
#benchT : temperature du banc
#lampT : temperature de la lampe UV
#flowA et flowB les débits A et B
#pression la pression du capteur.