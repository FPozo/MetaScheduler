"""* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 *                                                                                                                     *
 *  Link Class                                                                                                         *
 *  Scheduler                                                                                                          *
 *                                                                                                                     *
 *  Created by Francisco Pozo on 25/04/17.                                                                             *
 *  Copyright © 2017 Francisco Pozo. All rights reserved.                                                              *
 *                                                                                                                     *
 *  Class for the links in the network. Quite simple class that only defines the speed and link type (wired or         *
 *  wireless)                                                                                                          *
 *                                                                                                                     *
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * """

from enum import Enum  # Import enumerate as is not built-in in python


class LinkType(Enum):
    """
    Class to define the different link types
    """
    wired = 1
    wireless = 2


class Link:
    """
    Class that has all the information of a communication link (speed and type)
    """

    # Variable definitions #

    __speed = 0  # Speed in MB/s
    __link_type = 0  # Link type

    # Standard function definitions #

    def __init__(self, speed=100, link_type=LinkType.wired):
        """
        Initialization of the link, if no values given it creates an standard Deterministic Ethernet Link
        :param speed: Speed of the link in MB/s
        :param link_type: Type of the network (wired or wireless)
        """
        self.__speed = speed
        self.__link_type = link_type

    def __str__(self):
        """
        String call of the link class
        :return: a string with the information
        """
        # Check what kind of link it is
        if self.__link_type == LinkType.wired:
            return "Wired link with speed " + str(self.__speed) + "MB/s"
        else:
            return "Wireless link with speed " + str(self.__speed) + "MB/s"

    def get_type(self):
        """
        Get the link type
        :return: Link type
        """
        return self.__link_type

    def set_type(self, link_type):
        """
        Set the link type
        :param link_type: Link type
        :return: 
        """

        self.__link_type = link_type

    def get_speed(self):
        """
        Get the speed of the link
        :return: Link speed
        """
        return self.__speed

    def set_speed(self, speed):
        """
        Set the speed
        :param speed: Link speed in MB/s
        :return: 
        """

        self.__speed = speed
