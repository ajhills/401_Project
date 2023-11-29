import random
import socket

class PeerClient:
    def __init__(self, server_host, server_port, upload_port):
        self.server_host = server_host
        self.server_port = server_port
        self.upload_port = upload_port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.hostname = socket.gethostname()

    def add_rfc_from_file(self, file_path):
        with open(file_path, 'r') as file:
            first_line = file.readline().strip()
            rfc_number, title = first_line.split(':')
            # Ensure rfc_number is just the number
            rfc_number = rfc_number.replace('RFC', '').strip()
            self.send_add_request(rfc_number, title.strip())

    def connect_to_server(self):
        self.client_socket.connect((self.server_host, self.server_port))
        print(f"Connected to server at {self.server_host}:{self.server_port}.")

    def send_request(self, message):
        self.client_socket.sendall(message.encode())
        response = self.client_socket.recv(4096).decode()
        print("Response from server:")
        print(response)
        return response

    def send_get_request(self, rfc_number):
        request = self.format_request('GET', rfc_number, None)
        return self.send_request(request)    

    def send_add_request(self, rfc_number, title):
        request = self.format_request('ADD', rfc_number, title)
        return self.send_request(request)

    def send_lookup_request(self, rfc_number, title):
        request = self.format_request('LOOKUP', rfc_number, title)
        return self.send_request(request)

    def send_list_request(self):
        request = self.format_request('LIST', None, None)
        return self.send_request(request)

    def format_request(self, method, rfc_number, title):
        request_line = f"{method} RFC {rfc_number} P2P-CI/1.0\r\n"
        host_line = f"Host: {self.hostname}\r\n"
        port_line = f"Port: {self.upload_port}\r\n"
        title_line = f"Title: {title}\r\n" if title else ""
        return request_line + host_line + port_line + title_line + "\r\n"
    
    def execute_command(self):
        while True:
            command = input("Enter command (ADD, LOOKUP, LIST, GET, EXIT): ").strip().upper()
            if command == 'ADD':
                rfc_file_name = input("Enter the name of the RFC file (e.g., rcf1.txt): ")
                self.add_rfc_from_file(rfc_file_name)
            elif command == 'LOOKUP':
                rfc_number = input("Enter RFC number to lookup: ").strip()
                title = input("Enter title of the RFC: ").strip()
                self.send_lookup_request(rfc_number, title)
            elif command == 'LIST':
                self.send_list_request()
            elif command == 'GET':
                rfc_number = input("Enter RFC number to get: ").strip()
                response = self.send_get_request(rfc_number)
                if 'P2P-CI/1.0 200 OK' in response:
                    self.save_rfc_file(rfc_number, response)
                else:
                    print("RFC not found.")
            elif command == 'EXIT':
                print("Exiting...")
                break
            else:
                print("Invalid command. Please try again.")

    def save_rfc_file(self, rfc_number, response):
        # Check if the response header indicates that data is included
        if '\r\n\r\n' in response:
            data = response.split('\r\n\r\n', 1)[1]
            with open(f'rfc{rfc_number}.txt', 'w') as file:
                file.write(data)
            print(f"RFC {rfc_number} downloaded successfully.")
        else:
            print("No data received to save.")

if __name__ == "__main__":
    server_host = input("Enter the server IP address: ")
    server_port = 7734  # Assuming the server port is 7734
    upload_port = random.randint(1000, 9999)  # Random 4-digit port number for the client
    peer = PeerClient(server_host, server_port, upload_port)
    peer.connect_to_server()
    peer.execute_command()
