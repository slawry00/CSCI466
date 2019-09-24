# Spencer Lawry
# Been a while since I've used Python...
# 9/22/19
# Networks
# Programming Assignment 1

import sys

def main():
    if len(sys.argv) < 2:
        print("Need command line argument: player1_fires = 1, player2_fires = 2")
    else:
        if sys.argv[1] == '1':
            my_file = open("player1_fires.txt", "w")
        elif sys.argv[1] == '2':
            my_file = open("player2_fires.txt", "w")
        else:
            print("Only 1 or 2 are valid inputs")
            exit()

        for i in range(10):
            if i > 0:
                my_file.write("\n")
            for j in range(10):
                my_file.write("_")

if __name__ == "__main__":
    main()
