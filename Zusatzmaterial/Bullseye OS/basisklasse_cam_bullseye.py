"""
Alternative Klasse für die Kamera für die Verwendung auf RPIOS Bullseye 
"""


# import click
# import time
import numpy as np
from picamera2 import Picamera2
import cv2
import libcamera


class Camera(object):
    """Klasse für die Abfrage der Kamera mittels OpenCV

    Args:
        devicenumber int: Identifier for camera (OpenCV VideoCapture)
        buffersize int : Größe des Videobuffers (OpenCV VideoCapture)
        skip_frame int : Anzahl der zu verwerfenden Bilder bei Ausführung von get_frame
        height, width int: Höhe und Breite des Bildes
        flip bool: vertical flip of taken image
        colorspace str: Verwendeter Farbraum ('bgr','rgb', 'gray')
    Methoden:
        get_frame: Rückgabe eines Bildes als np.array unter Verwendung von skip_frame
        get_jpeg: Rückgabe eines Bildes als jpeg
        release: Freigabe der Kamera
        get_size (int,int): Rückgabe des Bildgröße
        get_size: Rückgabe der verwendeten Bildgröße
        check bool: Rückgabe von True wenn Kamera erreichbar

    """

    def __init__(
        self,
        buffersize: int = 1,
        skip_frame: int = 2,
        height: int = None,
        width: int = None,
        hflip: bool = True,
        vflip=True,
        colorspace: str = None,
    ) -> None:
        self.__skip_frame = skip_frame
        self.__PiCamera = Picamera2()
        self.__imgsize = self.__PiCamera.preview_configuration.size
        self.__width = width or self.__imgsize[0]
        self.__height = height or self.__imgsize[1]
        self.__hflip = hflip
        self.__vflip = vflip
        self.__colorspace = colorspace or "bgr"
        self.__config = self.__PiCamera.create_still_configuration(
            main={"size": (self.__width, self.__height), "format": "RGB888"},
            transform=libcamera.Transform(
                hflip=int(self.__hflip), vflip=int(self.__vflip)
            ),
            buffer_count=buffersize,
        )
        self.__PiCamera.configure(self.__config)
        self.__PiCamera.start()

    def get_size(self) -> tuple:
        """
        Return size of image returned be get_frame
        """
        return self.__imgsize

    def get_frame(self) -> np.array:
        """
        Reads frame from camera, applies tranformations to it and returns die resulting frame
        """
        if self.__skip_frame:
            for i in range(int(self.__skip_frame)):
                frame = self.__PiCamera.capture_array()
        frame = self.__PiCamera.capture_array()
        if self.__colorspace == "rgb":
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        elif self.__colorspace == "gray":
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            pass
        return frame

    def get_jpeg(self) -> np.array:
        """
        Reads frame from camera via get_frame and return the frame in jpg-format
        Primarily used for video-streaming
        """
        frame = self.get_frame()
        _, jpeg = cv2.imencode(".jpeg", frame)
        return jpeg

    def check(self) -> bool:
        """
        Test for accessibility of the camera
        """
        flag = self.__PiCamera.is_open
        return flag

    def release(self) -> None:
        """
        Releases camera and allows other processes to access it
        """
        self.__PiCamera.close()


if __name__ == "__main__":

    cam = Camera()
    while True:
        img = cam.get_frame()
        cv2.imshow("image", img)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    cam.release()
    print(" - camera released")
    cv2.destroyAllWindows()
