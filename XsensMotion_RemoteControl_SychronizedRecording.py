import socket
import struct
import moticon_insole3.proto.service.service_pb2 as proto_s
import numpy as np
import os
from pathlib import Path


class ConnectionClosed(Exception):
    pass


def run_recording():
    # Create a TCP/IP socket
    sock_insole = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # sock_xsens = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Create a UDP socket (for xsens remote control)
    sock_xsens_reco = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Define the server name of the Moticon App and Qualysis computer
    # This needs to be confirmed after each experiment setup, since the IP address
    # may change
    
    # Ip address & port of Moticon insole (Find this in the Moticon Phone App)
    # The smartphone needs to join the subnetwork of the Xsens router 'AP_Bodypack'
    #server_name_insole = "192.168.1.197"
    server_name_insole = ""
    port_insole = 9999
    
    # IP address & port for the remote control of Xsens MVN. IP address is the
    # address of the Qualisys computer under the USB connection with the Xsens
    # router. The port number is at the MVN software 'Options/Remote control'
    client_name_xsens = "192.168.1.8"
    port_reco_xsens = 6004
    
    # build the insole socket and listen to server
    server_address_insole = (server_name_insole, port_insole)
    print ('insole connection starting up on {} port {}'.format(server_name_insole, port_insole))
    sock_insole.bind(server_address_insole)
    sock_insole.listen(1)
    
    saving_numb = 1  # initialize savng trial number as 1

    while True:
        
        # file names for saving, trial number will automatically add one for each repeated trial
        # to avoid over-writig. It is suggested to rename saved trials right after each recording.
        insole_text_name = "../Test13102021/Insole/data_insole_trial"\
            + str(saving_numb) + ".txt"  # text file for insole data saving
            
        # empty the variables for saving next trial's data
        data_insole_store = []
        
        # Connect to Moticon insoles
        print('Moticon insoles waiting for a connection')
        connection_insole, client_address_insole = sock_insole.accept()
        
        client_address_xsens_reco = (client_name_xsens, port_reco_xsens)
        print ('Xsesn remote control connecting up on {} port {}'.format(client_name_xsens, port_reco_xsens))
        sock_xsens_reco.connect(client_address_xsens_reco)
        
        frame_counter = 0
        
        try:
            print('client connected: {}'.format(client_address_insole))
            
            sock_xsens_reco.send('<StartRecordingReq>'.encode("utf8"))
            print('Xsens MVN recording started')  # Connect to Xsesn MVN
            

            while True:
                
                try:
                    # read insole socket data
                    msg_buf_insole = get_message_insole(connection_insole)
                    
                except ConnectionClosed as e:
                    print(e)
                    break
    
                # start xsens recording and save data after the insole's header line
                if frame_counter < 5:
                    
                    # data_insole_header_store.append(msg_insole) # don't save the insole header
                    
                    # start the MVN recording, if the insole head frames are over
                    # if frame_counter == 4:
                        
                    frame_counter = frame_counter + 1  # count increase until 5
                    
                else:

                    # parse the insole data and save it to file
                    msg_insole = proto_s.MoticonMessage()
                    msg_insole.ParseFromString(msg_buf_insole)
                    
                    saving_data = extract_insole_data(msg_insole)

                    # store the insole
                    data_insole_store.append(saving_data)

        finally:
            # Stop the MVN recording
            sock_xsens_reco.send('<StopRecordingReq>'.encode("utf8"))
            
            # save data
            insole_data_save(insole_text_name, data_insole_store)
            
            
            saving_numb += 1  # trial number + 1, automatically
            
            # close connections
            connection_insole.close()


def get_message_insole(conn_insole):
    """Read a message from a socket, taking care of message framing."""
    len_buf = socket_read_n(conn_insole, 2)
    msg_len = struct.unpack('>H', len_buf)[0]
    msg_buf = socket_read_n(conn_insole, msg_len)
    return msg_buf
    
def socket_read_n(conn, n):
    """Read exactly n bytes from a socket."""
    buf = b''
    while n > 0:
        data = conn.recv(n)
        if data == b'':
            raise ConnectionClosed('connection closed')
        buf += data
        n -= len(data)
    return buf

def extract_insole_data(msg_insole):
    """Extract only the pressure and acc info from the large streaming data"""
    
    saving_data = [msg_insole.data_message.time, msg_insole.data_message.side,\
                   *msg_insole.data_message.pressure,\
                   *np.around(msg_insole.data_message.acceleration, decimals=3),\
                   *np.around(msg_insole.data_message.angular, decimals=3),\
                   msg_insole.data_message.total_force,\
                   *np.around(msg_insole.data_message.cop, decimals=5)]
        
    return saving_data
    

def insole_data_save(file_name, data):
    """save the insole data into a text file"""
    
    # create path if not exist
    directory = os.path.dirname(file_name)
    Path(directory).mkdir(parents=True, exist_ok=True)
    
    insole_file = open(file_name, 'w')  # open file for writing
    
    # save data into text file
    # write header
    header_str = ['time', 'side', 'P1', 'P2', 'P3',\
              'P4', 'P5', 'P6', 'P7',\
              'P8', 'P9', 'P10', 'P11',\
              'P12', 'P13', 'P14', 'P15',\
              'P16', 'acc1', 'acc2', 'acc3', 'ang1', 'ang2', 'ang3',\
              'totalForce', 'cop1', 'cop2']
           
    try:
        for header_name in header_str:  # write header
            insole_file.write(header_name)
            insole_file.write(' ')
        insole_file.write('\n')
        
        c = len(data[0])  # get col number
        for row in data:  # write data
            for col in range(0, c):
                insole_file.write(str(row[col]))
                insole_file.write(' ')
            insole_file.write('\n')
             
    finally:
        insole_file.close()
            
            
    return


if __name__ == '__main__':
    run_recording()
