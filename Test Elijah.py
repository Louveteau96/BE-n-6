import serial

#Connexion port série
def connexion(port_serie,id):
    port_serie = "Com3"
    id = "123"
    ser = serial.Serial(port_serie,baudrate=9600,timeout=10)
    ser.write(id)
    return ser


#Initialistation de l'appareil
def initialisation(ser):
    #set mode remote pour pouvoir interagir avec l'appareil
    ser.write("set mode remote")
    reponse = ser.readline()
    if(reponse != "set mode remote ok"):
        print("Initialisation échouée remote")
        return
    
    #gas unit en ppb
    ser.write("set gas unit ppb")
    reponse = ser.readline()
    if(reponse != "set gas unit ppb ok"):
        print("Initialisation échouée ppb")
        return
    return

#Envoi et réception des commandes
def recuperation_donnee(ser):
    ser.write("lrec 1 1") #l'instrument envoi 1 enregistrement
    #Ce qu'on recoit
    #lrec 1 1 heure date flag o3 hio3 cellA cellB benchT lampT o3lamp flowA, flowB, pression
    donnees = ser.readline()
    print("Données lues : " + donnees)
    
def close_connexion(ser):
    ser.close()

#Questions :
#Est-ce que le write(id) doit se faire à chaque lrec ou juste une initialisation
def main():
    ser = connexion("Com3","123")
    initialisation(ser)
    recuperation_donnee(ser)
    close_connexion(ser)

main()