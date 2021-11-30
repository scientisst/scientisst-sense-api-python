class InvalidAddressError(Exception):
    """
    The specified address is invalid.
    """

    def __init__(self):
        super().__init__("The specified address is invalid.")


class BTAdapterNotFoundError(Exception):
    """
    No Bluetooth adapter was found.
    """

    def __init__(self):
        super().__init__("No Bluetooth adapter was found.")


class DeviceNotFoundError(Exception):
    """
    The device could not be found.
    """

    def __init__(self):
        super().__init__("The device could not be found.")


class ContactingDeviceError(Exception):
    """
    The computer lost communication with the device.
    """

    def __init__(self):
        super().__init__("The computer lost communication with the device.")


class PortCouldNotBeOpenedError(Exception):
    """
    The communication port does not exist or it is already being used.
    """

    def __init__(self):
        super().__init__(
            "The communication port does not exist or it is already being used."
        )


class PortInitializationError(Exception):
    """
    The communication port could not be initialized.
    """

    def __init__(self):
        super().__init__("The communication port could not be initialized.")


class DeviceNotIdleError(Exception):
    """
    The device is not idle.
    """

    def __init__(self):
        super().__init__("The device is not idle.")


class DeviceNotInAcquisitionError(Exception):
    """
    The device is not in acquisition mode.
    """

    def __init__(self):
        super().__init__("The device is not in acquisition mode.")


class InvalidParameterError(Exception):
    """
    Invalid parameter.
    """

    def __init__(self):
        super().__init__("Invalid parameter.")


class NotSupportedError(Exception):
    """
    Operation not supported by the device.
    """

    def __init__(self):
        super().__init__("Operation not supported by the device.")


class UnknownError(Exception):
    """
    Unknown error: `message`.
    """

    def __init__(self, message=""):
        super().__init__("Unknown error: {}".format(message))
