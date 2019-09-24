# Spencer Lawry
# Been a while since I've used Python...
# 9/22/19
# Networks
# Programming Assignment 1

import http.client, sys, urllib

if len(sys.argv) < 6:
    print("Format: python3 client.py server_ip_address port# player# X Y")
    print("player# must be either 1 or 2")
    exit()
else:
    server_ip = sys.argv[1]
    port_num = sys.argv[2]
    player = sys.argv[3]
    x_coord = sys.argv[4]
    y_coord = sys.argv[5]

    if player == '1':
        fire_file = "player1_fires.txt"
    elif player == '2':
        fire_file = "player2_fires.txt"
    else:
        print("Player number was not inputted correctly. Type: python3 client.py for directions")
        exit()
    fire_mat = []

def send():
    data = urllib.parse.urlencode({'p':player,'x':x_coord, 'y':y_coord})
    conn = http.client.HTTPConnection(server_ip, port_num)
    conn.request("POST", data)
    r1 = conn.getresponse()
    print(r1.status, r1.reason)
    if r1.status == 200:
        res_data = r1.read().decode("utf-8")
        res_data_dics = urllib.parse.parse_qs(res_data)
        hit = int(res_data_dics["hit"][0])
        sink = res_data_dics["sink"][0]
        if hit:
            print("HIT AT ({},{})".format(x_coord, y_coord))
            if sink != '0':
                print("AND {} SANK".format(sink))

        else:
            print("Miss at ({},{})".format(x_coord, y_coord))

        update_mat(hit,sink)
        update_file()
    print_board()

# Makes the fire_matrix from the fire_file
def make_fire_mat():
    global fire_mat
    with open(fire_file, "r") as board:
        for row in board:
            board_row = []
            for spot in row:
                if spot != '\n':
                    board_row.append(spot)
            fire_mat.append(board_row)


def update_mat(hit, sank):
    global fire_mat
    x = int(x_coord)
    y = int(y_coord)
    if hit:
        if sank != '0':
            fire_mat[y][x] = sank
        else:
            fire_mat[y][x] = 'x'
    else:
        fire_mat[y][x] = 'o'

# updates the player#_fires.txt file with the new fire location
def update_file():
    global fire_file
    with open(fire_file, "w") as board_file:
        for i,row in enumerate(fire_mat):
            if i > 0:
                board_file.write("\n")
            for spot in row:
                board_file.write(spot)

# prints the player fire record board
def print_board():
    print()
    print(" ", end=" ")
    for i in range(10):
        print(i, end=" ")
    print()

    for i, row in enumerate(fire_mat):
        if i > 0:
            print()
        print(i, end=" ")
        for spot in row:
            print(spot, end=" ")
    print()

if __name__ == "__main__":
    make_fire_mat()
    send()
