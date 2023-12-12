from asyncio.windows_events import NULL
import pickle
import socket
import struct
import time
from constants import *
# import os

# def create_snmp_response():
#     version = 0x00 
#     community = "public"
#     request_type = 0xA0
#     request_id = 0
#     error_status = 0
#     error_index = 0 
#     PDU_type = 0
#     name = "IP"
#     value = NULL
#     snmp_packet = pickle.dumps([version, community, PDU_type, request_type, request_id, error_status, error_index, name, value])
#     return snmp_packet

#--- FETCH HELPER ---#

def download_file(host_info, fname, rname, repo_path):
    try:
        # result = self.send_receive([GET_INFO, username], self.server_host, self.server_port)
        sender_host = host_info[0]
        sender_port = host_info[1] + 1

        new_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        new_sock.connect((sender_host, sender_port))
        new_sock.send(pickle.dumps([SEND,fname]))
        print("[**] Downloading file...")
        
        file_path = os.path.join(repo_path, rname)
        with open(file_path, 'wb') as f:
            while True:
                data = new_sock.recv(BUFFER)
                if not data:
                    break
                f.write(data)
            f.close()
        # print('[*] DOWNLOAD successfully.')
        new_sock.close()
        return True
    except Exception as e:
        new_sock.close()
        # print("Download:",e)
        return False

def send_file(conn, file_name, repo_path):
    try:
        print("[**] Sending file...")
        # repo_path = os.path.join(os.getcwd(), 'repo')
        # downloads_path = os.path.join(os.getcwd(), 'downloads')
        file_path = os.path.join(repo_path, file_name)
        # print("File path:", file_path)
        # print("Repo path:", repo_path)
        with open(file_path, 'rb') as f:
            for data in f:
                conn.sendall(data)
        f.close()
        conn.close()            
        print('[*] SEND successfully.')
        return True
    except Exception as e:
        return False

#--- PING HELPER ---#

def respond_ping(conn, addr):
    try:
        print(f'[*] Received ping from {addr[0]} : {addr[1]}')
        conn.send(pickle.dumps([PING_STATUS, True]))
    except Exception as e:
        conn.send(pickle.dumps([PING_STATUS, False]))

#--- PUBLISH HELPER ---#

def make_publish_copy(lname_path, fname, repo_path):
    try:
        fname_path = os.path.join(repo_path, fname)
        # if os.path.exists(fname_path):
        #     action = input("Replace the original file or Cancel to rename (R/C): ")
        #     if action == 'C':
        #         return False
        #     elif action == 'R':
        #         pass
        #     else:
        #         while action != 'C' and action != 'R':
        #             action = input("Invalid option, please enter again (R/C): ")
        #             if action == 'C':
        #                 return False
        #             elif action == 'R':
        #                 break
        os.chmod(lname_path, 0o400) #get permission
        with open(lname_path, 'rb') as source_file:
            with open(fname_path, 'wb+') as destination_file:
                chunk_size = 8192
                while True:
                    chunk = source_file.read(chunk_size)
                    if not chunk:
                        break
                    destination_file.write(chunk)
        return True
    except Exception as e:
        return False
    # print("success make copy to repo")

# def create_manage_repo(repo_path):
#     manage_repo_name = "manage.repo"
#     create_file_path = os.path.join(repo_path, manage_repo_name)
#     if not os.path.exists(create_file_path):
#         with open(create_file_path, 'w'):
#             pass
#     else:
#         print("already create manage repo")
#         return create_file_path
#     os.system(f'attrib +h "{create_file_path}"') #hide repo file
#     print(f'success create manage repo at "{create_file_path}"')

def create_repo(repo_path):
    # current_folder = os.path.dirname(os.path.abspath(__file__))
    # current_folder = os.getcwd()
    # folder_name = "repo"
    # create_folder_path = os.path.join(current_folder, folder_name)
    try:
        if not os.path.exists(repo_path):
            os.makedirs(repo_path)
        return True
    except Exception as e:
        return False
    # print(repo_path)

#--- DELETE HELPER ---#

def delete_file(fname, repo_path):
    try:
        fname_path = os.path.join(repo_path, fname)
        os.remove(fname_path)
        return True
    except Exception as e:
        return False