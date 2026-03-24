import socket

#AF_INEXT car IPV4
#SOCK_DGRAM pour udp (rapidité pas de vérif contrairement à tcp)
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

#cf doc page:206 pour le port
port = 9880
ip = "192.00" #IP de la machine pour l'instant je sais pas
adress = (ip,port)
s.settimeout(10)
id = bytes([177])


def commande(cmd,socket,adress):
    cmd = cmd+"\n"
    if id == bytes([0]):
        socket.sendto(cmd.encode('ascii'), adress)
    else:
        socket.sendto(id+cmd.encode('ascii'), adress)


def main():
    commande("O2",s,adress)
    reponse = s.recv(1024).decode('ascii')
    print(reponse)

main()

