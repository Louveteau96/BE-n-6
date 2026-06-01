import socket

#AF_INEXT car IPV4
#SOCK_DGRAM pour udp (rapidité pas de vérif contrairement à tcp)
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

#cf doc page:206 pour le port
port = 9880
#Pour tester mettre l'adresse suivante : "127.0.0.1"
ip = "192.168.0.200" #IP de la machine pour l'instant je sais pas
adress = (ip,port)
s.settimeout(10)
id = 49 + 128
id = chr(id)


def commande(cmd,socket,adress):
    cmd = f"{id}{cmd}\r\n"
    socket.sendto(cmd.encode('utf-8'), adress)


def main():
    commande("O2",s,adress)
    reponse = s.recv(1024).decode('utf-8')
    print(reponse)
    s.close()

main()

