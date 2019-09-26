# Spencer Lawry & Philip Gales
# 9/22/19
# Networks
# Programming Assignment 1

import http.server, sys, urllib.request, urllib.parse

if len(sys.argv) < 4:
    print("Format: python3 server.py port# board_file_player1 board_file_player2")
    exit()

def main():
    global board_mat1
    global board_mat2
    global cur_mat

    port_num = sys.argv[1]
    if is_num(port_num):
        port_num = int(port_num)
    else:
        print("invalid port_number")
        exit()

    cur_mat = []
    board_mat1 = make_mat(sys.argv[2])
    board_mat2 = make_mat(sys.argv[3])


    # start the server
    try:
        my_server = http.server.HTTPServer(('localhost', port_num), MyHandler)
        my_server.serve_forever() #runs the server indefinitely
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
    fire_spot = cur_mat[y][x] #our matrix is column major
    if fire_spot == 'x':
        return True
    return False

# "fires" at the targeted x,y location on own_board
# returns Tuple of (hit, sink)
# hit: (hit = 0 or 1) --- 0 means miss, 1 means hit
# sink: (sink = 0,C,B,R,S or D) --- 0 means no sink, C = carrier(len of ship=5), B = battleship(4)
# R = cruiser(3), S = submarine(3), D = destroyer(2)
def fire(x,y,p):
    global cur_mat
    fire_spot = cur_mat[y][x] #our matrix is column major
    cur_mat[y][x] = 'x'  # removes the spot from the matrix by replacing it with an 'x'
    update_file(p)
    if fire_spot == '_':
        return (0, 0) #hit = 0, sink = 0 (none)
    else:
        sink = check_sink(fire_spot)
        return (1, sink)

# updates the file using the cur_mat (which holds either board_mat1 or board_mat2 objects)
# by overwritting it with the current board configuration
# returns null
def update_file(player):
    if player == 1:
        opp_file = 3 # they shoot at the opponent board (not their own)
    else:
        opp_file = 2

    with open(sys.argv[opp_file], "w") as board_file:
        for i,row in enumerate(cur_mat):
            if i > 0:
                board_file.write("\n")
            for spot in row:
                board_file.write(spot)

#checks if the hit sank the ship.
# returns (sink = 0,C,B,R,S or D) --- 0 means no sink, C = carrier, B = battleship, R = cruiser,
#S = submarine, D = destroyer
def check_sink(fire_spot):
    sink = fire_spot   # sink is true given by the char that represents that ship type:
    #(C,B,R,S,D), unless the updated file has that char in it
    for row in cur_mat:
        for spot in row:
            if spot == fire_spot:
                sink = 0
    return sink

# returns a string in format from a matrix
def format_file(some_file):
    stream = ""
    stream += '<html>'
    stream += '<body>'
    for i in range(11):
        if i == 0:
            stream += '<span>'
            stream += '</span>'
        else:
            stream += '<span>'
            stream += str(i-1)
            stream += '</span>'
    stream += '<br>'

    with open(some_file, "r") as board:
        for i, row in enumerate(board):
            if i > 0:
                stream += '<br>'
            stream += '<span>'
            stream += str(i)
            stream += '</span>'
            for spot in row:
                stream += '<span>'
                stream += spot
                stream += '</span>'
    stream += '<style>span { width: 16px; display: inline-block;}</style>'
    stream += '</body>'
    stream += '</html>'

    return stream.encode("utf-8")
# Makes the matrix from a file and returns it
def make_mat(some_file):
    mat = []
    with open(some_file, "r") as board:
        for row in board:
            board_row = []
            for spot in row:
                if spot != '\n':
                    board_row.append(spot)
            mat.append(board_row)
    return mat

class MyHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        print(self.requestline)
        mess_type = 200
        if (self.path == "/player1_board.txt"): #lazy "or" formatting here
            req_file = self.path[1:]
        elif (self.path == "/player2_board.txt"):
            req_file = self.path[1:]
        elif (self.path == "/player1_fires.txt"):
            req_file = self.path[1:]
        elif (self.path == "/player2_fires.txt"):
            req_file = self.path[1:]
        elif (self.path == "/favicon.ico"):
            mess_type = 204
        else:
            mess_type = 404

        self.send_response(mess_type)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        if mess_type == 200:
            formed_file = format_file(req_file)
            self.wfile.write(formed_file)

    def do_POST(self):
        global cur_mat
        data = urllib.parse.parse_qs(self.path)

        cond1 = 'p' in data and 'x' in data and 'y' in data
        cond2 = is_num(data['p'][0]) and is_num(data['x'][0]) and is_num(data['y'][0])
        cond3 = data['p'][0] == '1' or data['p'][0] == '2'

        if cond1 and cond2 and cond3:
            player = int(data['p'][0])
            if player == 1:
                cur_mat = board_mat2
            else:
                cur_mat = board_mat1

            x_val = int(data['x'][0])
            y_val = int(data['y'][0])
            mess_type = check_message(x_val,y_val)
            self.send_response(mess_type)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
        else:
            mess_type = 400
            self.send_response(mess_type) #bad request
            self.end_headers()

        if mess_type == 200:
            hit, sink = fire(x_val, y_val, player)
            response_data = urllib.parse.urlencode({'hit':hit, 'sink':sink})
            self.wfile.write(response_data.encode("utf-8"))



if __name__ == "__main__":
    main()
