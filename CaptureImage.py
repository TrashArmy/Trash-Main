import picamera


def capture(data_path, image_name):
    # camera should be a PiCamera object
    with picamera.PiCamera() as camera:
        camera.resolution = (1024, 1024)
        file_name = data_path + "/" + image_name + ".jpg"
        camera.capture(file_name, resize=(480, 480))
    return file_name


if __name__ == '__main__':
    print("Import the file and call capture with path to image and image name")
