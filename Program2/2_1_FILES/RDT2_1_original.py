import Network2_1
import argparse
from time import sleep
import hashlib

# this was not very readable by default so I made it readable
class Packet:
    # the number of bytes used to store packet length
    seq_num_S_length = 10
    length_S_length = 10
    # length of md5 checksum in hex
    checksum_length = 32
    # packet header will include whether it is an ACK or NAK
    # ACK = 'A', NAK = 'N'. Every packet will be either 'A' or 'N'
    ACK_length = 1

    def __init__(self, seq_num, msg_S, ACK='A'):
        self.seq_num = seq_num
        self.msg_S = msg_S
        self.ack = ACK

    # takes a data string, puts headers on it, forms the packet, and returns the packet
    @classmethod
    def from_byte_S(self, byte_S):
        if Packet.corrupt(byte_S):
            raise RuntimeError('Cannot initialize Packet: byte_S is corrupt')
        #extract the fields
        seq_num = int(byte_S[Packet.length_S_length :
                             Packet.length_S_length +
                             Packet.seq_num_S_length])

        ack = byte_S[Packet.length_S_length +
                     Packet.seq_num_S_length :
                     Packet.length_S_length +
                     Packet.seq_num_S_length +
                     Packet.ACK_length]

        msg_S = byte_S[Packet.length_S_length +
                       Packet.seq_num_S_length +
                       Packet.checksum_length +
                       Packet.ACK_length :]


        return self(seq_num, msg_S, ack)

    # Retrieves the data from the Packet and returns it as a string (byte buffer)
    def get_byte_S(self):
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

    # if it is the server, it sends NAK. If it is the client, it resends last packet
    # server executes this if it receives corrupt data
    # client executes this if it receives corrupt data or NAK
    def role_play(self, role):
        if (role == 'server'):
            self.rdt_2_1_send('', 'N')
        else:
            self.rdt_2_1_send(self.last_p.msg_S)

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

    # by default, it is an ACK('A')
    def rdt_2_1_send(self, msg_S, ACK='A'):
        #print "entered rdt_2_1_send"
        p = Packet(self.seq_num, msg_S, ACK)
        self.network.udt_send(p.get_byte_S())

        # we dont want to resend empty NAK packets
        if (ACK == 'A'):
            self.last_p = p
        self.seq_num = (self.seq_num+1)%2 # either 0 or 1, so mod by 2


    def rdt_2_1_receive(self):
        ret_S = None
        byte_S = self.network.udt_receive()
        self.byte_buffer += byte_S
        #keep extracting packets - if reordered, could get more than one
        while True:
            #check if we have received enough bytes
            if(len(self.byte_buffer) < Packet.length_S_length):
                return ret_S
            #extract length of packet
            length = int(self.byte_buffer[:Packet.length_S_length])
            if len(self.byte_buffer) < length:
                return ret_S
            # if it is corrupted handle it with role_play and throw away data
            if (Packet.corrupt(self.byte_buffer[0:length])):
                self.role_play(self.role_S)
                self.byte_buffer = self.byte_buffer[length:]
                return ret_S

            # so we have an uncorrupted, full length packet, make it a Packet again
            p = Packet.from_byte_S(self.byte_buffer[0:length])

            # only client can receive NAK, resend last packet and throw away corrupt data
            if (p.ack == 'N'):
                self.role_play(self.role_S)
                self.byte_buffer = self.byte_buffer[length:]
                return ret_S

            # get the sequence number of the received packet (which is the ack num)
            ack_num = p.seq_num

            # duplicate packet from client, but client must have received corrupt server response
            # so server sends response again, but throws away the data itself
            if (ack_num != self.seq_num):
                self.rdt_2_1_send(self.last_p.msg_S)
                self.byte_buffer = self.byte_buffer[length:]
                return ret_S

            # only gets to this point if it is not corrupt, not a nak, and not a duplicate
            # therefore it is a good packet, increment seq_num, and pass up to APP layer
            self.seq_num = (self.seq_num+1)%2 # either 0 or 1, so mod by 2
            if (ret_S is None):
                ret_S =  p.msg_S
            else:
                ret_S = ret_S + p.msg_S # I dont think this ever happens

            # remove Packet data from buffer
            self.byte_buffer = self.byte_buffer[length:]

    def rdt_3_0_send(self, msg_S):
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

