# Spencer Lawry
# Been a while since I've used Python...
# 9/22/19
# Networks
# Programming Assignment 1

import http.server, sys, urllib.request, urllib.parse

if len(sys.argv) < 3:
    print("Format: python server.py port# own_board.html")
    exit()
else:
    port_num = sys.argv[1]
    board_mat = []
    with open(sys.argv[2], "r") as board:
        for row in board:
            board_row = []
            for spot in row:
                if spot != '\n':
                    board_row.append(spot)
            board_mat.append(board_row)
    for row in board_mat:
        print(row)

#runs the server indefinitely
def run():
    try:
        my_server = http.server.HTTPServer(('localhost', 5000), MyHandler)
        my_server.serve_forever()
    except KeyboardInterrupt:
        print ('^C received, shutting down the web server')
        my_server.socket.close()

#checks if the number can be cast to an int. Returns boolean
def is_num(n):
    try:
        int(n)
        return True
    except ValueError:
        return False

#checks the x,y coordinates of the fire message. Returns the HTTP message code that applies
# if out of bounds, returns HTTP Not Found: 404
# if in redundant location, returns HTTP Gone: 410
# otherwise, returns HTTP OK: 200
def check_message(x,y):
    if not 0 <= x < 10 or not 0 <= y < 10:
        return 404
    elif already_shot():
        return 410
    else:
        return 200


#checks the board for the spots already fired at and returns True if it has already been shot
# otherwise, it returns False
def already_shot():
    return False
# (needs to be implemented)

class MyHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        data = urllib.parse.parse_qs(self.path)
#       print(data)
        if 'x' in data and 'y' in data and is_num(data['x'][0]) and is_num(data['y'][0]):
            x_val = int(data['x'][0])
            y_val = int(data['y'][0])
            mess_type = check_message(x_val,y_val)
            self.send_response(mess_type)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
        else:
            #print("x:{} y:{}".format(x_val,y_val))
            self.send_response(400) #bad request
            self.end_headers()




if __name__ == "__main__":
    run()
