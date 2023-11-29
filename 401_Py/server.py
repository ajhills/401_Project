import socket
import threading

class LinkedListNode:
    def __init__(self, data):
        self.data = data
        self.next = None

class LinkedList:
    def __init__(self):
        self.head = None

    def insert_front(self, data):
        new_node = LinkedListNode(data)
        new_node.next = self.head
        self.head = new_node

    def remove(self, condition):
        current = self.head
        prev = None
        while current:
            if condition(current.data):
                if prev:
                    prev.next = current.next
                else:
                    self.head = current.next
                break
            prev = current
            current = current.next

    def find(self, condition):
        current = self.head
        while current:
            if condition(current.data):
                return current.data
            current = current.next
        return None

    def get_all(self):
        data = []
        current = self.head
        while current:
            data.append(current.data)
            current = current.next
        return data

class Server:
    def __init__(self):
        self.host = '0.0.0.0'  # Listen on all network interfaces
        self.port = 7734
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.peers_list = LinkedList()  # Client linked list
        self.rfc_index = LinkedList()   # RFC linked list

    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"Server listening on {self.host}:{self.port}")

        while True:
            client, address = self.server_socket.accept()
            threading.Thread(target=self.handle_client, args=(client,)).start()

    def handle_client(self, client_socket):
        while True:
            request = client_socket.recv(1024).decode()
            print("Received request:", request)  #debug print
            if not request:
                break  #break if client ends connection

            method, rfc_number, version, headers = self.parse_request(request)
            response = ''
            if method == 'ADD':
                response = self.handle_add(rfc_number, headers)
            elif method == 'LOOKUP':
                response = self.handle_lookup(rfc_number, headers)
            elif method == 'LIST':
                response = self.handle_list(headers)

            client_socket.sendall(response.encode())

    def parse_request(self, request):
        lines = request.split('\r\n')
        first_line = lines[0].split(' ')
        method = first_line[0]

        #get the RFC num.
        #rfc format: "ADD RFC 123 P2P-CI/1.0"
        rfc_number = first_line[2] if len(first_line) > 2 and first_line[1] == 'RFC' else None

        version = first_line[3] if len(first_line) > 3 else None

        headers = {}
        for line in lines[1:]:
            if line:  #skip empty lines
                header_key, header_value = line.split(': ')
                headers[header_key] = header_value

        return method, rfc_number, version, headers

    def handle_add(self, rfc_number, headers):
        #get the host, port and title values
        host = headers.get('Host')
        port = headers.get('Port')
        title = headers.get('Title')

        #make new rfc for add
        rfc_record = (int(rfc_number), title, host)

        #debug print to check what's being added to peers_list and rfc_index
        print("Adding to peers_list:", host, port)
        print("Adding to rfc_index:", rfc_number, title, host)

        #save the client to list 
        if not self.peers_list.find(lambda x: x[0] == host):
            self.peers_list.insert_front((host, port))

        #add rfc to linked list
        self.rfc_index.insert_front(rfc_record)

        #Successful rfc response
        response = f"P2P-CI/1.0 200 OK\nRFC {rfc_number} {title} {host} {port}\n\n"
        return response

    def handle_lookup(self, rfc_number, headers):
        #check if rfc is present in list
        if rfc_number is None:
            return "P2P-CI/1.0 400 Bad Request\r\n\r\n"

        #make rfc an int
        try:
            rfc_number = int(rfc_number)
        except ValueError:
            return "P2P-CI/1.0 400 Bad Request\r\n\r\n"

        #search / get rfc in list
        matching_rfc_records = []
        current = self.rfc_index.head
        while current:
            if current.data[0] == rfc_number:
                matching_rfc_records.append(current.data)
            current = current.next

        #succesful response
        if matching_rfc_records:
            response = "P2P-CI/1.0 200 OK\r\n\r\n"
            for record in matching_rfc_records:
                rfc_num, title, host = record
                peer_info = self.peers_list.find(lambda x: x[0] == host)
                if peer_info:
                    response += f"RFC {rfc_num} {title} {host} {peer_info[1]}\r\n"
        else:
            response = "P2P-CI/1.0 404 Not Found\r\n\r\n"

        return response

    def handle_list(self, headers):
        response = "P2P-CI/1.0 200 OK\r\n\r\n"

        current = self.rfc_index.head
        while current:
            print("Current RFC in Index:", current.data)  #debugging
            rfc_number, title, host = current.data
            peer_info = self.peers_list.find(lambda x: x[0] == host)
            if peer_info:
                host, port = peer_info
                response += f"RFC {rfc_number} {title} {host} {port}\r\n"
            else:
                print("Peer not found for:", current.data)  #debugginh
            current = current.next

        print("Final Response:", response)  #debugging
        return response

if __name__ == "__main__":
    server = Server()
    server.start()
