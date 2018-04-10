import picamera
import os
import light


def capture(data_path, image_name):
    camera = picamera.PiCamera()
    camera.resolution = (1024, 1024)
    file_name = data_path + "/" + image_name + ".jpg"
    LIGHT = light.Light(18)
    LIGHT.on()
    camera.capture(file_name, resize = (480, 480))
    LIGHT.off()
    return file_name

if __name__ = '__main__':
    print ("Import the file and call capture with path to image and image name")
