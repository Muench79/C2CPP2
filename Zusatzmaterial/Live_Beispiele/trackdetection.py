import numpy as np
import logging

# create logger
logger = logging.getLogger(__name__)


# # create format handler (console)
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# console_handler.setFormatter(formatter)
# console_handler.setLevel(logging.INFO)

# # create format handler (file)
# file_handler = logging.FileHandler(os.path.join(PATH, 'log.log'), mode="a", encoding="utf-8")
# file_handler.setFormatter(formatter)
# file_handler.setLevel(logging.DEBUG)

# add handler
# logger.addHandler(console_handler)
# logger.addHandler(file_handler)

def log_message(level, message, **kwargs):
    # Format and generate log message
    param_str = ' | '.join(f'{key}={value}' for key, value in kwargs.items())
    full_message = f'{message} | {param_str}' if param_str else message

    if level == 'DEBUG':
        logger.debug(full_message)
    elif level == 'INFO':
        logger.info(full_message)
    elif level == 'WARNING':
        logger.warning(full_message)
    elif level == 'ERROR':
        logger.error(full_message)
    elif level == 'CRITICAL':
        logger.critical(full_message)
    else:
        logger.info(f'Unbekannter Loglevel \'{level}\': {full_message}')

class TrackDetection:
    def __init__(self, center=100, cluster_size = 5, cluster_distance = 50):
        self.__center = center
        self.__clusters = []
        self.__cluster_size = cluster_size
        self.__cluster_distance = cluster_distance
        self.__x_left_inner = 0
        self.__x_left_outer = 0
        self.__x_right_inner = 0
        self.__x_right_outer = 0
        self.__x_1 = 0
        self.__x_2 = 0
        self.__position = None

    def center(self, center):
        self.__center = center
    
    def cluster_settings(self, cluster_size, cluster_distance):
        self.__cluster_size = cluster_size
        self.__cluster_distance = cluster_distance

    def row(self, row):
        self.__x_left_inner = None
        self.__x_left_outer = None
        self.__x_right_inner = None
        self.__x_right_outer = None
        self.__x_1 = None
        self.__x_2 = None
        self.__position = None

        # Alle Indizes der weißen Pixel in einer Zeile suchen
        white_pixels = np.where(row == 255)[0]
        self.__clusters = []
        if len(white_pixels) > 0:
            #Es sind weiße Pixel vorhanden
            # Start Pixel
            start = white_pixels[0]
            # Vorheriges Pixel
            prev = white_pixels[0]
            for x in white_pixels[1:]:
                # Alle Pixel durchlaufen, beginnend bei Index 1 (ab dem zweiten Element)
                if x == prev + 1:
                    # Aktueller Pixel liegt direkt neben dem vorherigen Pixel
                    prev = x # Bereich erweitern
                else:
                    # Aktueller Pixel liegt nicht direkt neben dem vorherigen Pixel
                    self.__clusters.append((start, prev))
                    start = x
                    prev = x
            self.__clusters.append((start, prev))
        log_message('DEBUG', 'Clusters-RAW', clusters=self.__clusters)
        
        l = len(self.__clusters)
        if l == 1:
            # Es wurde genau ein Cluster gefunden
            if self.__clusters[0][0] + self.__cluster_size > self.__clusters[0][1]:
                # Cluster ist zu klein
                log_message('ERROR', '1 Cluster: zu klein', clusters=self.__clusters)
                self.__clusters = []
            else:
                #print(self.__center, self.__clusters[0][1])
                if self.__center < self.__clusters[0][1]:
                    log_message('DEBUG', '1 Cluster: befindet sich rechts', clusters=self.__clusters)
                    self.__position = 2
                else:
                    log_message('DEBUG', '1 Cluster: befindet sich links', clusters=self.__clusters)
                    self.__position = 1
                self.__x_1 = self.__clusters[0][0]
                self.__x_2 = self.__clusters[0][1]
                return self.__clusters[0][0], self.__clusters[0][1]
        elif l == 2:
            # Es wurden genau zwei Cluster gefunden
            c_1_size = self.__clusters[0][0] + self.__cluster_size > self.__clusters[0][1]
            c_2_size = self.__clusters[1][0] + self.__cluster_size > self.__clusters[1][1]
            c_1_2_distance = self.__clusters[0][1] + self.__cluster_distance > self.__clusters[1][0]
            if c_1_size or c_2_size or c_1_2_distance:
                log_message('ERROR', '2 Cluster: Distanz oder Größe', c_1_size=c_1_size, c_2_size=c_2_size, c_1_2_distance=c_1_2_distance, clusters=self.__clusters)
                self.__clusters = []
            else:
                self.__x_left_inner = self.__clusters[0][1]
                self.__x_right_inner = self.__clusters[1][0]
                self.__x_left_outer = self.__clusters[0][0]
                self.__x_right_outer = self.__clusters[1][1]
                self.__position = 0
                log_message('DEBUG', '2 Cluster: Spur detektiert', clusters=self.__clusters)
                return ((self.__clusters[0][0], self.__clusters[0][1]), 
                        (self.__clusters[1][0], self.__clusters[1][1]))
        else:
            log_message('ERROR', 'X Cluster: Anzahl fehlerhaft', count=len(self.__clusters), clusters=self.__clusters)
            self.__clusters = []
    
    @property
    def position(self):
        return self.__position
    
    @property
    def x_left_inner(self):
        return self.__x_left_inner
    
    @property
    def x_left_outer(self):
        return self.__x_left_outer
    
    @property
    def x_right_inner(self):
        return self.__x_right_inner
    
    @property
    def x_right_outer(self):
        return self.__x_right_outer
    
    @property
    def x_1(self):
        return self.__x_1
    
    @property
    def x_2(self):
        return self.__x_2
    
    @property
    def count(self):
        return len(self.__clusters)

    @property
    def distance_outer(self):
        if self.__x_left_outer is not None and self.__x_right_outer is not None:
            print(self.__x_left_outer, self.__x_right_outer)
            return self.__x_right_outer - self.__x_left_outer
    
    @property
    def distance_inner(self):
        if self.__x_left_inner is not None and self.__x_right_inner is not None:
            return self.__x_right_inner - self.__x_left_inner

if __name__ == '__main__':
     td = TrackDetection(10)
     x = np.array([0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,255,255,255,255,255,255,255,0])
     print(td.row(x), td.position, td.x_1, td.x_2, td.distance_outer, td.distance_inner)