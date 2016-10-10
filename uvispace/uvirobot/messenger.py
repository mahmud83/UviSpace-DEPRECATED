#!/usr/bin/env python 
"""
This module subscribes to speed topic and sends SPs through serial comm

It invokes the class SerMesProtocol() to manage the serial port. When a
new speed value is received, it is send to the external UGV using the
serial protocol object.
"""
# Standar libraries
import glob
import struct
import sys
import getopt
# ROS libraries
import rospy
from geometry_msgs.msg import Twist
# Local libraries
from serialcomm import SerMesProtocol

def main(argv):
    # This exception prevents a crash when no device is connected to CPU        
    try:
        port = glob.glob('/dev/ttyUSB*')[0]
    except IndexError:
        print 'It was not detected any serial port connected to PC'		
        sys.exit(1)  

    baudrate = 57600
    # Converts the Python id number to a C valid number, in unsigned byte
    my_serial = SerMesProtocol(port=port, baudrate=baudrate)    
    my_serial.SLAVE_ID = struct.pack( '>B',robot_id)
    # Checks connection to board. If broken, program exits
    if my_serial.ready():
        print "The board is ready"
        listener()
    else:
        print "The board is not ready"
        sys.exit()
    # spin() simply keeps python from exiting until this node is stopped
    rospy.spin()
        
def listener(robot_id):
    """Creates a node and subscribes to its robot 'cmd_vel' topic.""" 
    rospy.init_node('robot{}_messenger'.format(robot_id), anonymous=True)
    rospy.Subscriber('/robot_{}/cmd_vel'.format(robot_id), Twist, 
                     move_robot, queue_size=1)        
    
def move_robot(data, rho=0.065, L=0.150):
    """Converts Twist msg into 2WD value and send it through port."""
    v_RightWheel, v_LeftWheel = get_2WD_speeds(data.linear.x, data.angular.z)
    rospy.loginfo('I am sending R: {} L: {}'.format(v_RightWheel,
                                                      v_LeftWheel) )
    my_serial.move([v_RightWheel, v_LeftWheel])
            
def get_2WD_speeds(vLinear, vRotation, minInput=-0.3, maxInput=0.3, 
                    minOutput=89, maxOutput=165, rho=0.065, L=0.150):
    """
    Obtains two speeds components, one for each side of the vehicle. It
    calculates the resulting value according to the output required 
    scale. This calculus responds to the dynamics system proposed on the 
    paper: http://ieeexplore.ieee.org/stamp/stamp.jsp?arnumber=5674957

    Parameters
    ----------
    vLinear : int or float
        desired linear speed of the vehicle.

    vRotation : int or float
        desired rotatory speed of the vehicle.

    minInput : int or float
        input value for reverse linear direction at max speed.

    maxInput : int or float
        input value for direct linear direction at max speed.

    minOutput : int or float
        output value for minimum set point sent to the vehicle.

    maxOutput : int or float
        output value for maximum set point sent to the vehicle. 

    rho : float 
        Parameter of the dynamic model, which represents the vehicle's 
        wheels diameter, in meters.

    L : float
        Parameter of the dynamic model, which represents the distance 
        between the driving wheels of the vehicle.

    Returns
    -------
    v_R : 0 to 255 int
        output value for the right wheel.
        0 corresponds to max speed at reverse direction.
        255 corresponds to max speed at direct direction.
        127 corresponds to null speed.

    v_L : 0 to 255 int
        output value for the left wheel.
    """
    # Conversion of the linear speed range to the wheels angular speed.
    maxAngular = maxInput / rho
    minAngular = minInput / rho
    # Both terms are previosly calculated to reduce redundant operations.
    term1 = (1 / rho ) * vLinear
    term2 = (2 * rho * vRotation) / L
    # Calculates non-scaled raw values of the speeds.
    vR_raw = term1 + term2
    vL_raw = term1 - term2
    # Clips and scales the speed values to minOutput and maxOutput.
    v_clipped = np.clip([vR_raw, vL_raw], minAngular, maxAngular)
    v_num = (v_clipped - minAngular) * (maxOutput - minOutput)
    v_den = (maxAngular - minAngular)
    v_scaled = minOutput + v_num // v_den
    v_R, v_L = v_scaled.astype(int)
    return v_R, v_L   
     

    
if __name__ == "__main__":
    # This exception forces to give the robot_id argument
    try:
        opts, args = getopt.getopt(sys.argv,"hr:",["robotid="])
    except getopt.GetoptError:
        print 'messenger.py -r <robot_id>'
   for opt, arg in opts:
      if opt == '-h':
         print 'messenger.py -r, --robotid <robot_id>'
         sys.exit()
      elif opt in ("-r", "--robotid"):
         robot_id = arg        
    main(robot_id)
    
    
    
