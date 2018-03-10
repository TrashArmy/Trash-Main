"""Main controller for Automated Trash Receptacle

Controls everything from here
"""
import time
import pigpio
import MySQLdb
import motor # motor controller
import servo_HS805BB # servo controller
#import light # light controller
import sonar # ultrasonic sensor controller

# Configuration
MYSQL_HOST = '159.203.125.202'
MYSQL_USER = 'remote'
MYSQL_PASS = 'login'
MYSQL_DB = 'SeniorDesign'
MYSQL_PORT = 3306

SERVO_1 = 0 # pin for servo 1
SERVO_2 = 0 # pin for servo 2
SERVO_3 = 0 # pin for servo 3

ACTUATOR_PWM = 0 # pin for speed control of linear actuator
ACTUATOR_FWD = 0 # pin for fwd control of linear actuator
ACTUATOR_REV = 0 # pin for rev control of linear actuator

LIGHT = 0 # pin for light

SONAR_1_ECHO = 20 # pin for sonar sensor 1 echo
SONAR_1_TRIG = 21 # pin for sonar sensor 1 trigger
SONAR_1_MIN = 6 # min distance for 100% [cm]
SONAR_1_MAX = 25 # max distance for 0% [cm]
SONAR_2_ECHO = 0 # pin for sonar sensor 2 echo
SONAR_2_TRIG = 0 # pin for sonar sensor 2 trigger
SONAR_3_ECHO = 0 # pin for sonar sensor 3 echo
SONAR_3_TRIG = 0 # pin for sonar sensor 3 trigger
SONAR_4_ECHO = 0 # pin for sonar sensor 4 echo
SONAR_4_TRIG = 0 # pin for sonar sensor 4 trigger

DOOR_SWITCH = 0 # pin for switch on door


# Define functions

def sonar_ping(s, cursor):
    #print(s.read())
    r = s.read_cm_avg(100, 0.05)
    if r >= SONAR_1_MAX:
        print('0%')
    elif r <= SONAR_1_MIN:
        print('100%')
    else:
        v = ((SONAR_1_MAX-r)/(SONAR_1_MAX-SONAR_1_MIN))*100
        print('{}%'.format(round(v)))


if __name__ == '__main__':
    # Initialization
    pi = pigpio.pi()
    conn = MySQLdb.connect(host = MYSQL_HOST,
                           user = MYSQL_USER,
                           passwd = MYSQL_PASS,
                           db = MYSQL_DB, 
                           port = MYSQL_PORT)
    cursor = conn.cursor()


    SONAR_1 = sonar.Sonar(pi, SONAR_1_TRIG, SONAR_1_ECHO)

    # Do stuff
    try:
        while(True):
            sonar_ping(SONAR_1, cursor)
            #print('loop!')
            #time.sleep(1)
            time.sleep(0.03)
    except KeyboardInterrupt:
        SONAR_1.cancel()




    # pi.stop()