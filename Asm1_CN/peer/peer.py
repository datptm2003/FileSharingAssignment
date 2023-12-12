# from atexit import register
import socket
# import os
from constants import *
import peer.helper as helper
from server.server import Server
import threading
import pickle
import time
import shlex

class Peer:
    def __init__(self, host='localhost', port=PEER_PORT, server_host='localhost', server_port=SERVER_PORT, max_connect = 16):
        self.username = ''
        self.host = host
        self.port = port
        #--- DEBUG ONLY ---#
        # self.port = int(input("Enter port: "))
        #------------------#
        self.sock = None
        # self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.sock.bind((self.host, self.port))
        
        # self.sock.listen(max_connect)
        self.semaphore = threading.Semaphore(max_connect)
        self.server_host = server_host
        self.server_port = server_port
        # self.start_time = time.time()
        self.is_online = 0
        self.max_connect = max_connect
        self.repo_path = REPO_PATH
        print("[*] Client is on host address", self.host)
    
    #--- REQUEST HANDLING HELPER ---#

    # def respond_ping(self):
    #     client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #     client_address = (self.host, 12000)
    #     client_socket.bind(client_address)
    #     client_socket.listen(1)

    #     print('[*] Client is ready to receive pings.')

    #     while True:
    #         data, server_address = client_socket.recv(1024)
    #         request = pickle.loads(data)
    #         request_type = request[2]
    #         print(request_type)
    #         request_id = request[3]
    #         print(f'[*] Received ping from {server_address}')
    #         if request_type == 0xA0:
    #             client_socket.sendto(helper.create_snmp_response("public", request_id, self.start_time), server_address)

    def send_receive(self, message, host, port):
        # print(host, port)
        result = None
        if host == self.server_host and port == self.server_port:
            # print('Sock:',self.sock)
            # print('Message:',message)
            self.sock.send(pickle.dumps(message))            # send some data
            result = pickle.loads(self.sock.recv(BUFFER))    # receive the response
        else:
            new_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            new_sock.bind((self.host,self.port))
            new_sock.connect((host,port))
            new_sock.send(pickle.dumps(message))                # send some data
            result = pickle.loads(new_sock.recv(BUFFER))        # receive the response
            new_sock.close()
        return result
  
    

    #--- COMMAND HANDLING ---#
    def handle_listen(self, conn, addr):
        try:
            data = conn.recv(BUFFER)
            if not data:
                return
            request = pickle.loads(data)  # unwrap the request
            if request[0] == SEND:
                fname = request[1]
                self.semaphore.acquire()
                helper.send_file(conn, fname, self.repo_path)
                self.semaphore.release()
                
            if request[0] == PING:
                self.semaphore.acquire()
                helper.respond_ping(conn, addr)
                self.semaphore.release()
        except Exception as e:
            print("[*] Error: SEND RESPONSE failed!")
    
    def listen(self):
        self.lst_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.lst_sock.bind((self.host, self.port + 1))
        self.lst_sock.listen(self.max_connect)
        while True:
            if self.is_online == 1:
                try:
                    (conn, addr) = self.lst_sock.accept()
                    # print("[*] Got a connection from ", addr[0], ":", addr[1])
                    thread = threading.Thread(target=self.handle_listen, args = (conn, addr))
                    thread.start()
                except Exception as e:
                    pass
                # thread.join()

    def send_command(self):
        while True:
            try:
                command_line = input('>> ')
                parsed_string = shlex.split(command_line)
                # parsed_string = command_line.split()
                if (parsed_string[0] == "connect"):
                    server_ip = parsed_string[1]
                    self.server_host = server_ip
                    server_port = int(parsed_string[2])
                    self.server_port = server_port
                    try:
                        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        # self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
                        # self.sock.bind((self.host, self.port))
                        self.sock.connect((server_ip, server_port))
                        self.host, self.port = self.sock.getsockname()
                    except Exception as e:
                        # print("Connect:",e)
                        print("[*] Error: CONNECT failed!")
                    else:
                        print("[*] Client address:", self.host, ":", self.port)
                        print("[*] Client connected with server at:", server_ip, ":", server_port)
                        listen_thread = threading.Thread(target=self.listen, args=())
                        listen_thread.start()
                        # listen_thread.join()

                elif (parsed_string[0] == "register"):
                    if self.is_online == 1:
                        print("[*] You have already signed in!")
                        continue
                    username = parsed_string[1]
                    password = parsed_string[2]
                    self.semaphore.acquire()
                    register_status = self.register(username, password)
                    if register_status[1] and register_status[2] == 1:
                        self.is_online = 1
                        self.username = username
                        self.password = password
                        server_repo_path = os.path.join(REPO_PATH, self.host + '/' + str(self.server_port-1))
                        self.repo_path = os.path.join(server_repo_path, username)
                        print("[*] REGISTER successfully.")
                    elif register_status[1] and register_status[2] == 0:
                        print("[*] The username already exists.")
                    else:
                        print("[*] Error: REGISTER failed!")
                    # print("[*] Congratulations you have been registered successfully.\n[*] You will now be put to the listening state.")
                    self.semaphore.release()

                elif (parsed_string[0] == "disconnect"):
                    self.semaphore.acquire()
                    if self.is_online == 1:
                        logout_status = self.logout()
                        if logout_status[1]:
                            self.is_online = 0
                            self.sock.close()
                            self.lst_sock.close()
                            # self.sock = None
                            print("[*] LOGOUT successfully.")
                            print("[*] Client disconnected with server at:", self.server_host, ":", self.server_port)
                            self.server_host = 0
                            self.server_port = SERVER_PORT
                        else:
                            print("[*] Error: LOGOUT failed!")
                    else:
                        self.sock.close()
                        self.lst_sock.close()
                        # self.sock = None
                        print("[*] Client disconnected with server at:", self.server_host, ":", self.server_port)
                        self.server_host = 0
                        self.server_port = SERVER_PORT
                    self.semaphore.release()
                    

                elif (parsed_string[0] == "login"):
                    if self.is_online == 1:
                        print("[*] You have already signed in.")
                        continue
                    username = parsed_string[1]
                    password = parsed_string[2]
                    self.semaphore.acquire()
                    login_status = self.login(username, password)
                    if login_status[1] and login_status[2] == 1:
                        self.is_online = 1
                        self.username = username
                        self.password = password
                        server_repo_path = os.path.join(REPO_PATH, self.host + '/' + str(self.server_port-1))
                        self.repo_path = os.path.join(server_repo_path, username)
                        print("[*] LOGIN successfully.")
                    elif login_status[1] and login_status[2] == 0:
                        print("[*] Invalid password.")
                    elif login_status[1] and login_status[2] == -1:
                        print("[*] The username doesn't exist.")
                    else:
                        print("[*] Error: LOGIN failed!")
                    self.semaphore.release()

                elif (parsed_string[0] == "logout"):
                    self.semaphore.acquire()
                    logout_status = self.logout()
                    if logout_status[1]:
                        self.is_online = 0
                        print("[*] LOGOUT successfully.")
                    else:
                        print("[*] Error: LOGOUT failed!")
                    self.semaphore.release()

                elif (parsed_string[0] == "change_password"):
                    old_password = parsed_string[1]
                    new_password = parsed_string[2]
                    if self.is_online == 0:
                        print("[*] You haven't login yet.")
                        continue
                    self.semaphore.acquire()
                    change_pass_status = self.change_password(old_password,new_password)
                    if change_pass_status[1] and change_pass_status[2] == 2:
                        print("[*] CHANGE_PASSWORD successfully.")
                    elif change_pass_status[1] and change_pass_status[2] == 1:
                        print("[*] The new password is similar to the old one.")
                    elif change_pass_status[1] and change_pass_status[2] == 0:
                        print("[*] Invalid old password.")
                    elif change_pass_status[1] and change_pass_status[2] == -1:
                        print("[*] The username doesn't exist.")
                    else:
                        print("[*] Error: CHANGE_PASSWORD failed!")
                    self.semaphore.release()
                
                elif (parsed_string[0] == "fetch"):
                    if self.is_online == 0:
                        print("[*] You haven't login yet.")
                        continue
                    fname = parsed_string[1]
                    if len(parsed_string) > 2:
                        rname = parsed_string[2]
                    else:
                        rname = fname
                    # repo_path = os.path.join(REPO_PATH, self.username)
                    rname_path = os.path.join(self.repo_path, rname)
                    do_cancel = False
                    if os.path.exists(rname_path):
                        action = input("Replace the original file or Cancel to rename (R/C): ")
                        if action == 'C':
                            do_cancel = True
                        elif action == 'R':
                            pass
                        else:
                            while action != 'C' and action != 'R':
                                action = input("Invalid option, please enter again (R/C): ")
                                if action == 'C':
                                    do_cancel = True
                                elif action == 'R':
                                    break
                    if do_cancel:
                        continue
                    start_time_1 = time.time()
                    self.semaphore.acquire()
                    fetch_status = self.search(fname)
                    self.semaphore.release()
                    sender_username = None
                    end_time_1 = time.time()
                    if fetch_status[1] and fetch_status[2]:
                        list_peers = fetch_status[3]
                        if len(list_peers) == 1:
                            for key in list_peers:
                                sender_username = key
                        elif len(list_peers) > 1:
                            print('[**] List of other peers containing certain file:')
                            for key in list_peers:
                                print(key)
                            sender_username = input('Which client do you want to fetch the file from: ')
                            while sender_username not in list_peers:
                                sender_username = input("You have entered an invalid username, please enter again: ")
                        start_time_2 = time.time()
                        download_status = helper.download_file(list_peers[sender_username], fname, rname, self.repo_path)
                        update_status = self.send_receive([PUBLISH, self.username, rname], self.server_host, self.server_port)
                        end_time_2 = time.time()
                        if download_status and update_status[1]:
                            print(f"[*] DOwNLOAD successfully.")
                            print(f"[*] FETCH successfully. ({(end_time_1 - start_time_1) + (end_time_2 - start_time_2):.5f} s)")
                        else:
                            print("[*] Error: DOWNLOAD failed!")
                    elif fetch_status[1] and not fetch_status[2]:
                        print('[*] No such file in any client!')
                    else:
                        print('[*] Error: FETCH failed!')

                elif (parsed_string[0] == "publish"):
                    if self.is_online == 0:
                        print("[*] You haven't login yet.")
                        continue
                    lname_path = parsed_string[1]
                    fname = parsed_string[2]
                    fname_path = os.path.join(self.repo_path, fname)
                    do_cancel = False
                    if os.path.exists(fname_path):
                        action = input("Replace the original file or Cancel to rename (R/C): ")
                        if action == 'C':
                            do_cancel = True
                        elif action == 'R':
                            pass
                        else:
                            while action != 'C' and action != 'R':
                                action = input("Invalid option, please enter again (R/C): ")
                                if action == 'C':
                                    do_cancel = True
                                elif action == 'R':
                                    break
                    if do_cancel:
                        continue
                    self.semaphore.acquire()
                    start_time = time.time()
                    publish_status = self.publish(lname_path, fname)
                    end_time = time.time()
                    # print("success" if(publish_successfully) else "fail")
                    if publish_status is None or publish_status is False:
                        pass
                        # print("[*] Error: PUBLISH failed! You already publish this file name, please choose another name if you want publish it.")
                    elif publish_status[1]:
                        print(f"[*] PUBLISH successfully. ({end_time - start_time:.5f} s)")
                    else:
                        print("[*] Error: PUBLISH failed!")
                    self.semaphore.release()
                
                elif (parsed_string[0] == "delete"):
                    if self.is_online == 0:
                        print("[*] You haven't login yet.")
                        continue
                    fname = parsed_string[1]
                    # repo_path = os.path.join(REPO_PATH, self.username)
                    fname_path = os.path.join(self.repo_path, fname)
                    if not os.path.exists(fname_path):
                        print("[*] Error: The file doesn't exist in the repo!")
                        continue
                    self.semaphore.acquire()
                    start_time = time.time()
                    delete_status = self.delete(fname)
                    end_time = time.time()
                    # print("success" if(publish_successfully) else "fail")
                    if delete_status[1]:
                        print(f"[*] DELETE successfully. ({end_time - start_time:.5f} s)")
                    else:
                        print("[*] Error: DELETE failed!")
                    self.semaphore.release()

                elif (parsed_string[0] == "search"):
                    if self.is_online == 0:
                        print("[*] You haven't login yet.")
                        continue
                    fname = parsed_string[1]
                    # repo_path = os.path.join(REPO_PATH, self.username)
                    self.semaphore.acquire()
                    fetch_status = self.search(fname)
                    if fetch_status[1] and fetch_status[2]:
                        list_peers = fetch_status[3]
                        print('[**] List of other peers containing certain file:')
                        for key in list_peers:
                            print(key)
                    elif fetch_status[1] and not fetch_status[2]:
                        print('[*] No such file in any client!')
                    else:
                        print('[*] Error: SEARCH failed!')
                    self.semaphore.release()

                elif (parsed_string[0] == "view"):
                    if self.is_online == 0:
                        print("[*] You haven't login yet.")
                        continue
                    if not os.path.exists(self.repo_path):
                        print("[*] Your repo is empty.")
                    else:
                        list_file = [f for f in os.listdir(self.repo_path) if os.path.isfile(self.repo_path + '/' + f)]
                        print("[*] List of all files in your repo:", list_file)

                else:
                    print("[*] Error: Invalid command!")

            except Exception as e:
                # print("Request:",e)
                print("[*] Error: REQUEST failed!")
    
    def run(self):
        # listen_thread = threading.Thread(target=self.listen, args=())
        send_thread = threading.Thread(target=self.send_command, args=())

        # Start both threads
        # listen_thread.start()
        send_thread.start()
        # listen_thread.join()
        send_thread.join()


    #--- LIST OF REMOTE REQUEST FUNCTION ---#
    
    def register(self, username, password):
        # assert self.list_id is None
        result = self.send_receive([REGISTER, username, password], self.server_host, self.server_port)
        return result

    def login(self, username, password):
        # assert self.list_id is None
        result = self.send_receive([LOGIN, username, password], self.server_host, self.server_port)
        return result

    def logout(self):
        # assert self.list_id is None 
        result = self.send_receive([LOGOUT, self.username], self.server_host, self.server_port)
        return result

    def change_password(self, old_password, new_password):
        # assert self.list_id is None 
        result = self.send_receive([CHANGEPWD, self.username, old_password, new_password], self.server_host, self.server_port)
        return result

    def search(self, fname):
        helper.create_repo(self.repo_path)
        result = self.send_receive([SEARCH, fname, self.username], self.server_host, self.server_port)
        return result
    
    def publish(self, lname, fname):
        helper.create_repo(self.repo_path)
        helper.make_publish_copy(lname,fname,self.repo_path)
        # if not check_existed_fname:
        #     # self.error_message="The file is already exist in repo"
        #     return False
        result = self.send_receive([PUBLISH, self.username, fname], self.server_host, self.server_port)
        return result

    def delete(self, fname):
        helper.delete_file(fname,self.repo_path)
        result = self.send_receive([DELETE, self.username, fname], self.server_host, self.server_port)
        return result
