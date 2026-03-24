import serial

#Connexion port série

#Pour l'id cf page:206
id = bytes([177])
port = "/dev/ttyUSB0"

def connexion(port_serie,id):
    port = port_serie
    ser = serial.Serial(port,baudrate=9600,timeout=10)
    return ser

#commande met lui même un \n si la commande donnée en a déjà un normalement ça ne pose pas probleme
def commande(cmd,ser):
    cmd = cmd+"\n"
    if id==bytes([0]):
        return ser.write(cmd.encode('ascii'))
    else:
        return ser.write(id + cmd.encpde('ascii'))

#Initialistation de l'appareil
def initialisation(ser):
    #set mode remote pour pouvoir interagir avec l'appareil
    commande("set mode remote",ser)
    reponse = ser.readline().decode('ascii')
    if(reponse != "set mode remote ok"):
        print("Initialisation échouée remote")
        print("réponse : " + reponse)
        return
    
    #gas unit en ppb
    commande("set gas unit ppb")
    reponse = ser.readline()
    if(reponse != "set gas unit ppb ok"):
        print("Initialisation échouée ppb")
        print("réponse : " + reponse)
        return
    return

#Envoi et réception des commandes
def recuperation_donnee(ser):
    commande("lrec 1 1",ser) #l'instrument envoi 1 enregistrement
    #Ce qu'on recoit
    #lrec 1 1 heure date flag o3 hio3 cellA cellB benchT lampT o3lamp flowA, flowB, pression
    donnees = ser.readline().decode('ascii')
    print("Données lues : " + donnees)
    
def close_connexion(ser):
    ser.close()


def main():
    # ser = connexion("Com3","123")
    # initialisation(ser)
    # recuperation_donnee(ser)
    # close_connexion(ser)
    id = bytes([177])
    print (id)

main()