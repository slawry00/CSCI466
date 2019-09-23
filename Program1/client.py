# Spencer Lawry
# Been a while since I've used Python...
# 9/22/19
# Networks
# Programming Assignment 1

import http.client, sys, urllib
def main():
    if len(sys.argv) < 5:
        print("Format: python client.py server_ip_address port# X Y")
        exit()
    else:
        server_ip = sys.argv[1]
        port_num = sys.argv[2]
        x_coord = sys.argv[3]
        y_coord = sys.argv[4]

    data = urllib.parse.urlencode({'x':x_coord, 'y':y_coord})
    conn = http.client.HTTPConnection(server_ip, port_num)
    conn.request("POST", data)
    r1 = conn.getresponse()
    print(r1.status, r1.reason)



if __name__ == "__main__":
    main()
