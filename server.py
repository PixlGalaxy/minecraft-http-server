import socket
from threading import Thread
import struct
import json
import base64

##Application Port
SERVER_PORT = 12505

##Minecraft Server Details
Minecraft_Server_ConnectionMessage = """
Message Displayed To User When Connecting To Server.
""" ##Message To Show When Kicked From Server

Minecraft_Server_MOTD = "A Simple HTTP/MINECRAFT Server" ##Message Shown On The Server
Minecraft_Server_Version = "1.16.5" ##Minecraft Server Version
Minecraft_Server_Max_Players = 1024 ##Max Players 
Minecraft_Server_Online_Players = 1024 ##Online Players Connected To Server
Minecraft_Server_ICONPNG = "./static/resources/favicon.png" ##Minecraft Server Icon PNG 64x64

def read_varint(s):
    number = 0
    for i in range(5):
        byte = s.recv(1)
        if len(byte) == 0:
            raise IOError("Socket closed")
        number |= (byte[0] & 0x7F) << (7 * i)
        if not byte[0] & 0x80:
            break
    return number

def write_varint(value):
    out = bytearray()
    while True:
        if (value & ~0x7F) == 0:
            out.append(value)
            break
        out.append((value & 0x7F) | 0x80)
        value >>= 7
    return out

def handle_client(client_socket, address):
    try:
        packet_length = read_varint(client_socket)
        http_client_socket = client_socket
        http_client_adress = address

        packet_id = read_varint(client_socket)
        
        if packet_id == 0x00:  # Handshake packet ID
            print(f"Connection From: {address} (MINECRAFT)")
            protocol_version = read_varint(client_socket)
            server_address_length = read_varint(client_socket)
            server_address = client_socket.recv(server_address_length)
            server_port = struct.unpack('>H', client_socket.recv(2))[0]
            next_state = read_varint(client_socket)
            
            if next_state == 1:  # Status request
                packet_length = read_varint(client_socket)
                packet_id = read_varint(client_socket)

                if packet_id == 0x00:  # Status request packet ID
                    
                    # Convert image to base64
                    with open("{}".format(Minecraft_Server_ICONPNG), "rb") as image_file:
                        favicon_base64 = base64.b64encode(image_file.read()).decode('utf-8')

                    status_response = {
                        "version": {
                            "name": Minecraft_Server_Version,
                            "protocol": 754
                        },
                        "players": {
                            "max": Minecraft_Server_Max_Players,
                            "online": Minecraft_Server_Online_Players,
                            "sample": []
                        },
                        "description": {
                            "text": Minecraft_Server_MOTD
                        },
                        "favicon": f"data:image/png;base64,{favicon_base64}"
                    }
                    status_response_json = json.dumps(status_response)
                    response_data = status_response_json.encode('utf-8')

                    packet_id = 0x00  # Status response packet ID
                    response_packet = write_varint(packet_id) + write_varint(len(response_data)) + response_data
                    response_length = write_varint(len(response_packet))
                    response_packet = response_length + response_packet

                    client_socket.sendall(response_packet)

                packet_length = read_varint(client_socket)
                packet_id = read_varint(client_socket)

                if packet_id == 0x01:  # Ping packet ID
                    payload = client_socket.recv(8)
                    pong_response = write_varint(0x01) + payload
                    pong_length = write_varint(len(pong_response))
                    pong_packet = pong_length + pong_response

                    client_socket.sendall(pong_packet)

            elif next_state == 2:  # Login state
                message = json.dumps({"text": Minecraft_Server_ConnectionMessage})
                json_data = message.encode('utf-8')
                
                packet_id = 0x00 
                response_data = write_varint(packet_id) + write_varint(len(json_data)) + json_data
                response_length = write_varint(len(response_data))
                response_packet = response_length + response_data

                client_socket.sendall(response_packet)
                print(f"Connection From: {address} (MINECRAFT) Disconnected.")
        
        else:
            print(f"Connection From: {address} (HTTP)")
            try:
                request_lines = client_socket.recv(1024).decode().split("\r\n")
                request_method, file_requested, _ = request_lines[0].split(" ")

                if file_requested.endswith(".css"):
                    handle_static_file_request(f"./static/{file_requested}", client_socket) # CSS File

                if file_requested.endswith(".ico"):
                    handle_static_file_request(f"./static/resources/{file_requested}", client_socket) # ICO File

                if file_requested.endswith(".webp"):
                    handle_static_file_request(f"./static/resources/{file_requested}", client_socket) # WEBP File
                else:
                    with open("./templates/event_details.html", "r") as file: # HTML File
                        html_content = file.read()

                    http_response = f"""HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n{html_content}"""

                    client_socket.sendall(http_response.encode('utf-8'))
                        
            except Exception as e:
                print(f"Error While Managing HTTP Connection For: {address}: {e}")

    except Exception as e:
        print(f"Error While Managing Connection For: {address}: {e}")

def handle_static_file_request(file_path, client_socket):
    try:
        with open(file_path, "rb") as file:
            file_content = file.read()

        http_response = f"HTTP/1.1 200 OK\r\nContent-Length: {len(file_content)}\r\nContent-Type: text/css\r\n\r\n".encode() + file_content
        client_socket.sendall(http_response)
    except FileNotFoundError:
        print(f"Static File Not Found: {file_path}")
        http_response = b"HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\n\r\n"
        client_socket.sendall(http_response)

def run_minecraft_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('', SERVER_PORT))
    server_socket.listen(5)
    print(f"Application Listening On Port: {SERVER_PORT}")

    while True:
        client_socket, address = server_socket.accept()
        Thread(target=handle_client, args=(client_socket, address)).start()

if __name__ == '__main__':
    minecraft_thread = Thread(target=run_minecraft_server)
    minecraft_thread.start()
