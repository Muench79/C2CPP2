IMAGE_WIDTH=640                 #width of images to save
IMAGE_HEIGHT=480                #height of images to save
RECORD_EACH_N_IMAGES=1          #only record each Nth image
MIN_RECORDING_SPEED=20          #only record if car is driving at least this speed
AXIS_ID_ANGLE = 0               #which joystick axis to use for the steering angle
AXIS_ID_FORWARD = 4             #which joystick axis to use for the driving forward (attention: output -1 .. +1)
AXIS_ID_BACKWARD = 5            #which joystick axis to use for the driving backward (attention: output -1 .. +1)
PRINT_JOYSTICK_VALUES = False   #print all axis events (even if not assigned)
SPEED_LIMIT = 50                #maximum speed to use for the joystick


import json
import os
#fake video device for pygame to avoid error message about missing video device
os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame

import os.path
import os
import uuid
from flask import Flask, Response, request
from cv2 import imwrite, putText
from datetime import datetime

from helpers.basisklassen_cam import Camera
from src.basecar import BaseCar

#loading calibration data
calibrated_references = [300, 300, 300, 300, 300]
try:
    with open("helpers/config.json", "r") as f:
        data = json.load(f)
        turning_offset = data["turning_offset"]
        forward_A = data["forward_A"]
        forward_B = data["forward_B"]
except:
    print("Keine geeignete Datei config.json gefunden!")
    turning_offset = 0
    forward_A = 0
    forward_B = 0
else:
    print("config.json geladen...")

# CREATION OF THE CAR & CAMERA
print("-" * 30)
print("CREATION CAR/CAMERA:")
car = BaseCar(turning_offset, forward_A, forward_B)
config_cam = dict(skip_frame=2, buffersize=1, colorspace="bgr", height=IMAGE_HEIGHT, width=IMAGE_WIDTH)
cam = Camera(**config_cam)
cam.recording = False
cam.runName = "DMRC"  # Part of string representing the name of the saved images
cam.runID = str(uuid.uuid4())[:8]  # Part of string representing the name of the saved images
cam.imageNumber = 0  # Part of string representing the name of the saved images
cam.imageFolder = "./images/"
if not os.path.isdir(cam.imageFolder):
    os.mkdir(cam.imageFolder)
    print("create", cam.imageFolder)
cam.recordSpeed = MIN_RECORDING_SPEED  # min speed necessary to record images
cam.k = RECORD_EACH_N_IMAGES  # represent frequency of images recording: 1 out of k

# check if camera is working
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
    #initialize joystick
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

    #exit if no joystick is found
    if len(joysticks) < 1:
        print("ERROR: No joystick detected!")   
        exit()


    #renember last angle / speed to check if it has to be changed
    last_angle = 0
    last_speed = 0
    
    print("...waiting for joystick input. Press CTRL+C to exit...")

    try:
        while keepPlaying:
            clock.tick(60)
            # check for changed joystick values and set angle and speed accordingly
            for event in pygame.event.get():
                if event.type == pygame.JOYAXISMOTION:
                    joy_angle = joysticks[0].get_axis(AXIS_ID_ANGLE)
                    joy_forward = joysticks[0].get_axis(AXIS_ID_FORWARD)
                    if joy_forward == 0.0:          #when button hasn't been used before, joystick is returning 0.0 even if it's in -1.0 position
                        joy_forward = -1.0
                    joy_backward = joysticks[0].get_axis(AXIS_ID_BACKWARD)
                    if joy_backward == 0.0:          #when button hasn't been used before, joystick is returning 0.0 even if it's in -1.0 position
                        joy_backward = -1.0
                    if PRINT_JOYSTICK_VALUES:
                        print(f"angle: {joy_angle} forward:{joy_forward} backward:{joy_backward}")

                    #calculation driving angle. Input: -1 (left) to +1 (right)
                    angle = int(90 + joy_angle * 45 + 0.5)

                    #calculation driving speed.
                    #buttons forward and backward return -1.0 if not touched and +1.0 on max position
                    #adding +1 to get 0.0 to 2.0 values
                    #dividing by 2 to get 0.0 to 1.0 values
                    speed = int(((joy_forward+1)/2 -(joy_backward + 1)/2)*SPEED_LIMIT)

                    if ((last_angle != angle) or (last_speed != speed)):
                        car.drive(angle, speed)

                    last_angle = angle
                    last_speed = speed
            
            # grab an image from the camera
            frame = cam.get_frame()
            cam.imageNumber += 1
            if (
                car.speed > cam.recordSpeed
                and cam.imageNumber % cam.k == 0
            ):
                currentTime = datetime.now().strftime("%Y%m%d_%H-%M-%S")
                filename = "IMG_{}_{}_{}_{:04d}_S{:03d}_A{:03d}.jpg".format(
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
    except KeyboardInterrupt:
        car.drive(0,0)
        print("...detected CTRL+C")
        print("Exit...")

if __name__ == '__main__':
    main()