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

def main():
    # Setup
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

    fire_mat = make_fire_mat(fire_file)

    # Send
    data = urllib.parse.urlencode({'p':player,'x':x_coord, 'y':y_coord})
    conn = http.client.HTTPConnection(server_ip, port_num)
    conn.request("POST", data)
    r1 = conn.getresponse()
    print("HEADER RESPONSE: ", r1.status, r1.reason)
    if r1.status == 200:
        res_data = r1.read().decode("utf-8")
        print("HIT/MISS RESPONSE: ", res_data)
        res_data_dics = urllib.parse.parse_qs(res_data)
        hit = int(res_data_dics["hit"][0])
        sink = res_data_dics["sink"][0]
        if hit:
            print("HIT AT ({},{})".format(x_coord, y_coord))
            if sink != '0':
                print("AND {} SANK".format(sink))

        else:
            print("Miss at ({},{})".format(x_coord, y_coord))

        update_mat(fire_mat, int(x_coord), int(y_coord), hit, sink)
        update_file(fire_file, fire_mat)
    print_board(fire_mat)

# Makes the matrix from the file and returns it
def make_fire_mat(fire_file):
    mat = []
    with open(fire_file, "r") as board:
        for row in board:
            board_row = []
            for spot in row:
                if spot != '\n':
                    board_row.append(spot)
            mat.append(board_row)
    return mat


# updates the matrix (modifies it) with new spot given the matrix to update, the x,y coords,
# the hit (0=miss or 1=hit), and the sank boat char ('0' if no sink)
def update_mat(mat, x, y, hit, sank):
    if hit:
        if sank != '0':
            mat[y][x] = sank
        else:
            mat[y][x] = 'x'
    else:
        mat[y][x] = 'o'

# remakes the file from the matrix
def update_file(fire_file, mat):
    with open(fire_file, "w") as board_file:
        for i,row in enumerate(mat):
            if i > 0:
                board_file.write("\n")
            for spot in row:
                board_file.write(spot)

# prints the player fire record board from the matrix
def print_board(mat):
    print()
    print(" ", end=" ")
    for i in range(10):
        print(i, end=" ")
    print()

    for i, row in enumerate(mat):
        if i > 0:
            print()
        print(i, end=" ")
        for spot in row:
            print(spot, end=" ")
    print()

if __name__ == "__main__":
    main()
