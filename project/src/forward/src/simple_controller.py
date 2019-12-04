#!/usr/bin/env python

import rospy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
import tf2_ros
import tf2_geometry_msgs
from math import radians

TURTLEBOT_ID = 'yellow' # might need to change this. If unsure or doesn't work, check rostopic list

class EncoderListener():
    def __init__(self):

        rospy.init_node('closed_loop_control', anonymous=False)

        self.angle = 0
        self.distance = 0
        self.topic = "/" + TURTLEBOT_ID + "/odom/"

        self.tf_buffer = tf2_ros.Buffer(rospy.Duration(1200.0)) #tf buffer length
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer)

        print("ENCODER LISTENER STARTED")

        def callback(data): 
            #print(data.pose.pose.position)
            transform = self.tf_buffer.lookup_transform("base_link",
                                       "odom", #source frame
                                       rospy.Time(0), #get the tf at first available time
                                       rospy.Duration(1.0)) #wait for 1 second
            print("transform")
            print(transform)
            transform.transform.translation.x = 0
            transform.transform.translation.y = 0
            transform.transform.translation.z = 0

            pose_transformed = tf2_geometry_msgs.do_transform_pose(data.pose, transform)
            print("ORIGINAL")
            print(data.pose)
            print("TRANSFORMED")
            print(pose_transformed)

        rospy.Subscriber("/" + TURTLEBOT_ID + "/odom/", Odometry, callback)


class openloop_move():
    def __init__(self):
        # initiliaze
        # rospy.init_node('drawasquare', anonymous=False)

        # What to do you ctrl + c    
        rospy.on_shutdown(self.shutdown)
        
        self.cmd_vel = rospy.Publisher('/' + TURTLEBOT_ID + '/cmd_vel_mux/input/navi', Twist, queue_size=10)
        # self.cmd_vel = rospy.Publisher('cmd_vel_mux/input/navi', Twist, queue_size=10)
     
    #TurtleBot will stop if we don't keep telling it to move.  How often should we tell it to move? 10 HZ = 1/10 s = 0.1s
        self.update_rate = 10
        self.r = rospy.Rate(self.update_rate);
        
    def shutdown(self):
        # stop turtlebot
        rospy.loginfo("Stop Moving")
        self.cmd_vel.publish(Twist())
        rospy.sleep(1)

    def go_forward(self, time, speed=0.2):
        # default speed is moving at 0.2 m/s
        # time in seconds
        rospy.loginfo("go forward for {0} s at speed {1} m/s".format(time, speed))
        go_forward_cmd = Twist()
        go_forward_cmd.linear.x = speed
        go_forward_cmd.angular.z = 0
        for x in range(0,time*self.update_rate): 
            self.cmd_vel.publish(go_forward_cmd)
            self.r.sleep()
    
    def go_backward(self, time, speed=0.2):
        # default speed is moving at 0.2 m/s
        rospy.loginfo("go backward for {0} s at speed {1} m/s".format(time, speed))
        go_backward_cmd = Twist()
        go_backward_cmd.linear.x = -speed
        go_backward_cmd.angular.z = 0
        for x in range(0,time*self.update_rate): 
            self.cmd_vel.publish(go_backward_cmd)
            self.r.sleep()

    def turn_right(self, time, speed=45):
        # default speed is turning at 45 deg/s
        turn_right_cmd = Twist()
        turn_right_cmd.linear.x = 0
        turn_right_cmd.angular.z = radians(speed); # convert 45 deg/s to radians/s
        rospy.loginfo("turn_right for {0} s at speed {1} deg/s".format(time, speed))
        for x in range(0,time*self.update_rate):
            self.cmd_vel.publish(turn_right_cmd)
            self.r.sleep()            

    def turn_left(self, time, speed=45):
        # default speed is turning at 45 deg/s
        turn_left_cmd = Twist()
        turn_left_cmd.linear.x = 0
        turn_left_cmd.angular.z = -radians(speed); # convert 45 deg/s to radians/s
        rospy.loginfo("turn left for {0} s at speed {1} def/s".format(time, speed))
        for x in range(0,time*self.update_rate):
            self.cmd_vel.publish(turn_left_cmd)
            self.r.sleep()
    def curve_left(self, time):
        curve_left_cmd = Twist()
        curve_left_cmd.linear.x = 0.2
        curve_left_cmd.angular.z = -radians(45); # convert 45 deg/s to radians/s
        rospy.loginfo("turn left for {0} s at speed {1} def/s".format(time, speed))
        for x in range(0,time*self.update_rate):
            self.cmd_vel.publish(curve_left_cmd)
            self.r.sleep()
 
if __name__ == '__main__':
    encoder_listener = EncoderListener()
    draw_tri = openloop_move()
    draw_tri.go_forward(2)
    draw_tri.go_backward(2)
    draw_tri.go_forward(2)
    draw_tri.go_backward(2)
    draw_tri.go_forward(2)
    draw_tri.go_backward(2)
    draw_tri.go_forward(2)
    draw_tri.go_backward(2)
    # draw_tri.turn_right(2, speed=90)
    # draw_tri.curve_left(3)
    # draw_tri.go_forward(2)
    # draw_tri.turn_right(4, speed=90)
    # draw_tri.go_forward(2)
    # draw_tri.shutdown()
    # except:
        # rospy.loginfo("node terminated.")


