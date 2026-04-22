import socket

PORT = 9880
IP = "0.0.0.0"  # Écoute sur toutes les interfaces, y compris localhost

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind((IP, PORT))
print(f"Serveur UDP en écoute sur {IP}:{PORT}")

while True:
    data, addr = s.recvfrom(1024)
    data = data.decode('utf-8', errors='replace').strip()
    print(f"Reçu de {addr}: {data}")
    s.sendto(f"ACK:{data}".encode('utf-8'), addr)