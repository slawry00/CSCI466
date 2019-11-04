import Network2_1
import argparse
from time import sleep
import hashlib

# this was not very readable by default so I made it readable
class Packet:
    ## the number of bytes used to store packet length
    seq_num_S_length = 10
    length_S_length = 10
    ## length of md5 checksum in hex
    checksum_length = 32
    # packet header will include whether it is an ACK, NAK, or just data.
    # ACK = 'A', NAK = 'N'. Every packet will be either 'A' or 'N'
    ACK_length = 1

    def __init__(self, seq_num, msg_S, ACK='A'):
        #print "msg_S = " + msg_S + " and has type: " + str(type(msg_S))
        self.seq_num = seq_num
        self.msg_S = msg_S
        self.ack = ACK
        #print "input ACK = " + str(ACK)
        #print "Made Packet with " + str(self.ack) + "as it's ACK character"

    # takes a data string, puts headers on it, forms the packet, and returns the packet
    @classmethod
    def from_byte_S(self, byte_S):
        #print "entered from_byte_S"
        if Packet.corrupt(byte_S):
            raise RuntimeError('Cannot initialize Packet: byte_S is corrupt')
        #extract the fields
        seq_num = int(byte_S[Packet.length_S_length :
                             Packet.length_S_length +
                             Packet.seq_num_S_length])

        #print "ack is slicing: " + str(Packet.length_S_length + Packet.seq_num_S_length) +" to " +\
                                   #str(Packet.length_S_length + Packet.seq_num_S_length + \
                                   #    Packet.ACK_length)
        #print "remake byte_S = " + byte_S

        ack = byte_S[Packet.length_S_length +
                     Packet.seq_num_S_length :
                     Packet.length_S_length +
                     Packet.seq_num_S_length +
                     Packet.ACK_length]

        #print "ack is: " + ack

        # I added Packet,ACK_length here
        msg_S = byte_S[Packet.length_S_length +
                       Packet.seq_num_S_length +
                       Packet.checksum_length +
                       Packet.ACK_length :]


        return self(seq_num, msg_S, ack)

    # Retrieves the data from the Packet and returns it as a string (byte buffer)
    def get_byte_S(self):
        #print "self.msg_S = " + self.msg_S
        #print "entered get_byte_S"
        #convert sequence number of a byte field of seq_num_S_length bytes
        seq_num_S = str(self.seq_num).zfill(self.seq_num_S_length)

        #convert length to a byte field of length_S_length bytes
        length_S = str(self.length_S_length +
                       len(seq_num_S) +
                       self.checksum_length +
                       self.ACK_length +
                       len(self.msg_S)).zfill(self.length_S_length)

        #compute the checksum
        checksum = hashlib.md5((length_S +
                                seq_num_S +
                                self.ack +
                                self.msg_S).encode('utf-8'))

        checksum_S = checksum.hexdigest()
        #compile into a string
        #print "Returned Packet as string with " + str(self.ack) + " as its ACK character"
        #print "formed original byte_S = " + length_S + seq_num_S + self.ack + checksum_S + self.msg_S

        return length_S + seq_num_S + self.ack + checksum_S + self.msg_S

    @staticmethod
    def corrupt(byte_S):
        #extract the fields
        length_S = byte_S[0:Packet.length_S_length]

        seq_num_S = byte_S[Packet.length_S_length :
                           Packet.seq_num_S_length +
                           Packet.seq_num_S_length]

        checksum_S = byte_S[Packet.seq_num_S_length +
                            Packet.seq_num_S_length +
                            Packet.ACK_length :
                            Packet.seq_num_S_length +
                            Packet.length_S_length +
                            Packet.ACK_length +
                            Packet.checksum_length]
        # add ack_S
        ack_S = byte_S[Packet.length_S_length +
                      Packet.seq_num_S_length :
                      Packet.length_S_length +
                      Packet.seq_num_S_length +
                      Packet.ACK_length]

        msg_S = byte_S[Packet.seq_num_S_length +
                       Packet.seq_num_S_length +
                       Packet.ACK_length +\
                       Packet.checksum_length :]

        #compute the checksum locally
        checksum = hashlib.md5(str(length_S +
                                   seq_num_S +
                                   ack_S +
                                   msg_S).encode('utf-8'))

        computed_checksum_S = checksum.hexdigest()
        #and check if the same
        return checksum_S != computed_checksum_S



class RDT:
    ## latest sequence number used in a packet. Is either 0 or 1
    seq_num = 1
    ## buffer of bytes read from network
    byte_buffer = ''
    # save last packet, so its available for resending
    last_p = None

    def __init__(self, role_S, server_S, port):
        self.network = Network2_1.NetworkLayer(role_S, server_S, port)
        self.role_S = role_S

    def disconnect(self):
        self.network.disconnect()

    def rdt_1_0_send(self, msg_S):
        p = Packet(self.seq_num, msg_S)
        self.seq_num += 1
        self.network.udt_send(p.get_byte_S())

    def rdt_1_0_receive(self):
        ret_S = None
        byte_S = self.network.udt_receive()
        self.byte_buffer += byte_S
        #keep extracting packets - if reordered, could get more than one
        while True:
            #check if we have received enough bytes
            if(len(self.byte_buffer) < Packet.length_S_length):
                return ret_S #not enough bytes to read packet length
            #extract length of packet
            length = int(self.byte_buffer[:Packet.length_S_length])
            if len(self.byte_buffer) < length:
                return ret_S #not enough bytes to read the whole packet
            #create packet from buffer content and add to return string
            p = Packet.from_byte_S(self.byte_buffer[0:length])
            ret_S = p.msg_S if (ret_S is None) else ret_S + p.msg_S
            #remove the packet bytes from the buffer
            self.byte_buffer = self.byte_buffer[length:]
            #if this was the last packet, will return on the next iteration

    def rdt_2_1_send(self, msg_S):
        p = Packet(self.seq_num, msg_S)
        self.seq_num += 1
        self.network.udt_send(p.get_byte_S)
# Keep waiting until we have the proper amount of bytes
        while True:
            # Build up the byte buffer until we get the correct length
            self.byte_buffer += self.network.udt_receive()

            # If we finally have the correct nuber of bytes continue, otherwise keep waiting
            if (len(self.byte_buffer) >= Packet.length_S_length and \
                len(self.byte_buffer) >= int(self.byte_buffer[:Packet.length_S_length])):
                pass
            else:
                # See if we have a corrupted ACK or NACK
                if (Packet.corrupt((self.byte_buffer[:int(self.byte_buffer[:Packet.length_S_length])]))):
                    print("Corrupted ACK or NACK")
                    self.byte_buffer = self.byte_buffer[int(self.byte_buffer[:Packet.length_S_length]):]
                    self.network.udt_send(p.get_byte_S, True)
                else:
                    response = Packet.from_byte_S(self.byte_buffer[:int( \
                                                self.byte_buffer[:Packet.length_S_length])])
                    self.byte_buffer = self.byte_buffer[int(self.byte_buffer[:Packet.length_S_length]):]

                    # We got the wrong one and need to send again
                    if response.seq_num != self.seq_num:
                        print("Wrong order")
                        ack = Packet(response.seq_num, "1")
                        self.network.udt_send(ack.get_byte_S, True)

                    # Resend if a NACK otherwise increment sequence number
                    if (response.seq_num == self.seq_num):
                        if response.msg_S == "0":
                            print("This response was a NACK")
                            self.network.udt_send(p.get_byte_S, True)
                        elif response.msg_S == "1":
                            print("This response was a ACK")
                            self.seq_num += 1
                            break

    def rdt_2_1_receive(self):
        ret_S = None
        byte_S = self.network.udt_receive()
        self.byte_buffer += byte_S
        # Keep waiting until we have the proper amount of bytes
        while True:

            # See if we received the correct number of bytes (10 as the default)
            if (len(self.byte_buffer) < Packet.length_S_length or len(self.byte_buffer) < \
                                            int(self.byte_buffer[:Packet.length_S_length])):
                break

            #This packet is corrupt so send a NACK
            elif (Packet.corrupt((self.byte_buffer[:int(self.byte_buffer[:Packet.length_S_length])]))):
                print("This message is a NACK")
                self.network.udt_send(Packet(self.seq_num, "0").get_byte_S, False)
            else:
                # Get the data and prepare to return the message
                print("This message is a ACK")
                p = Packet.from_byte_S(self.byte_buffer[:int(self.byte_buffer[:Packet.length_S_length])])

                # Send the ACK and increase sequence number

                if (p.seq_num == self.seq_num):
                    ack = Packet(self.seq_num, "1")
                    self.seq_num += 1
                    self.network.udt_send(ack.get_byte_S, False)
                # We got the wrong one and need to send again
                else:
                    self.network.udt_send(Packet(p.seq_num, "1").get_byte_S, False)

                # Build up the return message
                if (ret_S is None):
                    ret_S = p.msg_S
                else:
                    ret_S += p.msg_S

            # Reset the byte buffer
            self.byte_buffer = self.byte_buffer[int(self.byte_buffer[:Packet.length_S_length]):]

        return ret_S

    def rdt_3_0_send(self, msg_S):
    # biting until we have the proper amount of bytes
        pass

    def rdt_3_0_receive(self):
        pass


if __name__ == '__main__':
    parser =  argparse.ArgumentParser(description='RDT implementation.')
    parser.add_argument('role', help='Role is either client or server.', choices=['client', 'server'])
    parser.add_argument('server', help='Server.')
    parser.add_argument('port', help='Port.', type=int)
    args = parser.parse_args()

    rdt = RDT(args.role, args.server, args.port)
    if args.role == 'client':
        rdt.rdt_1_0_send('MSG_FROM_CLIENT')
        sleep(2)
        print(rdt.rdt_1_0_receive())
        rdt.disconnect()


    else:
        sleep(1)
        print(rdt.rdt_1_0_receive())
        rdt.rdt_1_0_send('MSG_FROM_SERVER')
        rdt.disconnect()

