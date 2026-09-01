import socket

server = socket.socket()
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(('0.0.0.0', 24224))
server.listen(32)
while True:
    conn, _ = server.accept()
    try:
        while conn.recv(65536):
            pass
    except OSError:
        pass
    finally:
        conn.close()
