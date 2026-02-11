import socket
from threading import Thread
import struct
import json
import base64
import os
from dotenv import load_dotenv
from datetime import datetime
import time

# Load environment variables
load_dotenv()

# Configuration from .env
SERVER_PORT = int(os.getenv('SERVER_PORT', 12505))
HOST = os.getenv('HOST', '0.0.0.0')

# Minecraft Server Details
Minecraft_Server_ConnectionMessage = os.getenv('MINECRAFT_CONNECTION_MESSAGE', 'Welcome to the server!').encode().decode('unicode_escape')
Minecraft_Server_MOTD = os.getenv('MINECRAFT_MOTD', 'A Simple HTTP/MINECRAFT Server')
Minecraft_Server_Max_Players = int(os.getenv('MINECRAFT_MAX_PLAYERS', 100))
Minecraft_Server_Online_Players = int(os.getenv('MINECRAFT_ONLINE_PLAYERS', 1))
Minecraft_Server_ICONPNG = os.getenv('MINECRAFT_ICON_PATH', './static/resources/favicon.png')
Minecraft_Server_Version = os.getenv('MINECRAFT_VERSION', '1.20.1')

# Event Configuration
EVENT_TITLE = os.getenv('EVENT_TITLE', 'UHC EVENT')
EVENT_DATE = os.getenv('EVENT_DATE', '2026-02-15T19:00:00')
EVENT_DATE_FORMATTED = os.getenv('EVENT_DATE_FORMATTED', '15 de Febrero de 2026')
EVENT_OPEN_TIME = os.getenv('EVENT_OPEN_TIME', '18:00')
EVENT_START_TIME = os.getenv('EVENT_START_TIME', '19:00')
EVENT_VERSION = os.getenv('EVENT_VERSION', '1.20.1')
EVENT_FORMAT = os.getenv('EVENT_FORMAT', 'Duos')
EVENT_IP = os.getenv('EVENT_IP', 'zaylar.itzgalaxy.com:12505')
EVENT_DISCORD = os.getenv('EVENT_DISCORD', 'https://discord.gg/example')

# Horarios por zona
PERU_TIME = os.getenv('PERU_TIME', '18:00')
ARGENTINA_TIME = os.getenv('ARGENTINA_TIME', '20:00')
USA_TIME = os.getenv('USA_TIME', '19:00')
LA_TIME = os.getenv('LA_TIME', '16:00')
MEXICO_TIME = os.getenv('MEXICO_TIME', '17:00')
SPAIN_TIME = os.getenv('SPAIN_TIME', '01:00')

# Calculate event timestamp (Unix milliseconds for JavaScript)
try:
    event_datetime = datetime.strptime(EVENT_DATE, '%Y-%m-%dT%H:%M:%S')
    EVENT_TIMESTAMP_MS = int(event_datetime.timestamp() * 1000)
except:
    EVENT_TIMESTAMP_MS = int(datetime.now().timestamp() * 1000)

# Server statistics
server_stats = {
    'connections': [],
    'total_visitors': 0
}

def log_connection(address, connection_type, message=""):
    """Log connection details"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = {
        'timestamp': timestamp,
        'ip': address[0],
        'port': address[1],
        'type': connection_type,
        'message': message
    }
    server_stats['connections'].append(log_entry)
    print(f"[{timestamp}] {connection_type} Connection from {address[0]}:{address[1]} - {message}")
    
    # Keep last 100 connections
    if len(server_stats['connections']) > 100:
        server_stats['connections'] = server_stats['connections'][-100:]

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

def handle_minecraft_client(client_socket, address):
    """Handle Minecraft Protocol"""
    try:
        packet_length = read_varint(client_socket)
        packet_id = read_varint(client_socket)
        
        if packet_id == 0x00:  # Handshake packet
            log_connection(address, "MINECRAFT", "Handshake received")
            protocol_version = read_varint(client_socket)
            server_address_length = read_varint(client_socket)
            server_address = client_socket.recv(server_address_length)
            server_port = struct.unpack('>H', client_socket.recv(2))[0]
            next_state = read_varint(client_socket)
            
            if next_state == 1:  # Status request
                packet_length = read_varint(client_socket)
                packet_id = read_varint(client_socket)

                if packet_id == 0x00:  # Status request
                    try:
                        with open(Minecraft_Server_ICONPNG, "rb") as image_file:
                            favicon_base64 = base64.b64encode(image_file.read()).decode('utf-8')
                    except:
                        favicon_base64 = ""

                    status_response = {
                        "version": {
                            "name": Minecraft_Server_Version,
                            "protocol": 764
                        },
                        "players": {
                            "max": Minecraft_Server_Max_Players,
                            "online": Minecraft_Server_Online_Players,
                            "sample": []
                        },
                        "description": {
                            "text": Minecraft_Server_MOTD
                        }
                    }
                    
                    if favicon_base64:
                        status_response["favicon"] = f"data:image/png;base64,{favicon_base64}"

                    status_response_json = json.dumps(status_response)
                    response_data = status_response_json.encode('utf-8')

                    packet_id = 0x00
                    response_packet = write_varint(packet_id) + write_varint(len(response_data)) + response_data
                    response_length = write_varint(len(response_packet))
                    response_packet = response_length + response_packet

                    client_socket.sendall(response_packet)

                packet_length = read_varint(client_socket)
                packet_id = read_varint(client_socket)

                if packet_id == 0x01:  # Ping request
                    log_connection(address, "MINECRAFT", "Ping received")
                    payload = client_socket.recv(8)
                    pong_response = write_varint(0x01) + payload
                    pong_length = write_varint(len(pong_response))
                    pong_packet = pong_length + pong_response
                    client_socket.sendall(pong_packet)
                    
            elif next_state == 2:  # Login state
                log_connection(address, "MINECRAFT", "Login attempt")
                message = json.dumps({"text": Minecraft_Server_ConnectionMessage})
                json_data = message.encode('utf-8')
                
                packet_id = 0x00
                response_data = write_varint(packet_id) + write_varint(len(json_data)) + json_data
                response_length = write_varint(len(response_data))
                response_packet = response_length + response_data

                client_socket.sendall(response_packet)
                log_connection(address, "MINECRAFT", "Disconnected")
                server_stats['total_visitors'] += 1
                
    except Exception as e:
        log_connection(address, "MINECRAFT", f"Error: {str(e)}")

def handle_client(client_socket, address):
    """Detect Minecraft or HTTP protocol and route accordingly"""
    try:
        # Peek at the first byte to detect protocol
        client_socket.settimeout(2)
        first_byte = client_socket.recv(1)
        client_socket.settimeout(None)
        
        if not first_byte:
            client_socket.close()
            return
        
        # For Minecraft: First packet is a varint packet length (starts with low bytes)
        # For HTTP: First byte is usually 'G' (GET=71), 'P' (POST=80), 'H' (HEAD=72), etc.
        
        if chr(first_byte[0]) in ['G', 'P', 'H', 'D', 'O', 'T', 'C']:  # HTTP methods
            # HTTP Protocol
            try:
                log_connection(address, "HTTP", "Request received")
                
                # Reconstruct request
                remaining = client_socket.recv(4096)
                request_data = first_byte + remaining
                request_text = request_data.decode('utf-8', errors='ignore')
                
                handle_http_request(request_text, client_socket, address)
                server_stats['total_visitors'] += 1
            except Exception as e:
                log_connection(address, "HTTP", f"Error: {str(e)}")
        else:
            # Minecraft Protocol
            remaining_packet = client_socket.recv(4096)
            full_data = first_byte + remaining_packet
            
            # Create a new socket-like object with the buffered data
            class BufferedSocket:
                def __init__(self, sock, data):
                    self.sock = sock
                    self.buffer = data
                    self.buffer_pos = 0
                
                def recv(self, size):
                    if self.buffer_pos < len(self.buffer):
                        chunk = self.buffer[self.buffer_pos:self.buffer_pos + size]
                        self.buffer_pos += len(chunk)
                        
                        if len(chunk) < size:
                            # Need more data from socket
                            additional = self.sock.recv(size - len(chunk))
                            chunk += additional
                        return chunk
                    return self.sock.recv(size)
                
                def sendall(self, data):
                    return self.sock.sendall(data)
                
                def close(self):
                    return self.sock.close()
            
            buffered = BufferedSocket(client_socket, full_data)
            handle_minecraft_client(buffered, address)
            
    except Exception as e:
        log_connection(address, "UNKNOWN", f"Connection error: {str(e)}")
    finally:
        try:
            client_socket.close()
        except:
            pass

def handle_http_request(request_text, client_socket, address):
    """Handle HTTP requests"""
    try:
        request_lines = request_text.split("\r\n")
        if not request_lines:
            return
        
        request_line = request_lines[0].split(" ")
        if len(request_line) < 2:
            return
        
        method = request_line[0]
        path = request_line[1]
        
        # Handle static files
        if path.endswith('.css'):
            handle_static_file_request(f"./static{path}", client_socket)
            return
        
        if path.endswith('.ico') or path.endswith('.png') or path.endswith('.jpg') or path.endswith('.webp'):
            handle_static_file_request(f"./static/resources/{path.split('/')[-1]}", client_socket)
            return
        
        if path.startswith('/api/stats'):
            response_data = {
                'motd': Minecraft_Server_MOTD,
                'version': Minecraft_Server_Version,
                'max_players': Minecraft_Server_Max_Players,
                'online_players': Minecraft_Server_Online_Players,
                'total_visitors': server_stats['total_visitors'],
                'recent_connections': server_stats['connections'][-10:]
            }
            json_response = json.dumps(response_data)
            http_response = f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {len(json_response)}\r\n\r\n{json_response}"
            client_socket.sendall(http_response.encode('utf-8'))
            return
        
        if path.startswith('/api/connections'):
            response_data = {
                'connections': server_stats['connections'][-20:],
                'total': server_stats['total_visitors']
            }
            json_response = json.dumps(response_data)
            http_response = f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {len(json_response)}\r\n\r\n{json_response}"
            client_socket.sendall(http_response.encode('utf-8'))
            return
        
        # Serve main HTML page
        try:
            with open("./templates/event_details.html", "r", encoding='utf-8') as f:
                html_content = f.read()
            
            # Replace template variables
            html_content = html_content.replace('{{ event_title }}', EVENT_TITLE)
            html_content = html_content.replace('{{ event_date }}', EVENT_DATE)
            html_content = html_content.replace('{{ event_timestamp_ms }}', str(EVENT_TIMESTAMP_MS))
            html_content = html_content.replace('{{ event_date_formatted }}', EVENT_DATE_FORMATTED)
            html_content = html_content.replace('{{ event_open_time }}', EVENT_OPEN_TIME)
            html_content = html_content.replace('{{ event_start_time }}', EVENT_START_TIME)
            html_content = html_content.replace('{{ event_version }}', EVENT_VERSION)
            html_content = html_content.replace('{{ event_format }}', EVENT_FORMAT)
            html_content = html_content.replace('{{ event_ip }}', EVENT_IP)
            html_content = html_content.replace('{{ event_discord }}', EVENT_DISCORD)
            
            # Horarios
            html_content = html_content.replace('{{ peru_time }}', PERU_TIME)
            html_content = html_content.replace('{{ argentina_time }}', ARGENTINA_TIME)
            html_content = html_content.replace('{{ usa_time }}', USA_TIME)
            html_content = html_content.replace('{{ la_time }}', LA_TIME)
            html_content = html_content.replace('{{ mexico_time }}', MEXICO_TIME)
            html_content = html_content.replace('{{ spain_time }}', SPAIN_TIME)
            
            http_response = f"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nContent-Length: {len(html_content)}\r\nConnection: close\r\n\r\n{html_content}"
            client_socket.sendall(http_response.encode('utf-8'))
        except Exception as e:
            log_connection(address, "HTTP", f"Template error: {str(e)}")
            error_response = "HTTP/1.1 500 Internal Server Error\r\nContent-Length: 0\r\n\r\n"
            client_socket.sendall(error_response.encode('utf-8'))
    
    except Exception as e:
        log_connection(address, "HTTP", f"Request error: {str(e)}")

def handle_static_file_request(file_path, client_socket):
    try:
        with open(file_path, "rb") as file:
            file_content = file.read()

        content_type = "text/css"
        if file_path.endswith(".ico"):
            content_type = "image/x-icon"
        elif file_path.endswith(".png"):
            content_type = "image/png"
        elif file_path.endswith(".jpg") or file_path.endswith(".jpeg"):
            content_type = "image/jpeg"
        elif file_path.endswith(".webp"):
            content_type = "image/webp"

        http_response = f"HTTP/1.1 200 OK\r\nContent-Length: {len(file_content)}\r\nContent-Type: {content_type}\r\nConnection: close\r\n\r\n".encode() + file_content
        client_socket.sendall(http_response)
    except FileNotFoundError:
        log_connection(("unknown", 0), "HTTP", f"File not found: {file_path}")
        http_response = b"HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\nConnection: close\r\n\r\n"
        client_socket.sendall(http_response)
    except Exception as e:
        log_connection(("unknown", 0), "HTTP", f"Static file error: {str(e)}")

def run_minecraft_server():
    """Run Minecraft protocol server"""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, SERVER_PORT))
    server_socket.listen(5)
    print(f"\n{'='*60}")
    print(f"🎮 Minecraft Server listening on {HOST}:{SERVER_PORT}")
    print(f"🌐 HTTP Server available at http://localhost:{SERVER_PORT}")
    print(f"{'='*60}\n")

    while True:
        try:
            client_socket, address = server_socket.accept()
            Thread(target=handle_client, args=(client_socket, address), daemon=True).start()
        except KeyboardInterrupt:
            print("Shutting down server...")
            break
        except Exception as e:
            print(f"Error accepting connection: {e}")

if __name__ == '__main__':
    # Run unified server
    run_minecraft_server()
