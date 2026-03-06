# -*- coding: utf-8 -*-

import numpy as np
import logging

# Logger erstellen
logger = logging.getLogger(__name__)

def log_message(level, message, **kwargs):
    # Formatrierung und Meldungen erstellen
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
    """
    Erkennt Spurmarkierungen in einer binären Bildzeile und bestimmt die Spurposition.
    Version: 1.0.0
    
    Die Klasse analysiert eine einzelne Zeile eines binären Bildes (0 = schwarz,
    255 = weiß), fasst zusammenhängende weiße Pixel zu Clustern zusammen und
    bewertet diese anhand ihrer Größe und ihres Abstands. Auf Basis der erkannten
    Cluster wird bestimmt, ob sich die Spur links, rechts oder mittig befindet.
    Zusätzlich stellt die Klasse verschiedene geometrische Eigenschaften wie
    innere und äußere Begrenzungen der Spur zur Verfügung.

    Args:
        center (int, optional): Referenzpunkt (z. B. Bildmitte), der zur
            Bestimmung der relativen Position eines einzelnen Clusters genutzt
            wird. Standardwert: 100.
        cluster_size (int, optional): Minimale Größe eines Clusters, damit er als
            gültig gewertet wird. Standardwert: 5.
        cluster_distance (int, optional): Mindestabstand zwischen zwei Clustern,
            damit sie als getrennte Spurmarkierungen gelten. Standardwert: 50.
    """

    def __init__(self, center=100, cluster_size = 5, cluster_distance = 50):
        """
        Initialisiert die Spurdetektion mit den angegebenen Parametern.

        Args:
            center (int): Referenzpunkt zur Bestimmung der Spurposition.
            cluster_size (int): Minimale Größe eines gültigen Clusters.
            cluster_distance (int): Mindestabstand zwischen zwei Clustern.
        """
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
        """
        Setzt den Referenzpunkt für die Spurposition neu.

        Args:
            center (int): Neuer Referenzpunkt, typischerweise die Bildmitte.
        """
        self.__center = center
    
    def cluster_settings(self, cluster_size, cluster_distance):
        """
        Aktualisiert die Mindestgröße und den Mindestabstand für Cluster.

        Args:
            cluster_size (int): Minimale Clustergröße.
            cluster_distance (int): Mindestabstand zwischen zwei Clustern.
        """
        self.__cluster_size = cluster_size
        self.__cluster_distance = cluster_distance

    def row(self, row):
        """
        Analysiert eine binäre Bildzeile, erkennt Cluster und bestimmt die Spurposition.

        Die Methode sucht zusammenhängende weiße Pixel (255), gruppiert sie zu Clustern
        und bewertet diese anhand der eingestellten Parameter. Je nach Anzahl und
        Qualität der Cluster wird die Spurposition bestimmt.

        Args:
            row (numpy.ndarray): Eine eindimensionale Zeile eines binären Bildes.

        Returns:
            tuple | None:
                - Bei einem gültigen Einzelcluster: (x_start, x_ende)
                - Bei zwei gültigen Clustern: ((x1_start, x1_ende), (x2_start, x2_ende))
                - None, wenn keine gültige Spur erkannt wurde.
        """
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
        """
        Gibt die erkannte Spurposition zurück.

        Returns:
            int | None:
                - 0: Spur erkannt (zwei Cluster)
                - 1: Spur links (ein Cluster links des Zentrums)
                - 2: Spur rechts (ein Cluster rechts des Zentrums)
                - None: keine gültige Spur erkannt
        """
        return self.__position
    
    @property
    def x_left_inner(self):
        """
        Gibt die innere Grenze des linken Clusters zurück.

        Returns:
            int | None: Innere linke Begrenzung oder None.
        """
        return self.__x_left_inner
    
    @property
    def x_left_outer(self):
        """
        Gibt die äußere Grenze des linken Clusters zurück.

        Returns:
            int | None: Äußere linke Begrenzung oder None.
        """
        return self.__x_left_outer
    
    @property
    def x_right_inner(self):
        """
        Gibt die innere Grenze des rechten Clusters zurück.

        Returns:
            int | None: Innere rechte Begrenzung oder None.
        """
        return self.__x_right_inner
    
    @property
    def x_right_outer(self):
        """
        Gibt die äußere Grenze des rechten Clusters zurück.

        Returns:
            int | None: Äußere rechte Begrenzung oder None.
        """
        return self.__x_right_outer
    
    @property
    def x_1(self):
        """
        Startkoordinate eines einzelnen Clusters.

        Returns:
            int | None: Startposition oder None.
        """
        return self.__x_1
    
    @property
    def x_2(self):
        """
        Endkoordinate eines einzelnen Clusters.

        Returns:
            int | None: Endposition oder None.
        """
        return self.__x_2
    
    @property
    def count(self):
        """
        Anzahl der erkannten Cluster.

        Returns:
            int: Anzahl der Cluster.
        """
        return len(self.__clusters)

    @property
    def distance_outer(self):
        """
        Abstand zwischen den äußeren Grenzen zweier Cluster.

        Returns:
            int | None: Abstand oder None, wenn nicht berechenbar.
        """
        if self.__x_left_outer is not None and self.__x_right_outer is not None:
            print(self.__x_left_outer, self.__x_right_outer)
            return self.__x_right_outer - self.__x_left_outer
    
    @property
    def distance_inner(self):
        """
        Abstand zwischen den inneren Grenzen zweier Cluster.

        Returns:
            int | None: Abstand oder None, wenn nicht berechenbar.
        """
        if self.__x_left_inner is not None and self.__x_right_inner is not None:
            return self.__x_right_inner - self.__x_left_inner

if __name__ == '__main__':
     td = TrackDetection(10)
     x = np.array([0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,255,255,255,255,255,255,255,0])
     print(td.row(x), td.position, td.x_1, td.x_2, td.distance_outer, td.distance_inner)