import socket
import struct
import moticon_insole3.proto.service.service_pb2 as proto_s
import numpy as np
import os
from pathlib import Path
import csv
import time


class ConnectionClosed(Exception):
    pass


def run_recording():
    # Create a UDP socket (for Xsens joint angle data streaming)
    sock_xsens_Joint = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Create a UDP socket (for Xsens segment orentation streaming)
    sock_xsens_Seg = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Create a UDP socket (for Xsens CoM streaming)
    sock_xsens_CoM = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Create a UDP socket (for Xsens time code streaming)
    sock_xsens_Tim = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Create a TCP/IP socket (for insole data streaming)
    sock_insole = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Check the Internet setup of the Moticon App (smartphone) and the computer
    # for running this code. They need to be in the same sub-network.
    
    # Ip address & port of Moticon insole (Find this in the Moticon Phone App)
    server_name_insole = ""
    port_insole = 9999
    
    # Ip address & port of the Xsens MVN software (Find this in the 'Options
    # /Network Streamer', make sure you have created the streamer with corresponding
    # setup: Host/Port number should be in consistant with the ones listed below; 
    # 'UDP' type of Protocol needs to be selected; Corresponding Avatar number
    # needs to be selected; 'Send Pause' option needs to be selected. In the
    # Datagram selection, 'Joint Angles', should
    # be selected only, so that the parse function will work well. For other selections
    # of the Datagram, the parse function needs to be adjusted.)
    server_name_xsens = "127.0.0.1"
    port_stre_xsens_angles = 9763
    port_stre_xsens_Seg = 9764
    port_stre_xsens_CoM = 9765
    port_stre_xsens_Tim = 9766
    
    # build the xsens socket and listen to client
    server_address_xsens_angles = (server_name_xsens, port_stre_xsens_angles)
    print ('xsens connection starting up on {} port {}'.format(server_name_xsens, port_stre_xsens_angles))
    sock_xsens_Joint.bind(server_address_xsens_angles)
    
    # build the xsens socket and listen to client
    server_address_xsens_Seg = (server_name_xsens, port_stre_xsens_Seg)
    print ('xsens connection starting up on {} port {}'.format(server_name_xsens, port_stre_xsens_Seg))
    sock_xsens_Seg.bind(server_address_xsens_Seg)    
    
    # build the xsens socket and listen to client
    server_address_xsens_CoM = (server_name_xsens, port_stre_xsens_CoM)
    print ('xsens connection starting up on {} port {}'.format(server_name_xsens, port_stre_xsens_CoM))
    sock_xsens_CoM.bind(server_address_xsens_CoM)
    
    # build the xsens socket and listen to client
    server_address_xsens_Tim = (server_name_xsens, port_stre_xsens_Tim)
    print ('xsens connection starting up on {} port {}'.format(server_name_xsens, port_stre_xsens_Tim))
    sock_xsens_Tim.bind(server_address_xsens_Tim)

    # build the insole socket and listen to server
    server_address_insole = (server_name_insole, port_insole)
    print ('insole connection starting up on {} port {}'.format(server_name_insole, port_insole))
    sock_insole.bind(server_address_insole)
    sock_insole.listen(1)

    saving_numb = 1  # initialize savng trial number as 1

    while True:

        # Connect to Moticon insoles
        print('Moticon insoles waiting for a connection')
        connection_insole, client_address_insole = sock_insole.accept()
        
        # file names for saving, trial number will automatically add one for each repeated trial
        # to avoid over-writting. It is suggested to rename saved trials right after each recording.
        insole_text_name = "RecordingTest/data_insole_trial"\
            + str(saving_numb) + ".txt"  # text file for insole data saving
        xsens_text_name = "RecordingTest/data_xsens_trial"\
            + str(saving_numb) + ".txt"  # text file for xsens data saving
            
        # initialize the variable names for data storage
        insole_saving_data = []
        xsens_saving_data = []
            
        frame_counter = 0   # start from the frame of zero
        
        try:
            print('client connected: {}'.format(client_address_insole))

            while True:
                
                try:
                    # read insole socket data
                    msg_buf_insole = get_message_insole(connection_insole)
                    
                except ConnectionClosed as e:
                    print(e)
                    break
    
                # start xsens recording and save data after the insole's header line (top 5 frames)
                if frame_counter < 5:  # the first 5 frames are headings, skipping. 
                    frame_counter = frame_counter + 1  # count increase until 5
                    
                else:
                    try:
                        # read xsens socket data, the time cost of recv can be tested, normally should below 1ms
                        # st_time = time.time()
                        msg_buf_xsens_angles, address_xsens_joint = sock_xsens_Joint.recvfrom(584)
                        msg_buf_xsens_segments, address_xsens_segment = sock_xsens_Seg.recvfrom(760)
                        msg_buf_xsens_coms, address_xsens_com = sock_xsens_CoM.recvfrom(60)
                        msg_buf_xsens_time, address_xsens_time_code = sock_xsens_Tim.recvfrom(40)
                        # ed_time = time.time()
                        # print('reading --' + str(st_time - ed_time))
                        
                    except ConnectionClosed as e:
                        print(e)
                        break
                    
                    # parse the insole data and save it to file
                    msg_insole = proto_s.MoticonMessage()
                    msg_insole.ParseFromString(msg_buf_insole)
                    
                    # parse the xsens joint angles, time cost of parsing can be tested, should always below 1ms
                    # st_time = time.time()
                    Osim_ang = parse_xsens_angles(msg_buf_xsens_angles)
                    pelvis_loc_ore = parse_xsens_SegOrentation(msg_buf_xsens_segments)  
                    com_vec_data = parse_xsens_CoM(msg_buf_xsens_coms)
                    time_sec = parse_xsens_timecode(msg_buf_xsens_time)
                    # ed_time = time.time()
                    # print('parse--' + str(st_time - ed_time))
                    
                    # connect data together, in the format of OpenSim2392 model joint angle order
                    # generate joint angle data for saving
                    if frame_counter == 5:
                        time_start = time_sec
                        frame_counter = 6  # count increase
                    
                    # combine xsens data together
                    Osim_ang[0] = round(time_sec - time_start, 3)
                    Osim_ang[1:7] = pelvis_loc_ore
                    Osim_ang[24:27] = com_vec_data
                                        
                    # select insole data for saving
                    insole_saving_data.append(extract_insole_data(msg_insole))
                    xsens_saving_data.append(Osim_ang)
   
        finally:             
            # save the data into files
            insole_data_save(insole_text_name, insole_saving_data)
            xsens_data_save(xsens_text_name, xsens_saving_data)
            
            print('recording stoped')
            
            saving_numb += 1  # trial number + 1, automatically
            
            # close connections            
            connection_insole.close()
            # connection_xsens.close()    UDP does not need to kill


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
    header_str = ['Frame', 'side', 'P1', 'P2', 'P3',\
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


def parse_head_xsens(message):
    """Parse the head message from bytes into meaningful info"""
    # Parse the header for the first frame
    #messageId = str(message[0:6])[2:-1];  # comment out to save executing time
    messageType = int(str(message[4:6])[2:4])
    sampleCounter = struct.unpack('>I', message[6:10])[0] + 1
    #datagramCounter = struct.unpack('>b', message[10:11])[0]   # comment out to save executing time
    numJoints = struct.unpack('>b', message[11:12])[0]  # comment out to save executing time
    #timeCode = struct.unpack('>I', message[12:16])[0]  # comment out to save executing time
    
    #return messageId, messageType, sampleCounter, datagramCounter, numJoints, timeCode
    return messageType, sampleCounter, numJoints
    
    
def parse_xsens_angles(message):
    """Parse the joint angles the buffer data"""
    
    # parse the header information of the xsens data
    # messageId, messageType, sampleCounter, datagramCounter,\
    # numJoints, timeCode = parse_head_xsens(message)
    messageType, sampleCounter, numJoints = parse_head_xsens(message)  # simplified version

    numJoints = 28  # manually define the number of joints, since the head info is not correct

    # Initialization of position and orientation variavles
    # Ids = np.zeros((numJoints, 2))  # Segments = 23, numJoints = 22
    angles = np.zeros((numJoints, 3))  # Segments = 23  numJoints = 22
    
    if messageType == 20:  # check if the joint angles be streamed
    
        # for s in range(0, numJoints):  # Segments = 23
        for s in [0, 1, 2, 3, 14, 15, 16, 18, 19, 20]: 
            offset = s*20 + 0  # packetSize = 20
            
            # Ids[s, 0] = struct.unpack('>I', message[offset+24: offset+28])[0]
            # Ids[s, 1] = struct.unpack('>I', message[offset+ 4 +24: offset+ 4 +28])[0]
                        
            # id array should be like this, if not the 'joint_angle_regeneration'
            # need adjustments
            # [ 258.,  513.], [ 514.,  769.], [ 770., 1025.], [1026., 1281.],
            # [1282., 1537.], [1538., 1793.], [1283., 2049.], [2050., 2305.],
            # [2306., 2561.], [2562., 2817.], [1284., 3073.], [3074., 3329.],
            # [3330., 3585.], [3586., 3841.], [ 259., 4097.], [4098., 4353.],
            # [4354., 4609.], [4610., 4865.], [ 260., 5121.], [5122., 5377.],
            # [5378., 5633.], [5634., 5889.], [1280., 1792.], [1280., 3328.],
            # [1280., 2304.], [ 256., 1280.], [ 256.,  256.]
            
            angles[s, 0] = struct.unpack('>f', message[offset+ 8 +24: offset+ 8 +28])[0]
            angles[s, 1] = struct.unpack('>f', message[offset+ 12 +24: offset+ 12 +28])[0]
            angles[s, 2] = struct.unpack('>f', message[offset+ 16 +24: offset+ 16 +28])[0]

    else:  # if not, raise error message
        raise Exception('The Message Type is not Joint angles')

    angle_vec = joint_angle_regeneration(angles)

    return angle_vec


def joint_angle_regeneration(angles):
    """convert the rotation angles in x-y-z axises into pysiological joint angles"""
    
    # initalized the joint angle vectors as 18 columns, contains the following
    # info: 'pelvis_tilt'	'pelvis_list'	'pelvis_rotation'	'hip_flexion_r'
	# 'hip_adduction_r'    'hip_rotation_r'    'knee_angle_r'	'ankle_angle_r'
	# 'subtalar_angle_r'    'hip_flexion_l'	'hip_adduction_l'	'hip_rotation_l'
	# 'knee_angle_l'    'ankle_angle_l'    'subtalar_angle_l'
	# 'lumbar_extension'	'lumbar_bending'	'lumbar_rotation'
    
    angle_vec = np.zeros((27, ))
        
    # pelvis rotations are in the row of id number [256, 256]
    # check if pelvis rotation is pi/-pi off
    # if angles[-2, 2] > np.pi/2:
    #     angles[-2, 2] = angles[-2, 2] - np.pi
    # elif angles[-2,2 ] < -np.pi/2:
    #     angles[-2, 2] = angles[-2, 2] + np.pi
        
    # angle_vec[0:3] = [-angles[-2, 1], angles[-2, 0], angles[-2, 2]]
    
    # right hip rotations are in the row of id number [259, 4097]
    angle_vec[7:10] = [angles[14, 2], -angles[14, 0], angles[14, 1]]
    
    # righ knee flexion is in the row of id number [4098, 4353]
    angle_vec[10] = -angles[15, 2]
    
    # right ankle rotations are in the row of id number [4354, 4609]
    angle_vec[11:13] = [angles[16, 2], angles[16, 1]]
    
    # right mtp angle equal 0
    # angle_vec[12] = 0
    
    # left hip rotations are in the row of id number [260, 5121]
    angle_vec[14:17] = [angles[18, 2], -angles[18, 0], angles[18, 1]]
    
    # left knee flexion is in the row of id number [5122, 5377]
    angle_vec[17] = -angles[19, 2]
    
    # left ankle rotations are in the row of id number [5378, 5633]
    angle_vec[18:20] = [angles[20, 2], angles[20, 1]]
    
    # left mtp angle equal 0
    # angle_vec[19] = 0
    
    # lumbar joint rotations are in the row of id number [258, 513] or/and [514, 769]
    # L5S1, L4L3, L1T12, T9T8
    lumbar_joint = angles[0, :]  + angles[1, :] + angles[2, :] + angles[3, :]
    angle_vec[21:24] = [-lumbar_joint[2], lumbar_joint[0], lumbar_joint[1]]
    
    return np.around(angle_vec, decimals=3)

def parse_xsens_CoM(message):
    """Parse the CoM the buffer data"""
    
    # parse the header information of the xsens data
    # messageId, messageType, sampleCounter, datagramCounter,\
    # numJoints, timeCode = parse_head_xsens(message)
    messageType, sampleCounter, numJoints = parse_head_xsens(message)  # simplified version

    # Initialization of position and orientation variavles
    CoM = np.zeros((3, ))  # Segments = 23, numJoints = 22
    
    if messageType == 24:  # check if the CoM been streamed
    
        CoM = [struct.unpack('>f', message[24: 28])[0],
               struct.unpack('>f', message[32: 36])[0],
               -struct.unpack('>f', message[28: 32])[0]]

    else:  # if not, raise error message
        raise Exception('The Message Type is not CoM')

    return np.around(np.array(CoM), decimals=3)

def parse_xsens_SegOrentation(message):
    """Parse the CoM the buffer data"""
    
    # parse the header information of the xsens data
    # messageId, messageType, sampleCounter, datagramCounter,\
    # numJoints, timeCode = parse_head_xsens(message)
    messageType, sampleCounter, numJoints = parse_head_xsens(message)  # simplified version
    
    numSegments = 23
    biteSize = 32
    
    # Initialization of position and orientation variavles
    PelvisLoc = np.zeros((3, ))
    PelvisOre = np.zeros((3, ))  # Segments = 23, numJoints = 22
    
    if messageType == 2:  # check if the Position/Orientation been streamed
    
        for seg in range(numSegments):
            # only extract the pelvis position and orientation
            if struct.unpack('>I', message[seg*biteSize + 24:seg*biteSize + 28])[0] == 1:
                PelvisLoc = np.array([struct.unpack('>f', message[seg*biteSize + 28: seg*biteSize + 32])[0],
                             struct.unpack('>f', message[seg*biteSize + 36: seg*biteSize + 40])[0],
                             -struct.unpack('>f', message[seg*biteSize + 32: seg*biteSize + 36])[0]])
                
                qn = [struct.unpack('>f', message[seg*biteSize + 40: seg*biteSize + 44])[0],
                             struct.unpack('>f', message[seg*biteSize + 44: seg*biteSize + 48])[0],
                             struct.unpack('>f', message[seg*biteSize + 48: seg*biteSize + 52])[0],
                             struct.unpack('>f', message[seg*biteSize + 52: seg*biteSize + 56])[0]]
                
                # transfer the quantinue rotation to euler angles
                
                z = np.arctan2(2*(qn[1]*qn[2] + qn[0]*qn[3]), qn[0]**2 + qn[1]**2 - qn[2]**2 - qn[3]**2)
                y = np.arcsin(-2*(qn[1]*qn[3] - qn[0]*qn[2]))
                x = np.arctan2(2*(qn[2]*qn[3] + qn[0]*qn[1]), qn[0]**2 - qn[1]**2 - qn[2]**2 + qn[3]**2)
                
                # make sure the pelvis rotation is always positive
                if z < 0:
                    z = z + 2*np.pi
                    
                PelvisOre = np.array([-y, x, z])*180/np.pi
                    
                continue

        if sum(PelvisLoc) == 0:
            raise Exception('No segment has the id of 1 (Pelvis)')
            
    else:  # if not, raise error message
        raise Exception('The Message Type is not Segment Euler Data')

    return np.around(np.hstack((PelvisOre, PelvisLoc)), decimals=3)


def parse_xsens_timecode(message):
    """
    Parse the time code into seconds, assume the recording will not go over days
    """
    
    # parse the header information of the xsens data
    # messageId, messageType, sampleCounter, datagramCounter,\
    # numJoints, timeCode = parse_head_xsens(message)
    messageType, sampleCounter, numJoints = parse_head_xsens(message)  # simplified version
    
    if messageType == 25:
    
        timeFrame = str(message[-12:])[2:-1]
        
        timesecond = round(int(timeFrame[0:2])*3600 + int(timeFrame[3:5])*60 +\
                     int(timeFrame[6:8]) + int(timeFrame[9:12])*0.001, 3)
        
        
    else:
        raise Exception('The Message Type is not Time Code')
        
    return timesecond
        
def xsens_data_save(file_name, data):
    """save the xsens data into a text file"""
    
    # create path if not exist
    directory = os.path.dirname(file_name)
    Path(directory).mkdir(parents=True, exist_ok=True)
    
    xsens_file = open(file_name, 'w')  # open file for writing
    
     # titles of xsens joint angle savings
    Osim_ang_titles = ['time', 'pelvis_tilt', 'pelvis_list', 'pelvis_rotation',\
          'pelvis_tx', 'pelvis_ty', 'pelvis_tz', 'hip_flexion_r',\
          'hip_adduction_r', 'hip_rotation_r', 'knee_angle_r',\
          'ankle_angle_r', 'subtalar_angle_r', 'mtp_angle_r',\
          'hip_flexion_l', 'hip_adduction_l', 'hip_rotation_l',\
          'knee_angle_l', 'ankle_angle_l', 'subtalar_angle_l',\
          'mtp_angle_l', 'lumbar_extension', 'lumbar_bending',\
          'lumbar_rotation', 'CoMx', 'CoMy', 'CoMz']
    
    try:
        for header_name in Osim_ang_titles:  # write header
            xsens_file.write(header_name)
            xsens_file.write(' ')
        xsens_file.write('\n')
        
        c = len(data[0])  # get col number
        for row in data:  # write data
            for col in range(c):
                xsens_file.write(str(row[col]))
                xsens_file.write(' ')
            xsens_file.write('\n')
             
    finally:
        xsens_file.close()
            
    return   


if __name__ == '__main__':
    run_recording()
