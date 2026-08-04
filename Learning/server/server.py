import socket

server = socket.socket()

server.bind(("127.0.0.1", 8000))

while True:
    server.listen()

    print("Server is waiting...")

    client, address = server.accept()

    print("Connected!")
    print(client)

    print(address)

    client.close()