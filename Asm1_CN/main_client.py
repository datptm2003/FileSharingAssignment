from server.server import *
from peer.peer import *
import psutil

def get_wifi_ip_address():
    target_interface = "Wi-Fi 2"  # Thay thế bằng tên của giao diện WiFi bạn quan tâm
    interfaces = psutil.net_if_addrs()
    for interface, addresses in interfaces.items():
        if interface == target_interface:
            for address in addresses:
                if address.family == socket.AF_INET:
                    return address.address
    return None
if __name__ == '__main__':
    # host = socket.gethostbyname(socket.gethostname())
    host = get_wifi_ip_address()
    if host is None: host = socket.gethostbyname(socket.gethostname())
    port = "8081"
    PORT = "8080"
    HOST = host
    peer = Peer(host, int(port), HOST, int(PORT))
    """
    #Test for ping
    while True:
        peer.respond_ping()
    """
    peer.run()
    
    
         


         

