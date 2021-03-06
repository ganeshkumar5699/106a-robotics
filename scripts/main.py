# This file execute the whole process.

# step 1: read data from optitrack

# step 2: move the turtlebot in initial setting

# step 3: avoid human

# step 4: reach the goal


#!/usr/bin/env python

import rospy
from geometry_msgs.msg import Twist
from geometry_msgs.msg import PoseStamped
import tf2_ros
import tf2_geometry_msgs
from math import radians, modf, pi
import math
import numpy as np

import motion_analytics
import scipy.spatial

from util import quaternion_to_euler, euler_to_quaternion
import time


cur_ped_x = None
cur_ped_y = None

cur_linear_x = None
cur_linear_y = None


# TURTLEBOT_ID = 'yellow' # might need to change this. If unsure or doesn't work, check rostopic list

# moving_cmd_topic = '/' + TURTLEBOT_ID + '/cmd_vel_mux/input/navi'
moving_cmd_topic = '/cmd_vel_mux/input/navi'

# odom_reading_topic = '/' + TURTLEBOT_ID + '/odom/'
# odom_reading_topic = '/odom/'
odom_reading_topic = '/vrpn_client_node/tb/pose'

ped_reading_topic = '/vrpn_client_node/cap/pose'

# define global function that constantly read odom reading
def listener():

	rospy.init_node('tb_control', anonymous=False)

	angle = 0
	distance = 0
	# topic = "/" + TURTLEBOT_ID + "/odom/"

	tf_buffer = tf2_ros.Buffer(rospy.Duration(1200.0)) #tf buffer length
	tf_listener = tf2_ros.TransformListener(tf_buffer)

	def turtlebot_callback(data):

		global cur_linear_x
		global cur_linear_y
		global cur_linear_z
		global cur_angular_x
		global cur_angular_y
		global cur_angular_z
		global cur_angular_w
		global cur_yaw
		global cur_pitch
		global cur_roll

		cur_linear_x = -data.pose.position.x
		cur_linear_y = data.pose.position.z
		cur_linear_z = data.pose.position.y

		cur_angular_x = data.pose.orientation.x
		cur_angular_y = data.pose.orientation.z
		cur_angular_z = data.pose.orientation.y
		cur_angular_w = data.pose.orientation.w

		# each yaw, pitch, roll is between -pi to pi
		cur_yaw, cur_pitch, cur_roll = quaternion_to_euler(cur_angular_x, cur_angular_y, cur_angular_z, cur_angular_w)
		cur_yaw_affine = cur_yaw + pi # range of [0, 2pi]
		cur_yaw = (cur_yaw_affine + pi/2) % (2*pi)
		cur_yaw = cur_yaw - pi

	def pedestrain_callback(data):
		global cur_ped_x
		global cur_ped_y

		cur_ped_x = -data.pose.position.x

		# print("ped_x: ", data.pose.position.x)
		# print("not none: ", cur_ped_x)
		cur_ped_y = data.pose.position.z

		# print("ped_y: ", data.pose.position.y)
		# print("not none: ", cur_ped_y)

		# print("in the pedestrain callback")


	# tb_sub.unregister()
	rospy.Subscriber(ped_reading_topic, PoseStamped, pedestrain_callback)
	rospy.Subscriber(odom_reading_topic, PoseStamped, turtlebot_callback)


	# only get message in 0.05s, then unsubscribe
	# rospy.sleep(0.5)
	# sub.unregister()
	# rospy.spin()


class simple_move():
	def __init__(self):
		# initiliaze
		# rospy.init_node('drawasquare', anonymous=False)

		# What to do you ctrl + c
		rospy.on_shutdown(self.shutdown)

		#TurtleBot will stop if we don't keep telling it to move.  How often should we tell it to move? 10 HZ = 1/10 s = 0.1s
		self.update_rate = 10
		self.r = rospy.Rate(self.update_rate)

		self.cmd_vel = rospy.Publisher(moving_cmd_topic, Twist, queue_size=10)

	def shutdown(self):
		# stop turtlebot
		shut_down_cmd = Twist()
		shut_down_cmd.linear.x = 0
		shut_down_cmd.angular.z = 0
		self.cmd_vel.publish(shut_down_cmd)
		# rospy.sleep(1)
		# sub.unregister()
		# rospy.loginfo("Stop Moving")


	def go_straight(self, time=None, speed=0.2, distance=None):
		# proportional control term
		p1 = 3

		if distance:
			desired_x = cur_linear_x + math.cos(cur_yaw) * distance
			desired_y = cur_linear_y + math.sin(cur_yaw) * distance

			# print("desired_x: {0} desired_y: {1}".format(desired_x, desired_y))

			go_straight_cmd = Twist()
			go_straight_cmd.linear.x = speed
			go_straight_cmd.angular.z = 0


			# rospy.loginfo("go to {0} at speed {1} def/s".format(distance, speed))

			x_err, y_err = abs(desired_x - cur_linear_x), abs(desired_y - cur_linear_y)

			# while the distance is less than some threshold
			while abs(desired_x - cur_linear_x) > 0.1 or abs(desired_y - cur_linear_y) > 0.1:
				print("x and y errors are as foollows: ", x_err, y_err)
				print("tb x: {0} y: {1}".format(cur_linear_x, cur_linear_y))

				if abs(desired_x - cur_linear_x) < 0.3 and abs(desired_y - cur_linear_y) < 0.3:
					if speed > 0:
						go_straight_cmd.linear.x = max(speed * abs(desired_x - cur_linear_x) * p1, 0.2)
					else:
						go_straight_cmd.linear.x = min(speed * abs(desired_x - cur_linear_x) * p1, -0.2)
				self.cmd_vel.publish(go_straight_cmd)
				self.r.sleep()
				x_err, y_err = abs(desired_x - cur_linear_x), abs(desired_y - cur_linear_y)


		elif time:
			# rospy.loginfo("go for {0} s at speed {1} m/s".format(time, speed))
			go_straight_cmd = Twist()
			go_straight_cmd.linear.x = speed
			go_straight_cmd.angular.z = 0

			for x in range(0,int(time*self.update_rate)):
				self.cmd_vel.publish(go_straight_cmd)
				self.r.sleep()
		# go forever
		elif time is None and distance is None:
			go_straight_cmd = Twist()
			go_straight_cmd.linear.x = speed
			go_straight_cmd.angular.z = 0
			for x in range(0,999*self.update_rate):
				self.cmd_vel.publish(go_straight_cmd)
				self.r.sleep()


	def turn(self, time=None, speed=0.4, angle=None, yaw_coor=None):
		# counterclockwise is always increasing, and clockwise is always decreasing
		# starting z orientation angle is always 0,
		# and the reverse (pi or 180 degree) z is 1/-1 depends on which direction it moves
		# if move counterclockwise, then 0 -> pi -> -pi -> 0 complete one loop
		# if move clockwise, then 0 -> -pi -> pi -> 0 complete one loop

		# proportional control term
		p1 = 3

		if time:
			turn_cmd = Twist()
			turn_cmd.linear.x = 0
			turn_cmd.angular.z = speed
			rospy.loginfo("turn left for {0} s at speed {1} def/s".format(time, speed))
			for x in range(0,time*self.update_rate):
				self.cmd_vel.publish(turn_cmd)
				self.r.sleep()
				print("current yaw: ", cur_yaw)
		elif angle:
			if angle > 180 or angle < -180:
				raise Exception("angle must be smaller than 180 or greater than -180")

			starting_yaw = cur_yaw
			ending_yaw = radians(angle) + starting_yaw

			# handle the case where from positive to negative or from negative to positive
			if ending_yaw > pi:
				ending_yaw = pi-ending_yaw
			elif ending_yaw < -pi:
				ending_yaw = 2*pi+ending_yaw
			yaw_coor = ending_yaw
			rospy.loginfo("turn for {0} degree at speed {1} rad/s".format(angle, speed))

		# because z_coor could be 0
		if yaw_coor is not None:
			if yaw_coor > pi or yaw_coor < -pi:
				raise Exception("yaw_coor must be smaller than pi or greater than -pi")

			turn_cmd = Twist()
			turn_cmd.angular.z = speed

			print("starting to turn")
			error = abs(cur_yaw - yaw_coor)
			while error > 0.02:
				if error < 0.2:
					turn_cmd.angular.z = 0.15

				print("turning, with error ", abs(cur_yaw - yaw_coor))
				print("cur_yaw ", cur_yaw)
				print("yaw_coor ", yaw_coor)
				abs(cur_yaw - yaw_coor)
				self.cmd_vel.publish(turn_cmd)
				self.r.sleep()
				error = abs(cur_yaw - yaw_coor)



			turn_cmd.angular.z = 0
			self.cmd_vel.publish(turn_cmd)


	def curve_left(self, time, lin_speed=0.2, ang_speed=20):
		curve_left_cmd = Twist()
		curve_left_cmd.linear.x = lin_speed
		curve_left_cmd.angular.z = radians(ang_speed); # convert 45 deg/s to radians/s
		rospy.loginfo("curve left for {0} s at linear speed {1} m/s and angular speed {2} def/s".format(time, lin_speed, ang_speed))
		for x in range(0,time*self.update_rate):
			self.cmd_vel.publish(curve_left_cmd)
			self.r.sleep()


	def curve_right(self, time, lin_speed=0.2, ang_speed=20):
		curve_right_cmd = Twist()
		curve_right_cmd.linear.x = lin_speed
		curve_right_cmd.angular.z = -radians(ang_speed); # convert 45 deg/s to radians/s
		rospy.loginfo("curve right for {0} s at linear speed {1} m/s and angular speed {2} def/s".format(time, lin_speed, ang_speed))
		for x in range(0,time*self.update_rate):
			self.cmd_vel.publish(curve_right_cmd)
			self.r.sleep()


if __name__ == '__main__':
	listener()

	turtlebot = simple_move()
	rospy.sleep(1.5)
	print("tb x: {0} y: {1}".format(cur_linear_x, cur_linear_y))

	index = 0
	turtlebot_distance_to_human = math.sqrt((cur_linear_x - cur_ped_x)**2 + (cur_linear_y - cur_ped_y)**2)
	THRESHOLD = 1

	goal = (-1, 2)
	# print(cur_yaw)

	desired_coor = math.atan2((goal[1] - cur_linear_y), (goal[0] - cur_linear_x))

	print("calculation: ", desired_coor)

	turtlebot.turn(yaw_coor=desired_coor)
	rospy.sleep(0.5)

	# ########### With OptiTrack ###########
	# threshold = motion_analytics.get_min_distance(data)
	while not rospy.is_shutdown():

		# while not rospy.is_shutdown():
		if not cur_linear_x or not cur_ped_x:
			if not cur_linear_x:
				print("curlinx not def")
			if not cur_ped_x:
				print("curpedx not def")
			continue

		# print("initial distance: ", turtlebot_distance_to_human)
		print("pedestrain x: {0} y: {1}".format(cur_ped_x, cur_ped_y))
		print("tb x: {0} y: {1}".format(cur_linear_x, cur_linear_y))
		print("threshold: ", THRESHOLD)


		# go straight until close to stop threshold, then stop
		turtlebot_distance_to_goal = math.hypot(goal[0] - cur_linear_x, goal[1] - cur_linear_y)

		while turtlebot_distance_to_goal > 0.15:
			turtlebot_speed = 0.3 if THRESHOLD <= turtlebot_distance_to_human else 0
			turtlebot.go_straight(time=0.1, speed=turtlebot_speed)
			turtlebot_distance_to_goal = math.hypot(goal[0] - cur_linear_x, goal[1] - cur_linear_y)
			turtlebot_distance_to_human = math.sqrt((cur_linear_x - cur_ped_x)**2 + (cur_linear_y - cur_ped_y)**2)

			#if index%10 == 0:
			print("pedestrain x: {0} y: {1}".format(cur_ped_x, cur_ped_y))
			print("tb x: {0} y: {1}".format(cur_linear_x, cur_linear_y))
			print("pedestrain-robot distance: ", turtlebot_distance_to_human)
			print("goal-robot distance: ", turtlebot_distance_to_goal)

			index += 1
			time.sleep(0.017)
		break

	turtlebot.curve_right(time=4, lin_speed=0.3, ang_speed=35)
	turtlebot.shutdown()
