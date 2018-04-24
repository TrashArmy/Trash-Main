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

MODEL_FOLDER_NAME = './mobilenet_model'
# Path to frozen detection graph. This is the actual model that is used for the object detection.
PATH_TO_CKPT = MODEL_FOLDER_NAME + '/retrained_graph.pb'
# List of the strings that is used to add correct label for each box.
PATH_TO_LABELS = os.path.join('mobilenet_model', 'retrained_labels.txt')
NUM_CLASSES = 4 # Number of classes classifier has
CLASSIFICATION_DICT = {"aluminum can": 3, "plastic cup": 2, "plastic bottle": 2,
                        "paper cup": 0}
INPUT_HEIGHT = 224
INPUT_WIDTH = 224
INPUT_STD = 128
INPUT_MEAN = 128
INPUT_LAYER = "input"
OUTPUT_LAYER = "final_result"
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

def load_graph(model_file):
    graph = tf.Graph()
    graph_def = tf.GraphDef()
    with open(model_file, "rb") as f:
        graph_def.ParseFromString(f.read())
        with graph.as_default():
            tf.import_graph_def(graph_def)
    return graph

def read_tensor_from_image_file(file_name, input_height=299, input_width=299, input_mean=0, input_std=255):
    input_name = "file_reader"
    output_name = "normalized"
    file_reader = tf.read_file(file_name, input_name)
    if file_name.endswith(".png"):
        image_reader = tf.image.decode_png(file_reader, channels = 3, name='png_reader')
    elif file_name.endswith(".gif"):
        image_reader = tf.squeeze(tf.image.decode_gif(file_reader, name='gif_reader'))
    elif file_name.endswith(".bmp"):
        image_reader = tf.image.decode_bmp(file_reader, name='bmp_reader')
    else:
        image_reader = tf.image.decode_jpeg(file_reader, channels = 3, name='jpeg_reader')
    float_caster = tf.cast(image_reader, tf.float32)
    dims_expander = tf.expand_dims(float_caster, 0);
    resized = tf.image.resize_bilinear(dims_expander, [input_height, input_width])
    normalized = tf.divide(tf.subtract(resized, [input_mean]), [input_std])
    sess = tf.Session()
    result = sess.run(normalized)
    return result


def load_labels(label_file):
    label = []
    proto_as_ascii_lines = tf.gfile.GFile(label_file).readlines()
    for l in proto_as_ascii_lines:
        label.append(l.rstrip())
    return label

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
    graph = load_graph(PATH_TO_CKPT)
    labels = load_labels(PATH_TO_LABELS)

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
                try:
                    image_file = CaptureImage.capture(data_path, str(image_count))
                    image_count += 1
                except:
					print ("Image could not be taken")
					continue
            if LIGHT_EN:
                LIGHT.off()

            image_tensor = read_tensor_from_image_file(image_file, input_height=INPUT_HEIGHT, input_width=INPUT_HEIGHT, input_mean=INPUT_MEAN, input_std=INPUT_STD)
            input_name = "import/" + INPUT_LAYER
            output_name = "import/" + OUTPUT_LAYER
            input_operation = graph.get_operation_by_name(input_name);
            output_operation = graph.get_operation_by_name(output_name);
            with tf.Session(graph=graph) as sess:
                start = time.time()
                results = sess.run(output_operation.outputs[0], {input_operation.outputs[0]: image_tensor})
                end=time.time()
            results = np.squeeze(results)
            top_k = results.argsort()[-5:][::-1]
            top_k = top_k[0]
            print (labels[top_k])
            if (results[top_k] > 0.6):
                trash_id = CLASSIFICATION_DICT.get(labels[top_k])
            else:
                trash_id = 1
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
