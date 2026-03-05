import os
#fake video device for pygame to avoid error message about missing video device
os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame
import time

import os.path
import os
import uuid
from cv2 import imwrite, putText
from datetime import datetime

from basisklassen_cam import Camera
from basecar import BaseCar

ANGLE_AXIS_ID = 2
SPEED_AXIS_ID = 3

# CREATION OF THE CAR & CAMERA
print("-" * 30)
print("CREATION CAR/CAMERA:")
car = BaseCar()
config_cam = dict(skip_frame=2, buffersize=1, colorspace="bgr", height=480, width=640)
cam = Camera(**config_cam)
cam.recording = True
cam.runName = "DMRC"  # Part of string representing the name of the saved images
cam.runID = str(uuid.uuid4())[:8]  # Part of string representing the name of the saved images
cam.imageNumber = 0  # Part of string representing the name of the saved images
cam.imageFolder = "./images/"
if not os.path.isdir(cam.imageFolder):
    os.mkdir(cam.imageFolder)
    print("create", cam.imageFolder)
cam.recordSpeed = 20  # min speed necessary to record images
cam.k = 5  # represent frequency of images recording: 1 out of k

try:
    testFrame = cam.get_frame()
except:
    hasCam = False
finally:
    if testFrame is not None:
        hasCam = True
    else:
        hasCam = False
if hasCam:
    print("- Camera available.")
    CameraStateStr = "off"
else:
    print(" - Camera NOT available!")
    CameraStateStr = "not available"
print("Car bereit")

def main():
    pygame.init()
    joysticks = []
    clock = pygame.time.Clock()
    keepPlaying = True

    # for al the connected joysticks
    for i in range(0, pygame.joystick.get_count()):
        # create an Joystick object in our list
        joysticks.append(pygame.joystick.Joystick(i))
        # initialize the appended joystick (-1 means last array item)
        joysticks[-1].init()
        # print a statement telling what the name of the controller is
        print ("Detected joystick "),joysticks[-1].get_name(),"'"

    time.sleep(2)
    last_angle = 0
    last_speed = 0

    angle = 90
    speed = 0
    button_held = False
    while keepPlaying:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.JOYHATMOTION:
                hat = joysticks[0].get_hat(0)
                angle = int(90 - hat[1] * 45)

            if event.type == pygame.JOYBUTTONDOWN:
                if event.button == 0:
                    button_held = True
            if event.type == pygame.JOYBUTTONUP:
                if event.button == 0:
                    button_held = False
            speed = 30 if button_held else 0
        car.drive2(speed)
        last_angle += int((angle-last_angle)*0.4)
        car.steering_angle = last_angle
        # check for changed joystick values and set angle and speed accordingly
        # for event in pygame.event.get():
        #     print(event.type)
        #     if event.type == pygame.JOYAXISMOTION:
        #         print(f"Axis {event.axis}: {event.value:.3f}")
        #     #if event.type == 9:
        #         joy_angle = joysticks[0].get_axis(ANGLE_AXIS_ID)
        #         joy_speed = joysticks[0].get_axis(SPEED_AXIS_ID)
        #         print(event.type, joy_angle, joy_speed)
        #         angle = int(90 + joy_angle * 45 + 0.5)
        #         speed = int(-joy_speed*50)

                # if ((last_angle != angle) or (last_speed != speed)):
                #     car.drive(angle, speed)

                # last_angle = angle
                # last_speed = speed
        
        # grab an image from the camera
        frame = cam.get_frame()
        cam.imageNumber += 1
        if (
            car.speed > cam.recordSpeed
            and cam.imageNumber % cam.k == 0
        ):
            currentTime = datetime.now().strftime("%Y%m%d_%H-%M-%S")
            filename = "IMG_{}_{}_{}_{:04d}_S{:03d}_A{:03d}.png".format(
                cam.runName,
                cam.runID,
                currentTime,
                cam.imageNumber,
                car.speed,
                car.steering_angle,
            )
            print(filename)
            imwrite(cam.imageFolder + filename, frame)
            print("RECORD:", cam.imageNumber, filename)
            text = "RECORDING {}".format(cam.imageNumber)
            putText(frame, text, (10, 460), 1, 4, (0, 0, 255), 3, 1)
        else:
            pass

if __name__ == '__main__':
    main()