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
MYSQL_TABLE = 'TrashData'

TRASH_ID = 0 # id of trashcan

SERVO_1 = 0 # pin for servo 1
SERVO_2 = 0 # pin for servo 2
SERVO_3 = 0 # pin for servo 3

ACTUATOR_PWM = 0 # pin for speed control of linear actuator
ACTUATOR_FWD = 0 # pin for fwd control of linear actuator
ACTUATOR_REV = 0 # pin for rev control of linear actuator

LIGHT = 0 # pin for light

SONAR_0_ECHO = 20 # pin for sonar sensor 1 echo
SONAR_0_TRIG = 21 # pin for sonar sensor 1 trigger
SONAR_0_MIN = 6 # min distance for 100% [cm]
SONAR_0_MAX = 25 # max distance for 0% [cm]
SONAR_1_ECHO = 0 # pin for sonar sensor 2 echo
SONAR_1_TRIG = 0 # pin for sonar sensor 2 trigger
SONAR_2_ECHO = 0 # pin for sonar sensor 3 echo
SONAR_2_TRIG = 0 # pin for sonar sensor 3 trigger
SONAR_3_ECHO = 0 # pin for sonar sensor 4 echo
SONAR_3_TRIG = 0 # pin for sonar sensor 4 trigger

DOOR_SWITCH = 0 # pin for switch on door


# Define functions

def sonar_ping(id, s, conn, dmin, dmax):
    p = 0
    r = s.read_cm_avg(100, 0.05)
    if r >= dmax:
        p = 0
    elif r <= dmin:
        p = 100
    else:
        p = round(((dmax-r)/(dmax-dmin))*100)
    
    print('id: {}, fill: {}%'.format(id, p))

    cursor = conn.cursor()
    sql = "INSERT INTO {0} VALUES({1}, {2}, NOW(), {3}, 0);".format(
          MYSQL_TABLE, TRASH_ID, id, p)
    try:
        cursor.execute(sql);
        conn.commit()
    except:
       print('insert failed');
       conn.rollback()

# Main 

if __name__ == '__main__':
    # Initialization
    pi = pigpio.pi()
    conn = MySQLdb.connect(host = MYSQL_HOST,
                           user = MYSQL_USER,
                           passwd = MYSQL_PASS,
                           db = MYSQL_DB, 
                           port = MYSQL_PORT)

    if not pi.connected:
        printf('Raspberry Pi not connecting')
        exit()

    if not conn:
        printf('MySQL not connecting')
        exit()

    SONAR_0 = sonar.Sonar(pi, SONAR_0_TRIG, SONAR_0_ECHO)
    #SONAR_1 = sonar.Sonar(pi, SONAR_1_TRIG, SONAR_1_ECHO)
    #SONAR_2 = sonar.Sonar(pi, SONAR_2_TRIG, SONAR_2_ECHO)
    #SONAR_3 = sonar.Sonar(pi, SONAR_3_TRIG, SONAR_3_ECHO)

    # Do stuff
    try:
        while(True):
            sonar_ping(0, SONAR_0, conn, SONAR_0_MIN, SONAR_0_MAX)
            sonar_ping(1, SONAR_0, conn, SONAR_0_MIN, SONAR_0_MAX)
            sonar_ping(2, SONAR_0, conn, SONAR_0_MIN, SONAR_0_MAX)
            sonar_ping(3, SONAR_0, conn, SONAR_0_MIN, SONAR_0_MAX)
            #print('loop!')
    except KeyboardInterrupt:
        SONAR_0.cancel()



    conn.close()
    # pi.stop()