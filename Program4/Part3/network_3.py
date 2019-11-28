import queue
import threading


## wrapper class for a queue of packets
class Interface:
    ## @param maxsize - the maximum size of the queue storing packets
    def __init__(self, maxsize=0):
        self.in_queue = queue.Queue(maxsize)
        self.out_queue = queue.Queue(maxsize)

    ##get packet from the queue interface
    # @param in_or_out - use 'in' or 'out' interface
    def get(self, in_or_out):
        try:
            if in_or_out == 'in':
                pkt_S = self.in_queue.get(False)
                # if pkt_S is not None:
                #     print('getting packet from the IN queue')
                return pkt_S
            else:
                pkt_S = self.out_queue.get(False)
                # if pkt_S is not None:
                #     print('getting packet from the OUT queue')
                return pkt_S
        except queue.Empty:
            return None

    ##put the packet into the interface queue
    # @param pkt - Packet to be inserted into the queue
    # @param in_or_out - use 'in' or 'out' interface
    # @param block - if True, block until room in queue, if False may throw queue.Full exception
    def put(self, pkt, in_or_out, block=False):
        if in_or_out == 'out':
            # print('putting packet in the OUT queue')
            self.out_queue.put(pkt, block)
        else:
            # print('putting packet in the IN queue')
            self.in_queue.put(pkt, block)


## Implements a network layer packet.
class NetworkPacket:
    ## packet encoding lengths
    dst_S_length = 5
    prot_S_length = 1

    ## router control data lengths
    r_name_len = 2
    dest_len = 2
    node_len = 2
    cost_len = 5

    ##@param dst: address of the destination host
    # @param data_S: packet payload
    # @param prot_S: upper layer protocol for the packet (data, or control)
    def __init__(self, dst, prot_S, data_S):
        self.dst = dst
        self.data_S = data_S
        self.prot_S = prot_S

    ## called when printing the object
    def __str__(self):
        return self.to_byte_S()

    ## convert packet to a byte string for transmission over links
    def to_byte_S(self):
        byte_S = str(self.dst).zfill(self.dst_S_length)
        if self.prot_S == 'data':
            byte_S += '1'
        elif self.prot_S == 'control':
            byte_S += '2'
        else:
            raise('%s: unknown prot_S option: %s' %(self, self.prot_S))
        byte_S += self.data_S
        return byte_S

    ## extract a packet object from a byte string
    # @param byte_S: byte string representation of the packet
    @classmethod
    def from_byte_S(self, byte_S):
        dst = byte_S[0 : NetworkPacket.dst_S_length].strip('0')
        prot_S = byte_S[NetworkPacket.dst_S_length : NetworkPacket.dst_S_length + NetworkPacket.prot_S_length]
        if prot_S == '1':
            prot_S = 'data'
        elif prot_S == '2':
            prot_S = 'control'
        else:
            raise('%s: unknown prot_S field: %s' %(self, prot_S))
        data_S = byte_S[NetworkPacket.dst_S_length + NetworkPacket.prot_S_length : ]
        return self(dst, prot_S, data_S)
    #creates a routing table data message(string) from a routing table (dict)
    def create_rout_mess(self, r_name, rtab):
        mess = ''
        for dest in rtab:
            node = rtab.get(dest)[0]
            cost = rtab.get(dest)[1]

            mess += str(r_name)
            mess += str(dest)
            mess += str(node)
            mess += str(cost).zfill(self.cost_len)

        return mess

    # turns the network control packet back into a {dest : (router,cost)} as in rt_tbl_D
    def decode_rout_mess(self):
        mess = self.to_byte_S()[self.dst_S_length + self.prot_S_length :]
        tot_len = self.r_name_len + self.dest_len + self.node_len + self.cost_len
        tot_dict = {mess[0:self.r_name_len]:
                   {mess[self.r_name_len:self.r_name_len+self.dest_len] :
                   (mess[self.r_name_len+self.dest_len:self.r_name_len+self.dest_len+self.node_len],
                    int(mess[self.r_name_len+self.dest_len+self.node_len:tot_len]))}}
        mess = mess[tot_len:]

        while len(mess) > 0: #continues adding additional dest : (router, cost) tuples
            new_key = mess[0:self.r_name_len]
            next_dest = mess[self.r_name_len:self.r_name_len+self.dest_len]
            tot_dict[new_key][next_dest] = (mess[self.r_name_len+self.dest_len:
                                            self.r_name_len+self.dest_len+self.node_len],
                                            int(mess[self.r_name_len+self.dest_len+self.node_len:
                                            tot_len]))
            mess = mess[tot_len:]
        return tot_dict


## Implements a network host for receiving and transmitting data
class Host:

    ##@param addr: address of this node represented as an integer
    def __init__(self, addr):
        self.addr = addr
        self.intf_L = [Interface()]
        self.stop = False #for thread termination

    ## called when printing the object
    def __str__(self):
        return self.addr

    ## create a packet and enqueue for transmission
    # @param dst: destination address for the packet
    # @param data_S: data being transmitted to the network layer
    def udt_send(self, dst, data_S):
        p = NetworkPacket(dst, 'data', data_S)
        print('%s: sending packet "%s"' % (self, p))
        self.intf_L[0].put(p.to_byte_S(), 'out') #send packets always enqueued successfully

    ## receive packet from the network layer
    def udt_receive(self):
        pkt_S = self.intf_L[0].get('in')
        if pkt_S is not None:
            print('%s: received packet "%s"' % (self, pkt_S))

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



## Implements a multi-interface router
class Router:

    ##@param name: friendly router name for debugging
    # @param cost_D: cost table to neighbors {neighbor: {interface: cost}}
    # @param max_queue_size: max queue length (passed to Interface)
    def __init__(self, name, cost_D, max_queue_size):
        self.stop = False #for thread termination
        self.name = name
        #create a list of interfaces
        self.intf_L = [Interface(max_queue_size) for _ in range(len(cost_D))]
        #save neighbors and interfeces on which we connect to them
        self.cost_D = cost_D    # {neighbor: {interface: cost}}
        self.change_count = 2 # Threads are unreliable -> send updates twice
        new_dict = {}
        for dest in cost_D:
            for intf in cost_D[dest]:
                new_dict[dest] = (dest, cost_D[dest].get(intf))
                # here the routing table is initialized with this router's neighbors
        new_dict[self.name] = (self.name, 0)
        self.rt_tbl_D = {self.name : new_dict}
        # so now we have {src_router :{destination : (fwd_node, cost)}} dict(dict(tuple))
        # and it holds the routing tables of its own and also neighboring routers
        self.send_routes()
        print('%s: Initialized routing table' % self)
        self.print_routes()


    ## Print routing table
    def print_routes(self):
        dest_len = 0
        max_router = self.name #router with most known dests
        for router in self.rt_tbl_D:
            num_dests = len(self.rt_tbl_D[router])+1
            if num_dests > dest_len:
                dest_len = num_dests
                max_router = router
        print('='*(7*dest_len))
        print('|' + self.name.ljust(5, ' ') + '|', end = '')
        for dest in self.rt_tbl_D[max_router]:
            print(dest.rjust(6, ' ') + '|', end = '')
        print('\n'+'='*(7*dest_len), end = '')
        for router in self.rt_tbl_D:
            print('\n|' + router.ljust(5, ' ') + '|', end = '')
            for dest in self.rt_tbl_D[max_router]:
                if router in self.rt_tbl_D and dest in self.rt_tbl_D.get(router):
                    cost = self.rt_tbl_D.get(router).get(dest)[1]
                    print(str(cost).rjust(6, ' ') + '|', end = '')
                else:
                    print(''.rjust(6, ' ') + '|', end = '')
        print('\n'+'='*(7*dest_len))



    ## called when printing the object
    def __str__(self):
        return self.name


    ## look through the content of incoming interfaces and
    # process data and control packets
    def process_queues(self):
        for i in range(len(self.intf_L)):
            pkt_S = None
            #get packet from interface i
            pkt_S = self.intf_L[i].get('in')
            #if packet exists make a forwarding decision
            if pkt_S is not None:
                p = NetworkPacket.from_byte_S(pkt_S) #parse a packet out
                if p.prot_S == 'data':
                    self.forward_packet(p,i)
                elif p.prot_S == 'control':
                    self.update_routes(p, i)
                else:
                    raise Exception('%s: Unknown packet type in packet %s' % (self, p))


    ## forward the packet according to the routing table
    #  @param p Packet to forward
    #  @param i Incoming interface number for packet p
    def forward_packet(self, p, i):
        try:
            out_name = self.rt_tbl_D[self.name][p.dst][0]
            for intf in self.cost_D[out_name]: # have to access single entry from dictionary...
                out_intf = intf

            self.intf_L[out_intf].put(p.to_byte_S(), 'out', True)
            print('%s: forwarding packet "%s" from interface %d to %d' % \
                (self, p, i, 1))
        except queue.Full:
            print('%s: packet "%s" lost on interface %d' % (self, p, i))
            pass


    ## send out route update
    def send_routes(self):
        for neighbor in self.cost_D:
            if neighbor[0] == 'R': # if it's a router
                for i in self.cost_D[neighbor]: #only 1 intf in {intf : cost}
                    rout_dict = self.rt_tbl_D[self.name] # only have to send its own
                    rtable = NetworkPacket.create_rout_mess(NetworkPacket, self.name, rout_dict)
                    p = NetworkPacket(i, 'control', rtable)
                    try:
                        print('%s: sending routing update "%s" from interface %d' % (self, p, i))
                        self.intf_L[i].put(p.to_byte_S(), 'out', True)
                    except queue.Full:
                        print('%s: packet "%s" lost on interface %d' % (self, p, i))
                        pass


    ## forward the packet according to the routing table
    #  @param p Packet containing routing information
    def update_routes(self, p, i):
        rec_rtable = p.decode_rout_mess()
        if rec_rtable != self.rt_tbl_D:
            print('%s: Received routing update %s from interface %d' % (self, p, i))
            for router in rec_rtable:
                if router != self.name:
                    for dest in rec_rtable[router]:
                        node = rec_rtable[router][dest][0]
                        rec_cost = rec_rtable[router][dest][1]
                        if router in self.rt_tbl_D and dest in self.rt_tbl_D.get(router):
                            cur_cost_tup = self.rt_tbl_D.get(router).get(dest)
                            if cur_cost_tup[1] > rec_cost:
                                self.rt_tbl_D[router] = {dest : (node, rec_cost)}
                        else: # either router or dest not in table yet--- add it
                            if router in self.rt_tbl_D:
                                self.rt_tbl_D[router][dest] = (node, rec_cost)
                            else:
                                self.rt_tbl_D[router] = {dest : (node, rec_cost)}

            changed = False
            # now we check Bellman-Ford equation
            for router in self.rt_tbl_D:
                if router != self.name and router in self.cost_D: #neighboring router
                    cost_to_oth = self.rt_tbl_D[self.name][router][1]
                    for dest in self.rt_tbl_D[router]:
                        oth_cost = self.rt_tbl_D[router][dest][1]
                        if dest in self.rt_tbl_D[self.name]:
                            cur_cost = self.rt_tbl_D[self.name][dest][1]
                        else:
                            cur_cost = 9999
                        if cost_to_oth + oth_cost < cur_cost:
                            self.rt_tbl_D[self.name][dest] = (router, cost_to_oth + oth_cost)
                            changed = True
            if changed:
                self.change_count = 2
                self.send_routes()
            else: # this is so bad thread timing doesn't mess up the result
                self.change_count -= 1
                if self.change_count > 0:
                    self.send_routes()


    ## thread target for the host to keep forwarding data
    def run(self):
        print (threading.currentThread().getName() + ': Starting')
        while True:
            self.process_queues()
            if self.stop:
                print (threading.currentThread().getName() + ': Ending')
                return
