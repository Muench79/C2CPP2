
class Cropp:
    """
    Repräsentiert einen zweidimensionalen Zuschneidebereich (Crop-Bereich).

    Der Bereich wird durch zwei Wertepaare definiert:
    - ns: Nord-Süd-Ausrichtung (vertikale Begrenzung)
    - we: West-Ost-Ausrichtung (horizontale Begrenzung)

    Beide Wertepaare werden intern als Listen gespeichert und können über
    Setter-Methoden oder Properties geändert bzw. ausgelesen werden.

    Attributes:
        __ns (list[int]): Vertikaler Bereich als [min, max].
        __we (list[int]): Horizontaler Bereich als [min, max].
    """

    def __init__(self):
        """
        Initialisiert den Crop-Bereich mit Standardwerten.

        Standardwerte:
            ns = [0, 100]
            we = [0, 100]
        """
        self.__ns = [0,100]
        self.__we = [0,100]
    
    def __str__(self):
        """
        Gibt eine formatierte Zeichenkette zurück, die den aktuellen Crop-Bereich
        übersichtlich darstellt.

        Returns:
            str: Formatierte Darstellung des Crop-Bereichs.
        """
        return (f'Cropp:\n'
                f'ns: {self.__ns[0]:>3} {self.__ns[1]:<3}\n'
                f'we: {self.__we[0]:>3} {self.__we[1]:<3}')
    
    def set_ns(self, value):
        """
        Setzt den Nord-Süd-Bereich.

        Args:
            value (list[int]): Neuer Bereich als [min, max].
        """
        self.__ns = value
    
    def set_we(self, value):
        """
        Setzt den West-Ost-Bereich.

        Args:
            value (list[int]): Neuer Bereich als [min, max].
        """
        self.__we = value
    
    @property
    def ns(self):
        """
        Gibt den aktuellen Nord-Süd-Bereich zurück.

        Returns:
            list[int]: Bereich als [min, max].
        """
        return self.__ns
    
    @property
    def we(self):
        """
        Gibt den aktuellen West-Ost-Bereich zurück.

        Returns:
            list[int]: Bereich als [min, max].
        """
        return self.__we

if __name__ == '__main__':
    cropp = Cropp()
    cropp.set_ns([10,100])
    cropp.set_we([30,25])
    print(cropp)