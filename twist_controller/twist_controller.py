from yaw_controller import YawController
from pid import PID
from lowpass import LowPassFilter

import rospy

GAS_DENSITY = 2.858
ONE_MPH = 0.44704


class Controller(object):
    def __init__(self, vehicle_mass,fuel_capacity,brake_deadband,decel_limit,accel_limit,wheel_radius,wheel_base,steer_ratio,
                 max_lat_accel,max_steer_angle):
        self.yaw_controller = YawController(wheel_base,steer_ratio,0.1,max_lat_accel,max_steer_angle)
        kp = 0.4
        ki = 0.1
        kd = 0.1
        mn = 0. #min throttle
        mx = 0.3
        
        
        self.throttle_controller = PID(kp,ki,kd,mn,mx)
        
        tau = 0.5 #1/(2pi * tau) = cutoff frequency
        ts = 0.02 #sample time
        self.vel_lpf = LowPassFilter(tau,ts)
        self.str_lpf = LowPassFilter(1,1)
        self.vehicle_mass = vehicle_mass
        self.fuel_capacity = fuel_capacity
        self.brake_deadband = brake_deadband
        self.decel_limit = decel_limit
        self.accel_limit  = accel_limit
        self.wheel_radius  = wheel_radius
    
        self.last_time = rospy.get_time()
        # TODO: Implement
        pass
    
    def control(self, current_vel,dbw_enabled,linear_vel,angular_vel):
        # TODO: Change the arg, kwarg list to suit your needs
        # Return throttle, brake, steer
        if not dbw_enabled:
            self.throttle_controller.reset()
            return 1., 0., 0.
        
        current_vel = self.vel_lpf.filt(current_vel)
        steering = self.yaw_controller.get_steering(linear_vel,angular_vel,current_vel)
        steering = self.str_lpf.filt(steering)
        
        vel_error = linear_vel - current_vel
        self.last_vel = current_vel
        #rospy.loginfo('twist=controller--> target vel is %s', linear_vel)
        #rospy.loginfo('twist=controller--> error  vel is %s', vel_error)
        #rospy.loginfo('twist=controller--> current vel is %s', current_vel)

        current_time = rospy.get_time()
        sample_time = current_time - self.last_time
        self.last_time = current_time
        
        throttle = self.throttle_controller.step(vel_error,sample_time)
        #rospy.loginfo('twist=controller--> throttle from PID is %s', throttle)	
        
        if vel_error < 0 :
            throttle = 0.
        else:
            brake = 0.
       
        if linear_vel == 0 and current_vel < 0.1:
            throttle = 0.
            brake = 400.
            
        if (vel_error < 0 ):
                decel = max(vel_error,self.decel_limit)
                brake = 0.5* abs(decel)* self.vehicle_mass*self.wheel_radius      
            
        #rospy.loginfo('twist=controller--> Final throttle from PID is %s', throttle)
        #rospy.loginfo('twist=controller--> Final brake from PID is %s', brake)
        #rospy.loginfo('twist=controller--> Final steering from PID is %s', steering)
        
        #if steering > 0.5: steering = 0.5
        #if steering < -0.5: steering = -0.5
        return throttle,brake,steering