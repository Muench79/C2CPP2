# -*- coding: utf-8 -*-

import numpy as np

# Klasse HSVRange
class HSVRange:
    """
    Repräsentiert einen HSV-Farbbereich mit unterer und oberer Grenze.
    Version: 1.0.0

    Die Klasse speichert die Grenzen als NumPy-Arrays und stellt Methoden
    sowie Properties bereit, um die Werte zu setzen oder auszulesen.

    Args:
        lb (array-like): Untere Grenze des HSV-Bereichs als (H, S, V)-Matrix.
        ub (array-like): Obere Grenze des HSV-Bereichs als (H, S, V)-Matrix.

    Attributes:
        lb (numpy.ndarray): Untere HSV-Grenze.
        ub (numpy.ndarray): Obere HSV-Grenze.
    """

    def __init__(self, lb, ub):
        """
        Initialisiert einen neuen HSV-Farbbereich.

        Args:
            lb (array-like): Untere HSV-Grenze.
            ub (array-like): Obere HSV-Grenze.
        """

        self.lb = np.array(lb)
        self.ub = np.array(ub)

    def __str__(self):
        """
        Erzeugt eine formatierte Tabellenansicht des HSV-Farbbereichs.

        Die Ausgabe enthält die drei Farbkanäle Hue, Saturation und Value
        sowie deren jeweilige minimale und maximale Werte. Die Darstellung
        erfolgt in tabellarischer Form mit ausgerichteten Spalten, um eine
        gut lesbare Übersicht zu ermöglichen.

        Returns:
            str: Formatierte Tabelle mit den Min- und Max-Werten der
                HSV-Kanäle.
        """
        try:
            return ('HSV-Range:\n'
                f'{"Channel":<12}  {"Min":>3}   {"Max":<3}\n'
                f'{"-" * 12}  {"-" * 3}   {"-" * 3}\n'
                f'{"Hue":<12}: {int(self.lb[0]):>3} - {int(self.ub[0]):<3}\n'
                f'{"Saturation":<12}: {int(self.lb[1]):>3} - {int(self.ub[1]):<3}\n'
                f'{"Value":<12}: {int(self.lb[2]):>3} - {int(self.ub[2]):<3}\n')
        except:
            return 'Keine HSV-Range vorhanden'
        
    def lower_bound(self, lb):
        """
        Setzt die untere HSV-Grenze.

        Args:
            lb (array-like): Neue untere Grenze als (H, S, V)-Matrix.
        """
        self.lb = np.array(lb)

    def upper_bound(self, ub):
        """
        Setzt die obere HSV-Grenze.

        Args:
            ub (array-like): Neue obere Grenze als (H, S, V)-Matrix.
        """
        self.ub = np.array(ub)

    @property
    def lowerbound(self):
        """
        Gibt die untere HSV-Grenze zurück.

        Returns:
            numpy.ndarray: Untere Grenze des HSV-Bereichs.
        """
        return self.lb
    
    @property
    def upperbound(self):
        """
        Gibt die obere HSV-Grenze zurück.

        Returns:
            numpy.ndarray: Obere Grenze des HSV-Bereichs.
        """
        return self.ub
    
    @property
    def h_min_max(self):
        """
        Gibt das minimale und maximale Hue-Intervall zurück.

        Returns:
            tuple: (H_min, H_max)
        """
        return self.lb[0],self.ub[0] 

    @property
    def s_min_max(self):
        """
        Gibt das minimale und maximale Saturation-Intervall zurück.

        Returns:
            tuple: (S_min, S_max)
        """
        return self.lb[1],self.ub[1] 
    
    @property
    def v_min_max(self):
        """
        Gibt das minimale und maximale Value-Intervall zurück.

        Returns:
            tuple: (V_min, V_max)
        """
        return self.lb[2],self.ub[2]

if __name__ == '__main__':
    hsv_range = HSVRange((10,20,20), (40,50,60))
    print(hsv_range)
    