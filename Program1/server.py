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

    print (board_mat[2][2])

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
    elif already_shot(x,y):
        return 410
    else:
        return 200


#checks the board for the spots already fired at and returns True if it has already been shot
# otherwise, it returns False
def already_shot(x,y):
    fire_spot = board_mat[y][x] #our matrix is column major
    if fire_spot == 'x':
        return True
    return False

# "fires" at the targeted x,y location on own_board
# returns Tuple of (hit, sink) 
# hit: (hit = 0 or 1) --- 0 means miss, 1 means hit
# sink: (sink = 0,C,B,R,S or D) --- 0 means no sink, C = carrier(len of ship=5), B = battleship(4), R = cruiser(3), S = submarine(3), D = destroyer(2)
def fire(x,y):
    fire_spot = board_mat[y][x] #our matrix is column major
    board_mat[y][x] = 'x'  # removes the spot from the matrix by replacing it with an 'x'
    update_file()
    if fire_spot == '_':
        return (0, 0) #hit = 0, sink = 0 (none)
    else:
        sink = check_sink(fire_spot)
        return (1, sink)

# updates the file from the board_mat global variable by overwritting it with the current board
# returns null
def update_file():
    with open(sys.argv[2], "w") as board_file:
        for i,row in enumerate(board_mat):
            if i > 0:
                board_file.write("\n")
            for spot in row:
                board_file.write(spot)

    for row in board_mat:
        print(row)

#checks if the hit sank the ship.
# returns (sink = 0,C,B,R,S or D) --- 0 means no sink, C = carrier, B = battleship, R = cruiser, S = submarine, D = destroyer
def check_sink(fire_spot):
    sink = fire_spot   # sink is true given by the char that represents that ship type: (C,B,R,S,D), unless the updated file has that char in it
    for row in board_mat:
        for spot in board_mat:
            if spot == fire_spot:
                sink = 0
    return sink

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
            mess_type = 400
            self.send_response(mess_type) #bad request
            self.end_headers()

        if mess_type == 200:
            fire(x_val, y_val)



if __name__ == "__main__":
    run()
