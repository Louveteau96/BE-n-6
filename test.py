import serial
import time



########################################################################################################
#                                    INIT DES VARIABLES
########################################################################################################


# Configuration du port série (à adapter selon votre setup)
port = "/dev/ttyUSB0"  # Remplacez par le port série de votre système (ex: "COM3" sur Windows)
baudrate = 9600       # Débit en bauds (vérifiez la documentation de l'analyseur)


id =  "128"
cmd = "lrec"


########################################################################################################
#                                   CREATION DE LA COMMANDE
########################################################################################################

# Convertir chaque chiffre de ID en son code ASCII
ascii_id = []
for c in id:
    ascii_id.append(str(ord(c)))

# Convertir chaque caractère de CMD en son code ASCII
ascii_cmd = []
for c in cmd:
    ascii_cmd.append(str(ord(c)))

# Concaténer les listes et joindre en une seule chaîne
commande = "".join(ascii_id + ascii_cmd)+"10"

########################################################################################################
#                                         PROGRAMME
########################################################################################################


# Initialisation de la connexion série
ser = serial.Serial(
    port=port,
    baudrate=baudrate,
    timeout=1,
    #stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    #parity=serial.PARITY_NONE
)

try:
    print(f"Connecté au port {port} à {baudrate} bauds.")

    while True:
        # Exemple : Envoyer une commande C-Link pour récupérer la concentration d'ozone
        
        ser.write(commande)
        print(f"Commande envoyée : {cmd}")

        # Lire la réponse
        response = ser.readline()
        if response:
            print(f"Réponse reçue : {response.decode('ascii')}")

        time.sleep(10)  # Pause de 1 seconde entre chaque lecture

except KeyboardInterrupt:
    print("Arrêt du programme par l'utilisateur.")

except Exception as e:
    print(f"Erreur : {e}")

finally:
    ser.close()
    print("Connexion fermée.")
