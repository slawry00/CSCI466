# Spencer Lawry
# Been a while since I've used Python...
# 9/22/19
# Networks
# Programming Assignment 1

import sys

def main():
    if len(sys.argv) < 2:
        print("Need command line argument: opp_board = 0, own_board = 1")
    else:
        if sys.argv[1] == '0':
            my_file = open("opponent_board.html", "w")
        elif sys.argv[1] == '1':
            my_file = open("own_board.html", "w")
        else:
            print("Only 0 or 1 are valid inputs")
            exit()

        for i in range(10):
            if i > 0:
                my_file.write("\n")
            for j in range(10):
                my_file.write("_")

if __name__ == "__main__":
    main()
