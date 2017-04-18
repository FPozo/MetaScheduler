"""* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 *                                                                                                                     *
 *  Frame Class                                                                                                        *
 *  Network Generator                                                                                                  *
 *                                                                                                                     *
 *  Created by Francisco Pozo on 18/04/17.                                                                             *
 *  Copyright © 2016 Francisco Pozo. All rights reserved.                                                              *
 *                                                                                                                     *
 *  Class for the frames in the network. A frame has only one node (end system) sender and one or multiple (also end   *
 *  systems) receivers. All frames must have a period in microseconds and a in bytes in the range of the Ethernet      *
 *  Standard frames. They may also have a deadline (also in microseconds).                                             *
 *                                                                                                                     *
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * """


class Frame:
    """
    Class that has all the information of a time-triggered frame in the network
    """

    # Variable definitions #

    __sender = None                         # End system sender id of the frame
    __receivers = []                        # List of end systems receivers id of the frame
    __size = None                           # Size of the frame in bytes (it must be between 72 and 1526 bytes)
    __period = None                         # Period in microseconds of the frame
    __deadline = None                       # Deadline in microseconds of the frame (if 0 => same as period)

    # Standard function definitions #

    def __init__(self, sender, receivers, period=10000, deadline=0, size=1526):
        """
        Initialization of the needed values of a time-triggered frame
        :param sender: end system sender id
        :param receivers: list of end systems receivers id
        :param period: period in microseconds
        :param deadline: deadline in microseconds, should be smaller than the period
        :param size: size in bytes of the frame, must be in the Ethernet Standard range
        """
        # Check if the integer range fits in the standard Ethernet Standard value
        if size < 72 or size > 1526:                                    # The size must be inside the Ethernet Standard
            raise ValueError("The frame size must be between 72 and 1526 (Ethernet Standard)")

        self.__sender = sender
        self.__receivers = receivers
        self.__period = period
        if deadline == 0:                                               # If deadline is 0 => deadline = period
            self.__deadline = period
        else:
            self.__deadline = deadline
        self.__size = size

    def __str__(self):
        """
        String call of the frame class
        :return: a string with the information
        """
        return_text = "Frame information =>\n"
        return_text += "    Sender id     : " + str(self.__sender) + "\n"
        return_text += "    Receivers ids : " + str(self.__receivers) + "\n"
        return_text += "    Period        : " + str(self.__period) + " microseconds\n"
        return_text += "    Deadline      : " + str(self.__deadline) + " microseconds\n"
        return_text += "    Size          : " + str(self.__size) + " bytes"
        return return_text

    def get_period(self):
        """
        Gets the period of the frame
        :return: frame period
        """
        return self.__period

    def set_period(self, period):
        """
        Sets the period of the frame
        :param period: period in microseconds
        :return: None
        """
        self.__period = period

    def get_deadline(self):
        """
        Gets the deadline of the frame
        :return: deadline period
        """
        return self.__deadline

    def set_deadline(self, deadline):
        """
        Sets the deadline of the frame
        :param deadline: deadline in microseconds
        :return: None
        """
        if deadline == 0:                                               # If deadline is 0 => deadline = period
            self.__deadline = self.get_period()
        else:
            self.__deadline = deadline

    def get_size(self):
        """
        Gets the size of the frame
        :return: size frame
        """
        return self.__size

    def set_size(self, size):
        """
        Sets the size of the frame
        :param size: deadline in microseconds
        :return: None
        """
        # Check if the integer range fits in the standard Ethernet Standard value
        if size < 72 or size > 1526:                                    # The size must be inside the Ethernet Standard
            raise ValueError("The frame size must be between 72 and 1526 (Ethernet Standard)")

        self.__size = size

    def get_sender(self):
        """
        Gets the sender of the frame
        :return: frame sender
        """
        return self.__sender

    def set_sender(self, sender):
        """
        Set the sender of the frame
        :param sender: sender of the frame
        :return: 
        """
        self.__sender = sender

    def get_num_receivers(self):
        """
        Gets the number of receivers from that frame
        :return: number of receivers
        """
        return len(self.__receivers)

    def get_receivers(self):
        """
        Gets the list of receivers
        :return: receivers list
        """
        return self.__receivers

    def set_receivers(self, receivers):
        """
        Set the list of receivers
        :param receivers: list of receivers
        :return: 
        """
        self.__receivers = receivers
