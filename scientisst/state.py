class State:
    """
    ScientISST Device State class

    A state returned by ScientISST.state()

    """

    a = [0] * 8
    digital = [0] * 4
    battery = None
    bat_threshold = None
