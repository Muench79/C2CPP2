import numpy as np

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
        
        l = len(self.__clusters)
        if l == 1:
            # Es wurde genau ein Cluster gefunden
            if self.__clusters[0][0] + self.__cluster_size > self.__clusters[0][1]:
                # Cluster ist zu klein
                self.__clusters = []
            else:
                print(self.__center, self.__clusters[0][1])
                if self.__center < self.__clusters[0][1]:
                    self.__position = 2
                else:
                    self.__position = 1
                self.__x_1 = self.__clusters[0][0]
                self.__x_2 = self.__clusters[0][1]
                return self.__clusters[0][0], self.__clusters[0][1]
        elif l == 2:
            # Es wurden genau zwei Cluster gefunden
            if self.__clusters[0][0] + self.__cluster_size > self.__clusters[0][1] or \
               self.__clusters[1][0] + self.__cluster_size > self.__clusters[1][1] or \
               self.__clusters[0][1] + self.__cluster_distance > self.__clusters[1][0]:
                self.__clusters = []
            else:
                self.__x_left_inner = self.__clusters[0][1]
                self.__x_right_inner = self.__clusters[1][0]
                self.__x_left_outer = self.__clusters[0][0]
                self.__x_right_outer = self.__clusters[1][1]
                self.__position = 0
                return ((self.__clusters[0][0], self.__clusters[0][1]), 
                        (self.__clusters[1][0], self.__clusters[1][1]))
        else:
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