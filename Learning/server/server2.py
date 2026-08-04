import socket

server = socket.socket()

server.bind(("127.0.0.2", 9000))
print(server.fileno())



s1 = socket.socket()
s2 = socket.socket()
s3 = socket.socket()

print(s1.fileno())
print(s2.fileno())
print(s3.fileno())

while True:
    server.listen()

    print("Server is waiting...")

    client, address = server.accept()

    print("Connected!")
    print(client)

    print(address)

    client.close()