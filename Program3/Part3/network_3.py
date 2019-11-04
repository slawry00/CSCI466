'''
Created on Oct 12, 2016
@author: mwittie
'''
import queue
import threading


## wrapper class for a queue of packets
class Interface:
    ## @param maxsize - the maximum size of the queue storing packets
    def __init__(self, maxsize=0):
        self.queue = queue.Queue(maxsize);
        self.mtu = None

    ##get packet from the queue interface
    def get(self):
        try:
            return self.queue.get(False)
        except queue.Empty:
            return None

    ##put the packet into the interface queue
    # @param pkt - Packet to be inserted into the queue
    # @param block - if True, block until room in queue, if False may throw queue.Full exception
    def put(self, pkt, block=False):
        self.queue.put(pkt, block)


## Implements a network layer packet (different from the RDT packet:wq

# from programming assignment 2).
# NOTE: This class will need to be extended to for the packet to include
# the fields necessary for the completion of this assignment.
class NetworkPacket:
    ## packet encoding lengths
    dst_addr_S_length = 5
    #orig_addr_S_length = 5 I may need to do this.
    pack_num_length = 1
    more_frag_length = 1
    frag_num_length = 1
    tot_head_length = dst_addr_S_length+pack_num_length+more_frag_length+frag_num_length

    ##@param dst_addr: address of the destination host
    # @param data_S: packet payload
    # @param pack_num: packet identification number. starts at 1
    # @param more_frag: whether there are more frags. 0 = false. 1 = true
    # @param frag_num: fragmentation identification number. starts at 1. 0 means unfragmented
    def __init__(self, dst_addr, data_S, pack_num, more_frag=0, frag_num=0):
        self.dst_addr = dst_addr
        self.data_S = data_S
        self.pack_num = pack_num
        self.more_frag = more_frag
        self.frag_num = frag_num # analogous to fragmentation offset field in IPV4

    ## called when printing the object
    def __str__(self):
        return self.to_byte_S()

    ## convert packet to a byte string for transmission over links
    def to_byte_S(self):
        byte_S = str(self.dst_addr).zfill(self.dst_addr_S_length)
        byte_S += str(self.pack_num)
        byte_S += str(self.more_frag)
        byte_S += str(self.frag_num)
        byte_S += self.data_S
        return byte_S

    ## extract a packet object from a byte string
    # @param byte_S: byte string representation of the packet
    @classmethod
    def from_byte_S(self, byte_S):
        dst_addr = int(byte_S[0 : NetworkPacket.dst_addr_S_length])
        pack_num = int(byte_S[NetworkPacket.dst_addr_S_length :
                              NetworkPacket.dst_addr_S_length + NetworkPacket.pack_num_length])
        more_frag = int(byte_S[NetworkPacket.dst_addr_S_length + NetworkPacket.pack_num_length :
                              NetworkPacket.dst_addr_S_length + NetworkPacket.pack_num_length +
                              NetworkPacket.more_frag_length])
        frag_num = int(byte_S[NetworkPacket.dst_addr_S_length + NetworkPacket.pack_num_length +
                              NetworkPacket.more_frag_length:
                              NetworkPacket.tot_head_length])
        data_S = byte_S[NetworkPacket.tot_head_length: ]
        return self(dst_addr, data_S, pack_num, more_frag, frag_num)




## Implements a network host for receiving and transmitting data
class Host:

    ##@param addr: address of this node represented as an integer
    def __init__(self, addr):
        self.addr = addr
        self.in_intf_L = [Interface()]
        self.out_intf_L = [Interface()]
        self.stop = False #for thread termination
        self.pack_num = 1
        self.frag_buffer = ''

    ## called when printing the object
    def __str__(self):
        return 'Host_%s' % (self.addr)

    # Determine the amount of data that can be sent in each packet for the output interface
    def det_data_size(self, out_interface):
        return out_interface.mtu - NetworkPacket.tot_head_length

    ## create a packet and enqueue for transmission
    # @param dst_addr: destination address for the packet
    # @param data_S: data being transmitted to the network layer
    def udt_send(self, dst_addr, data_S):
        data_size = self.det_data_size(self.out_intf_L[0])
        #for now, we only have 1 outgoing interface

        while len(data_S) > data_size:
            chunk = data_S[:data_size]
            data_S = data_S[data_size:]
            p = NetworkPacket(dst_addr, chunk, self.pack_num)
            self.pack_num += 1
            self.out_intf_L[0].put(p.to_byte_S())
            print('%s: sending packet "%s" on the out interface with mtu=%d' %\
                                       (self, p, self.out_intf_L[0].mtu))

        if len(data_S) > 0: #send the remaining data shorter than data_size
            p = NetworkPacket(dst_addr, data_S, self.pack_num)
            self.pack_num += 1
            self.out_intf_L[0].put(p.to_byte_S()) #send packets always enqueued successfully
            print('%s: sending packet "%s" on the out interface with mtu=%d' %\
                                       (self, p, self.out_intf_L[0].mtu))

    ## receive packet from the network layer
    def udt_receive(self):
        pkt_S = self.in_intf_L[0].get()
        if pkt_S is not None:
            #print('pkt_S is "%s"' % (pkt_S))
            p = NetworkPacket.from_byte_S(pkt_S)
            #print('p is "%s"' % (pkt_S))
            #print('p.frag_num is "%s"' % (p.frag_num))
            #print('p.more_frag is "%s"' % (p.more_frag))
            #print('p.data_S is "%s"' % (p.data_S))

            if p.frag_num != 0: #it is fragmented, we must defragment
                if p.more_frag == 1: # we need to wait for the rest of the fragments
                    self.frag_buffer += p.data_S
                    #print('more_frag ENTERED----self.frag_buffer is %s' % (self.frag_buffer))
                    # add to buffer and wait for more
                else:
                    self.frag_buffer += p.data_S
                    p = NetworkPacket(p.dst_addr, self.frag_buffer, p.pack_num)
                    print('%s: received DEFRAGMENTED packet "%s" on the in interface' % (self, p))
                    #print('more_frag ELSED----self.frag_buffer is %s' % (self.frag_buffer))
                    self.frag_buffer = ''
            else:
                print('%s: received packet "%s" on the in interface' % (self, pkt_S))

    ## thread target for the host to keep receiving data
    def run(self):
        print (threading.currentThread().getName() + ': Starting')
        while True:
            #receive data arriving to the in interface
            self.udt_receive()
            #terminate
            if(self.stop):
                print (threading.currentThread().getName() + ': Ending')
                return



## Implements a multi-interface router described in class
class Router:

    ##@param name: friendly router name for debugging
    # @param intf_count: the number of input and output interfaces
    # @param max_queue_size: max queue length (passed to Interface)
    # @param routing table: the routing table for this router as a Dictionary
    def __init__(self, name, intf_count, max_queue_size, routing_table):
        self.stop = False #for thread termination
        self.name = name
        #create a list of interfaces
        self.in_intf_L = [Interface(max_queue_size) for _ in range(intf_count)]
        self.out_intf_L = [Interface(max_queue_size) for _ in range(intf_count)]
        self.routing_table = routing_table

    ## called when printing the object
    def __str__(self):
        return 'Router_%s' % (self.name)

    ## look through the content of incoming interfaces and forward to
    # appropriate outgoing interfaces
    def forward(self):
        for i in range(len(self.in_intf_L)):
            pkt_S = None
            try:
                #get packet from interface i
                pkt_S = self.in_intf_L[i].get()
                #if packet exists make a forwarding decision
                if pkt_S is not None:
                    p = NetworkPacket.from_byte_S(pkt_S) #parse a packet out
                    input_intf = self.in_intf_L[i]
                    input_mtu = input_intf.mtu
# needs work here still and in simulation routing table definition
                    out_intf_num = int(self.routing_table[str(i)]) 
                    # computes the output port from the routing table. the input port = i
                    # and the output port is given by the value from the dictionary w/ key i
                    output_intf = self.out_intf_L[out_intf_num] 
                    output_mtu = output_intf.mtu
                    if input_mtu > output_mtu:
                        self.fragment_send(p, input_intf, output_intf, i)
                    else:
                        output_intf.put(p.to_byte_S(), True)
                        print('%s: forwarding packet "%s" from interface %d to %d with mtu %d' \
                            % (self, p, i, i, self.out_intf_L[i].mtu))
            except queue.Full:
                print('%s: packet "%s" lost on interface %d' % (self, p, i))
                pass

    # fragments a packet that is too large for the output link
    def fragment_send(self, p, input_intf, output_intf, i):
        out_mtu = output_intf.mtu
        data_len = out_mtu - NetworkPacket.tot_head_length
        p_buff = p.data_S
        frag_num = 0
        while len(p_buff) > data_len:
            frag_data = p_buff[:data_len]
            p_buff = p_buff[data_len:]
            frag_num += 1
            frag_byte_S = str(p.dst_addr).zfill(p.dst_addr_S_length)
            frag_byte_S += str(p.pack_num)
            frag_byte_S += '1'
            frag_byte_S += str(frag_num)
            frag_byte_S += frag_data
            output_intf.put(frag_byte_S, True)
            print('%s: forwarding packet "%s" from interface %d to %d with mtu %d' \
                % (self, frag_byte_S, i, i, out_mtu))

        # last fragment
        frag_data = p_buff
        p_buff = ''
        frag_num += 1
        frag_byte_S = str(p.dst_addr).zfill(p.dst_addr_S_length)
        frag_byte_S += str(p.pack_num)
        frag_byte_S += '0' # last fragment, so more_frag set to 0
        frag_byte_S += str(frag_num)
        frag_byte_S += frag_data
        output_intf.put(frag_byte_S, True)
        print('%s: forwarding packet "%s" from interface %d to %d with mtu %d' \
                % (self, frag_byte_S, i, i, out_mtu))



    ## thread target for the host to keep forwarding data
    def run(self):
        print (threading.currentThread().getName() + ': Starting')
        while True:
            self.forward()
            if self.stop:
                print (threading.currentThread().getName() + ': Ending')
                return
