import pickle
import socket
from socket import AF_INET, SOCK_DGRAM
import struct
import time
from constants import *
import hashlib

# def create_snmp_request(community):
#     version = 0x00  # SNMPv1
#     request_type = 0xA0  # GET PDU
#     request_id = 1
#     error_status = 0
#     error_index = 0
#     null_byte = 0
#     PDU_type = 0
   
#     snmp_packet = pickle.dumps([version, community, request_type, request_id, error_status, error_index, null_byte, PDU_type])
#     return snmp_packet

# def parse_snmp_response(snmp_response):
#     if snmp_response:
#         response = pickle.loads(snmp_response)
        
#         # pdu_type = response[7]
#         error_status = response[4]
#         print("error", error_status)
#         if error_status == 0:
#             return True
#     return False
# def ping(set_of_host_info, host_name, port):
#     server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#     client_address = (set_of_host_info.get(host_name),port)
#     server_socket.settimeout(2.0)
#     for i in range(5):  
#         start_time = time.time()
#         snmp_request = create_snmp_request("public")
#         try:
#             server_socket.send(snmp_request, client_address)
#             response, _ = server_socket.recv(BUFFER)

#             end_time = time.time()
#             elapsed_time = end_time - start_time
#             if parse_snmp_response(response):
#                 print("SNMP Ping Successful")
#             else:
#                 print("SNMP Ping Unsuccessful")
#             print(f'Received response:  in {elapsed_time:.4f} seconds')
#         except (socket.timeout, WindowsError):
#             print(f'Ping {i + 1} unsuccessful. Timeout reached.')

#         time.sleep(1)

#     server_socket.close()

def hash_password(password):
   password_bytes = password.encode('utf-8')
   hash_object = hashlib.sha256(password_bytes)
   return hash_object.hexdigest()


def register(conn, set_of_file_lists, set_of_host_name, username, password, ip, port):  
    # list_id = len(set_of_lists) + 1 
    try:
        if username not in set_of_host_name:
            hashed_password = hash_password(password)
            set_of_host_name[username] = [ip,port,hashed_password,1]
            set_of_file_lists[username] = []
            conn.send(pickle.dumps([REGISTER_STATUS, True, 1]))      # Successfully registered with new username 
        else:
            conn.send(pickle.dumps([REGISTER_STATUS, True, 0]))      # Existed username
    except Exception as e:
        conn.send(pickle.dumps([REGISTER_STATUS, False]))

def login(conn, set_of_host_name, username, password, new_port):
    # list_id = len(set_of_lists) + 1 
    try:
        if username in set_of_host_name:
            true_password = set_of_host_name.get(username)[2]
            hashed_password = hash_password(password)
            if hashed_password == true_password:
                conn.send(pickle.dumps([LOGIN_STATUS, True, 1]))  # Registered user with valid password
                set_of_host_name.get(username)[1] = new_port
                set_of_host_name.get(username)[3] = 1
            else:
                conn.send(pickle.dumps([LOGIN_STATUS, True, 0]))  # Registered user with invalid password
        else:
            conn.send(pickle.dumps([LOGIN_STATUS, True, -1]))     # Not registered user
    except Exception as e:
        conn.send(pickle.dumps([LOGIN_STATUS, False]))            # Error
    
def logout(conn, set_of_host_name, username):
    # list_id = len(set_of_lists) + 1 
    try:
        set_of_host_name.get(username)[3] = 0
        conn.send(pickle.dumps([LOGOUT_STATUS, True]))          
    except Exception as e:
        conn.send(pickle.dumps([LOGOUT_STATUS, False]))

def change_password(conn, set_of_host_name, username, old_password, new_password):
    # list_id = len(set_of_lists) + 1 
    try:
        if username in set_of_host_name:
            true_password = set_of_host_name.get(username)[2]
            hashed_old_password = hash_password(old_password)
            hashed_new_password = hash_password(new_password)
            if hashed_old_password == true_password and new_password != old_password:
                conn.send(pickle.dumps([CHANGEPWD_STATUS, True, 2]))        # Successfully change password with new one
                set_of_host_name.get(username)[2] = hashed_new_password
            elif hashed_old_password == true_password and new_password == old_password:
                conn.send(pickle.dumps([CHANGEPWD_STATUS, True, 1]))        # New password is the same as old password
            else:
                conn.send(pickle.dumps([CHANGEPWD_STATUS, True, 0]))        # Old password doesn't match
        else:
            conn.send(pickle.dumps([CHANGEPWD_STATUS, True, -1]))           # Not registered user       
    except Exception as e:
        conn.send(pickle.dumps([CHANGEPWD_STATUS, False]))  

def search(conn,filename, cur_username, setOfInfoFileLists, setOfHostInfo):
    found = False
    return_file = {}
    try:
        for username in setOfInfoFileLists:
            # print(setOfInfoFileLists.get(username))
            if cur_username != username and filename in setOfInfoFileLists.get(username):
                if not found:
                    found = True
                return_file[username] = [setOfHostInfo.get(username)[0],setOfHostInfo.get(username)[1]]
        conn.send(pickle.dumps([SEARCH_STATUS, True, found, return_file]))
    except Exception as e:
        conn.send(pickle.dumps([SEARCH_STATUS, False]))

def publish(conn,set_of_file_lists, username, file_name):  
    # list_id = len(set_of_lists) + 1
    # set_of_host_name[list_id] = host_name
    # set_of_lists[list_id] = filename
    # print(f'"{set_of_lists}","{host_name}"\n')
    # conn.send(pickle.dumps([list_id, True]))
    try:
        if file_name not in set_of_file_lists.get(username):
            set_of_file_lists[username].append(file_name)
        conn.send(pickle.dumps([PUBLISH_STATUS, True]))
    except Exception as e:
        # print(e)
        conn.send(pickle.dumps([PUBLISH_STATUS, False]))

def delete(conn,set_of_file_lists, username, file_name):
    try:
        if file_name in set_of_file_lists.get(username):
            set_of_file_lists[username].remove(file_name)
        conn.send(pickle.dumps([DELETE_STATUS, True]))
    except Exception as e:
        conn.send(pickle.dumps([DELETE_STATUS, False]))

# def get_info(conn,set_of_host_name, username):  
#     try:
#         ip = set_of_host_name.get(username)[0]
#         port = set_of_host_name.get(username)[1]
#         conn.send(pickle.dumps([GET_INFO_STATUS, True, ip, port]))
#     except Exception as e:
#         conn.send(pickle.dumps([GET_INFO_STATUS, False]))