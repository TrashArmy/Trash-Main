"""Main controller for Automated Trash Receptacle

Controls everything from here
"""
import time
import pigpio
import os

# Import IOT Components
import MySQLdb
# if MySQLdb not found, do:
# sudo apt-get install mysql-server
# sudo apt-get install mysql-client
# sudo apt-get install python-mysqldb

# Import mechanical contoller components
import motor  # motor controller
import servo_HS805BB  # servo controller
import light  # light controller
import sonar  # ultrasonic sensor controller
import switch  # switch controller

# Importing components necessary for Computer Vision
import numpy as np
import sys
import tensorflow as tf
from collections import defaultdict
from io import StringIO
from matplotlib import pyplot as plt
from PIL import Image

sys.path.append('./object_detection')
from object_detection.utils import ops as utils_ops

if tf.__version__ < '1.4.0':
  raise ImportError('Please upgrade your tensorflow installation to v1.4.* or later!')
from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as vis_util



#Importing Our Custom Packages
import CaptureImage

# Configuration
MYSQL_HOST = '159.203.125.202'
MYSQL_USER = 'remote'
MYSQL_PASS = 'login'
MYSQL_DB = 'SeniorDesign'
MYSQL_PORT = 3306
MYSQL_TABLE = 'TrashData'

TRASHCAN_ID = 0  # id of trashcan

SERVO_EN = True
ACTUATOR_EN = True
LIGHT_EN = True
CAMERA_EN = True
SONAR_EN = True
DOOR_SWITCH_EN = True

SERVO_0_PWM = 23  # pin for servo 0
SERVO_0_CLOSE = 73  # angle at which flap 0 is closed
SERVO_0_OPEN = -45  # angle at which flap 0 is opened

SERVO_1_PWM = 24  # pin for servo 1
SERVO_1_CLOSE = 76  # angle at which flap 1 is closed
SERVO_1_OPEN = -45  # angle at which flap 1 is opened

SERVO_2_PWM = 12  # pin for servo 2
SERVO_2_CLOSE = 20  # angle at which flap 2 is closed
SERVO_2_OPEN = -75  # angle at which flap 2 is opened

ACTUATOR_PWM = 16  # pin for speed control of linear actuator
ACTUATOR_FWD = 21  # pin for fwd control of linear actuator
ACTUATOR_REV = 20  # pin for rev control of linear actuator

LIGHT_PIN = 18  # pin for light

SONAR_0_ECHO = 17  # pin for sonar sensor 1 echo
SONAR_0_TRIG = 27  # pin for sonar sensor 1 trigger
SONAR_0_MIN = 46  # min distance for 100% [cm]
SONAR_0_MAX = 146  # max distance for 0% [cm]

SONAR_1_ECHO = 22  # pin for sonar sensor 2 echo
SONAR_1_TRIG = 5  # pin for sonar sensor 2 trigger
SONAR_1_MIN = 29.7  # min distance for 100% [cm]
SONAR_1_MAX = 37  # max distance for 0% [cm]

SONAR_2_ECHO = 6  # pin for sonar sensor 3 echo
SONAR_2_TRIG = 13  # pin for sonar sensor 3 trigger
SONAR_2_MIN = 10.8  # min distance for 100% [cm]
SONAR_2_MAX = 121  # max distance for 0% [cm]

SONAR_3_ECHO = 19  # pin for sonar sensor 4 echo
SONAR_3_TRIG = 26  # pin for sonar sensor 4 trigger
SONAR_3_MIN = 5.5  # min distance for 100% [cm]
SONAR_3_MAX = 95.8  # max distance for 0% [cm]

DOOR_SWITCH_PIN = 4  # pin for switch on door


IMAGE_DIR = "./images/"

MODEL_FOLDER_NAME = 'classification_model'
# Path to frozen detection graph. This is the actual model that is used for the object detection.
PATH_TO_CKPT = MODEL_NAME + '/frozen_inference_graph.pb'
# List of the strings that is used to add correct label for each box.
PATH_TO_LABELS = os.path.join('classification_model', 'label_map.pbtxt')
NUM_CLASSES = 4 # Number of classes classifier has

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

    print('id: {}, fill: {}%, value: {}'.format(id, p, r))

    cursor = conn.cursor()
    sql = "INSERT INTO {0} VALUES({1}, {2}, NOW(), {3}, 0);".format(
          MYSQL_TABLE, TRASHCAN_ID, id, p)
    try:
        cursor.execute(sql)
        conn.commit()
    except:
        print('insert failed')
        conn.rollback()


def validateDir(name):
    # Returns dire
    if not os.path.exists(name):
        return name
    else:
        i = 1
        temp = name
        while i < 200 and os.path.exists(name):
            name = temp + "_" + str(i)
            i += 1
        if i == 200:
            raise Exception("Name value exceeding limit")
    return name


def getDataDir(name):
    '''
    Creates a folder with any name in the directory
    '''
    name = IMAGE_DIR + name
    name = validateDir(name)
    os.makedirs(name)
    return name


def getDataFolderName():
    return time.strftime("%Y%m%d", time.gmtime())

def loadImageIntoNumpyArray(image):
  (im_width, im_height) = image.size
  return np.array(image.getdata()).reshape(
      (im_height, im_width, 3)).astype(np.uint8)

def getLabelMapCategories():
    label_map = label_map_util.load_labelmap(PATH_TO_LABELS)
    categories = label_map_util.convert_label_map_to_categories(label_map,
        max_num_classes=NUM_CLASSES, use_display_name=True)
    category_index = label_map_util.create_category_index(categories)
    return category_index


# Main
if __name__ == '__main__':
    # Initialization
    pi = pigpio.pi()
    conn = MySQLdb.connect(host=MYSQL_HOST,
                           user=MYSQL_USER,
                           passwd=MYSQL_PASS,
                           db=MYSQL_DB,
                           port=MYSQL_PORT)

    if not pi.connected:
        print('Raspberry Pi not connecting')
        exit()

    if not conn:
        print('MySQL not connecting')
        exit()

    if DOOR_SWITCH_EN:
        DOOR_SWITCH = switch.Switch(pi, DOOR_SWITCH_PIN)

    if LIGHT_EN:
        LIGHT = light.Light(LIGHT_PIN)
        LIGHT.off()

    if SERVO_EN:
        SERVO_0 = servo_HS805BB.Servo_HS805BB(pi, SERVO_0_PWM)
        SERVO_1 = servo_HS805BB.Servo_HS805BB(pi, SERVO_1_PWM)
        SERVO_2 = servo_HS805BB.Servo_HS805BB(pi, SERVO_2_PWM)

        SERVO_0.degree(SERVO_0_CLOSE)
        SERVO_1.degree(SERVO_1_CLOSE)
        SERVO_2.degree(SERVO_2_CLOSE)

        SERVO_0.off()
        SERVO_1.off()
        SERVO_2.off()

    if ACTUATOR_EN:
        ACTUATOR = motor.Motor(pi, ACTUATOR_PWM, ACTUATOR_FWD, ACTUATOR_REV)
        ACTUATOR.speed(0)

    if SONAR_EN:
        SONAR_0 = sonar.Sonar(pi, SONAR_0_TRIG, SONAR_0_ECHO)
        SONAR_1 = sonar.Sonar(pi, SONAR_1_TRIG, SONAR_1_ECHO)
        SONAR_2 = sonar.Sonar(pi, SONAR_2_TRIG, SONAR_2_ECHO)
        SONAR_3 = sonar.Sonar(pi, SONAR_3_TRIG, SONAR_3_ECHO)

    # Create and get data folder
    data_path = getDataDir(getDataFolderName())
    image_count = 0
    LIGHT = light.Light(LIGHT_PIN)

    # Loading Frozen Tensorflow model into memory
    detection_graph = tf.Graph()
    with detection_graph.as_default():
      od_graph_def = tf.GraphDef()
      with tf.gfile.GFile(PATH_TO_CKPT, 'rb') as fid:
        serialized_graph = fid.read()
        od_graph_def.ParseFromString(serialized_graph)
        tf.import_graph_def(od_graph_def, name='')



    # Do stuff
    try:
        while(True):
            print('Ready...')
            if DOOR_SWITCH_EN:
                while(not DOOR_SWITCH.toggled()):
                    time.sleep(0.100)  # sleep 100 ms
            print('Door toggled')
            # Front door opened and closed; assume trash is on platform, and
            # begin computer vision algorithm below.

            # Algorithm should include the following for the light:
            #     import light
            #     LIGHT = light.Light(LIGHT_PIN)
            #     LIGHT.on()
            #     # do something
            #     LIGHT.off()
            # At this point in the controller, we should be able to call
            # the alogirthm like this:
            # trash_id = algorithm()  # should return a 0, 1, 2, or 3
            if LIGHT_EN:
                LIGHT.on()
                time.sleep(0.2)

            if CAMERA_EN:
                image_file = CaptureImage.capture(data_path, str(image_count))
                image_count += 1




            if LIGHT_EN:
                LIGHT.off()

            # Now that the trash is identified, open the correct flap.
            if SERVO_EN:
                if (trash_id == 0):
                    SERVO_0.degree(SERVO_0_OPEN)
                elif (trash_id == 1):
                    SERVO_1.degree(SERVO_1_OPEN)
                elif (trash_id == 2):
                    SERVO_2.degree(SERVO_2_OPEN)

                # do nothing for id 3, trash would fall into hole

            # Correct flap is opened, now it's time to drop the trash
            if ACTUATOR_EN:
                ACTUATOR.speed(1)  # drop platform
                time.sleep(5)  # wait five seconds
                ACTUATOR.speed(-1)  # close platform
                # time.sleep(5)
                # ACTUATOR.speed(0)

            # Trash dropped, wait for trash to fall into hole and close flap
            if SERVO_EN:
                if (trash_id == 0):
                    time.sleep(2)
                    SERVO_0.degree(SERVO_0_CLOSE)
                elif (trash_id == 1):
                    time.sleep(4)
                    SERVO_1.degree(SERVO_1_CLOSE)
                elif (trash_id == 2):
                    time.sleep(6)
                    SERVO_2.degree(SERVO_2_CLOSE)

            # Check fullness of bins before restarting loop
            if SONAR_EN:
                if (trash_id == 0):
                    sonar_ping(0, SONAR_0, conn, SONAR_0_MIN, SONAR_0_MAX)
                elif (trash_id == 1):
                    sonar_ping(1, SONAR_1, conn, SONAR_1_MIN, SONAR_1_MAX)
                elif (trash_id == 2):
                    sonar_ping(2, SONAR_2, conn, SONAR_2_MIN, SONAR_2_MAX)
                else:
                    sonar_ping(3, SONAR_3, conn, SONAR_3_MIN, SONAR_3_MAX)

            # Power off servos until needed again
            if SERVO_EN:
                SERVO_0.off()
                SERVO_1.off()
                SERVO_2.off()

            # Set actuator speed to zero
            if ACTUATOR_EN:
                ACTUATOR.speed(0)
    except KeyboardInterrupt:
        if ACTUATOR_EN:
            ACTUATOR.speed(0)

        if SERVO_EN:
            SERVO_0.off()
            SERVO_1.off()
            SERVO_2.off()

        if SONAR_EN:
            SONAR_0.cancel()
            SONAR_1.cancel()
            SONAR_2.cancel()
            SONAR_3.cancel()

        conn.close()
        pi.stop()

    conn.close()
    pi.stop()
