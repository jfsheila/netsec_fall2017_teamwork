from asyncio import *
import playground
from HandShakePacket import HsPkt
from playground.network.packet import PacketType
from playground.network.common import PlaygroundAddress
from playground.network.common import StackingProtocolFactory
from playground.network.common import StackingProtocol
from playground.network.common import StackingTransport
import random
import time

class TranCliProto(StackingProtocol):
    def __init__(self):
        '''
            Init TranCliProto: 
            self.RecSeq is to record sequential number from Server
            self.Status is to record protocol status Activated or InActivated 
            checking for the handshake processing
            
        '''
        self.transport = None
        self.Status = "InActivated"
        self.RecSeq = 0
        self.SenSeq = 0
        self.higherTransport = None
        self.deserializer = PacketType.Deserializer()

    def connection_made(self, transport):
        print("Client: TranCliProto Connection made")
        self.transport = transport
        self.higherTransport = StackingTransport(self.transport)
        self.connection_request()
        
        

    def data_received(self, data):
        self.deserializer.update(data)
        for pkt in self.deserializer.nextPackets():
            if self.Status=="InActivated":
                if pkt.Type==1 and pkt.Acknowledgement == (self.SenSeq + 1):
                    print("Client: Ack+Syn received!")
                    self.RecSeq = pkt.SequenceNumber
                    AckPkt = HsPkt()
                    AckPkt.Type = 2
                    AckPkt.Checksum = 0
                    AckPkt.SequenceNumber =0
                    AckPkt.Acknowledgement = self.RecSeq+1
                    self.transport.write(AckPkt.__serialize__())
                    print("Client: Ack sent!")
                    self.Status = "Activated"
                    time.sleep(3)                   #test area!!
                    self.close_request()    
                    self.higherProtocol().connection_made(self.higherTransport)
                    
                
                
                    
                else:
                    self.transport.close()
            elif self.Status == "Activated":
                
                '''
                    Protocol Activated Transport data HERE!
                '''
                
            elif self.Status == "HalfActivated":
                if pkt.Type == 3:
                    print("Client: Rip from server received!")
                    self.RecSeq = pkt.SequenceNumber  
                    clientRip = HsPkt()
                    clientRip.Type=4
                    clientRip.Checksum=0
                    clientRip.SequenceNumber = 0
                    self.RecSeq+=1
                    clientRip.Acknowledgement = self.RecSeq
                    self.transport.write(clientRip.__serialize__())
                    self.connection_lost("End")
                elif pkt.Type == 4 and pkt.Acknowledgement == self.SenSeq+1:       # RIP-ACK
                    '''
                        Stop sendind data and WAIT!
                    '''        
                    print("Client: Waiting for Server close the transport!")
                   
    def connection_request(self):
        print("Client: Connection Request sent!")
        handshakeRequest = HsPkt()
        handshakeRequest.Type = 0
        handshakeRequest.Acknowledgement = 0
        handshakeRequest.SequenceNumber = random.randint(0,99)   #currently the range is [0,99]
        handshakeRequest.Checksum = 0          # have to be improved in the future
        self.SenSeq = handshakeRequest.SequenceNumber
        self.transport.write(handshakeRequest.__serialize__())
        
    
    def close_request(self):
        '''
            Close higher level transportation!
        '''
        print("Client: Rip request sent!")
        closePacket = HsPkt()
        closePacket.Type = 3
        self.SenSeq+=1
        closePacket.SequenceNumber = self.SenSeq
        closePacket.Acknowledgement = 0
        closePacket.Checksum = 0
        self.Status = "HalfActivated"
        self.transport.write(closePacket.__serialize__())
    
    
    def connection_lost(self, exc):
        self.transport.close()
        self.higherProtocol().connection_lost(exc)
        print("Connection stop because {}".format(exc))
