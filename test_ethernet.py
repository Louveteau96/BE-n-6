import socket

#AF_INEXT car IPV4
#SOCK_DGRAM pour udp (rapidité pas de vérif contrairement à tcp)
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

port = 5000
ip = "192.00" #IP de la machine
adress = (ip,port)
s.settimeout(10)

#peut être il faut faire un .encode sur "O2"
#et du coup .decode sur s.recv
s.sendto("O2\n",adress)
print(s.recv(1024))