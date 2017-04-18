"""* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 *                                                                                                                     *
 *  Dependency Class                                                                                                   *
 *  Network Generator                                                                                                  *
 *                                                                                                                     *
 *  Created by Francisco Pozo on 18/04/17.                                                                             *
 *  Copyright © 2017 Francisco Pozo. All rights reserved.                                                              *
 *  Class for the dependencies between frames in the network.                                                          *
 *  A dependency is a relation between two frames at the end of its paths (as the information has been sent to the     *
 *  receiver).                                                                                                         *
 *  Dependencies can be for waiting a time from the predecessor frame transmission to the successor frame to be        *
 *  received. Also it can be that a successor must be received with a deadline of the predecessor frame. Of course it  *
 *  also can be combined both in a single dependency.                                                                  *
 *                                                                                                                     *
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * """


class Dependency:
    """
    Dependency class that defines the relation between two frames end paths in a minimum or/and maximum time
    """

    # Variable definitions #

    __predecessor_frame = None                  # Predecessor frame id number
    __predecessor_link = None                   # Predecessor link id number (must be end of the path)
    __successor_frame = None                    # Successor frame id number
    __successor_link = None                     # Successor link id number (must be end of the path)
    __waiting_time = None                       # Time for the successor frame to wait after the predecessor frame
    # 0 => no waiting time
    __deadline_time = None                      # Time that the successor frame has to be received after the predecessor
    # 0 => no deadline time

    # Standard function definitions #

    def __init__(self, predecessor_frame, predecessor_link, successor_frame, successor_link, waiting_time,
                 deadline_time):
        """
        Initialization of a dependency
        :param predecessor_frame: predecessor frame id
        :param predecessor_link: predecessor link id (must be end of the path)
        :param successor_frame: successor frame id
        :param successor_link: successor link id (must be end of the path)
        :param waiting_time: waiting time for the successor in microseconds
        :param deadline_time: deadline time for the successor in microseconds
        """
        # Check if there is consistency between deadline and waiting times
        if deadline_time < waiting_time and deadline_time != 0:
            raise ValueError("The waiting time must be smaller than the deadline time")
        if deadline_time == 0 and waiting_time == 0:
            raise ValueError("At least waiting or deadline time must be greater than 0")

        self.__predecessor_frame = predecessor_frame
        self.__predecessor_link = predecessor_link
        self.__successor_frame = successor_frame
        self.__successor_link = successor_link
        self.__waiting_time = waiting_time
        self.__deadline_time = deadline_time

    def __str__(self):
        """
        String call of the frame class
        :return: a string with the information
        """
        return_text = "Dependency information =>\n"
        return_text += "    Predecessor frame id : " + str(self.__predecessor_frame) + "\n"
        return_text += "    Predecessor link id  : " + str(self.__predecessor_link) + "\n"
        return_text += "    Successor frame id   : " + str(self.__successor_frame) + "\n"
        return_text += "    Successor link id    : " + str(self.__successor_link) + "\n"
        return_text += "    Waiting time         : " + str(self.__waiting_time) + " microseconds\n"
        return_text += "    Deadline time        : " + str(self.__deadline_time) + " microseconds"
        return return_text

    def get_predecessor_frame(self):
        """
        Gets the predecessor index frame
        :return: predecessor index frame
        """
        return self.__predecessor_frame

    def set_predecessor_frame(self, predecessor_frame):
        """
        Set the predecessor frame 
        :param predecessor_frame: predecessor frame index
        :return: 
        """
        self.__predecessor_frame = predecessor_frame

    def get_predecessor_link(self):
        """
        Gets the predecessor lind id
        :return: predecessor link id
        """
        return self.__predecessor_link

    def set_predecessor_link(self, predecessor_link):
        """
        Set the predecessor link
        :param predecessor_link: predecessor link index 
        :return: 
        """
        self.__predecessor_link = predecessor_link

    def get_successor_frame(self):
        """
        Gets the successor index frame
        :return: successor index frame
        """
        return self.__successor_frame

    def set_successor_frame(self, successor_frame):
        """
        Set successor frame
        :param successor_frame: successor frame index
        :return: 
        """
        self.__successor_frame = successor_frame

    def get_successor_link(self):
        """
        Gets the successor link id
        :return: successor link id
        """
        return self.__successor_link

    def set_successor_link(self, successor_link):
        """
        Set successor link
        :param successor_link: successor link index
        :return: 
        """
        self.__successor_link = successor_link

    def get_waiting_time(self):
        """
        Gets the waiting time
        :return: waiting time
        """
        return self.__waiting_time

    def set_waiting_time(self, waiting_time):
        """
        Set waiting time
        :param waiting_time: waiting time in microseconds
        :return: 
        """
        self.__waiting_time = waiting_time

    def get_deadline_time(self):
        """
        Gets the deadline time
        :return: deadline time
        """
        return self.__deadline_time

    def set_deadline_time(self, deadline_time):
        """
        Set deadline time
        :param deadline_time: deadline time in microseconds
        :return: 
        """
        self.__deadline_time = deadline_time

    def set_dependency_time(self, waiting_time=None, deadline_time=None):
        """
        Set the waiting and deadline times
        :param waiting_time: set the waiting time in microseconds
        :param deadline_time: set the deadline time in microseconds
        :return: 
        """
        # Check if there is consistency between deadline and waiting times
        if deadline_time < waiting_time and deadline_time != 0:
            raise ValueError("The waiting time must be smaller than the deadline time")
        if deadline_time == 0 and waiting_time == 0:
            raise ValueError("At least waiting or deadline time must be greater than 0")

        self.__waiting_time = waiting_time
        self.__deadline_time = deadline_time
