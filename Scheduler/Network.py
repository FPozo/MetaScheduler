"""* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * 
 *                                                                                                                     *
 *  Network Class                                                                                                      *
 *  Scheduler                                                                                                          *
 *                                                                                                                     *
 *  Created by Francisco Pozo on 25/04/17.                                                                             *
 *  Copyright © 2017 Francisco Pozo. All rights reserved.                                                              *
 *                                                                                                                     *
 *  Class that contains the information of the network.                                                                *
 *  A network has the information of all the frames and its dependencies (Application constraints of different types), *
 *  modeled in a relationship tree both by minimum and maximum time for the frame to be transmitted after.             *
 *  All frames are saved in a list.                                                                                    *
 *  Additions of new relations between frames are supposed to be added here, while the behavior is on the schedule,    *
 *  as done with the application constraints, period and deadlines.                                                    *
 *  Additionally, also reads the input network.                                                                        *
 *                                                                                                                     *
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * """

from Scheduler.Link import *
from Scheduler.Frame import Frame
from Scheduler.Dependency import DependencyTree
import xml.etree.ElementTree as Xml


class Network:
    """
    Network Class with the information of the network, also reading the network
    """

    # Variable definitions #

    __num_frames = None
    __frames = []
    __num_links = None
    __links = []
    __collision_domains = []
    __num_dependencies = None
    __dependencies = None
    __sensing_control_period = None
    __sensing_control_time = None
    __replica_policy = None
    __replica_interval = None
    __list_replicas = []
    __hyper_period = None
    __utilization = None

    # Standard function definitions #

    def __init__(self):
        self.__num_frames = None
        self.__frames = []
        self.__num_links = None
        self.__links = []
        self.__collision_domains = []
        self.__num_dependencies = None
        self.__dependencies = None
        self.__sensing_control_period = None
        self.__sensing_control_time = None
        self.__replica_policy = None
        self.__replica_interval = None
        self.__list_replicas = []
        self.__hyper_period = None
        self.__utilization = None

    def update_frames(self, links, hyper_period, list_replicas, collision_domains):
        """
        Init all the frames to be prepared to allocate all instances and replicas of frames
        :param links: list of links objects of the network that contains information of the speed
        :param hyper_period: hyper period of the network
        :param list_replicas: list of replicas for every collision domain
        :param collision_domains: matrix with the links in every collision domain
        :return: 
        """
        for frame in self.__frames:            # For all frames, init correctly its information
            frame.update_frame(links, hyper_period, list_replicas, collision_domains)

    # Input XML Functions

    def __get_network_information_xml(self, filename):
        """
        Get general information from the network xml file
        :param filename: name and relative direction of the xml file
        :return: 
        """
        # Open the file if exists
        try:
            tree = Xml.parse(filename)
        except:
            raise Exception("Could not read the xml file")
        root = tree.getroot()

        # Get all the valuable variables from the general information of the network
        general_information_xml = root.find('GeneralInformation')
        self.__num_frames = int(general_information_xml.find('NumberFrames').text)
        self.__num_links = int(general_information_xml.find('NumberLinks').text)
        self.__num_dependencies = int(general_information_xml.find('NumberDependencies').text)
        try:
            self.__sensing_control_period = int(general_information_xml.find('SensingControlPeriod').text)
        except ValueError:
            self.__sensing_control_period = None
        try:
            self.__sensing_control_time = int(general_information_xml.find('SensingControlTime').text)
        except ValueError:
            self.__sensing_control_time = None
        self.__replica_policy = general_information_xml.find('ReplicaPolicy').text
        try:
            self.__replica_interval = int(general_information_xml.find('ReplicaInterval').text)
        except ValueError:
            self.__replica_interval = None
        try:
            self.__list_replicas = [int(x) for x in general_information_xml.find('Replicas').text.split(';')]
        except ValueError:
            pass
        self.__hyper_period = int(general_information_xml.find('HyperPeriod').text)
        self.__utilization = float(general_information_xml.find('Utilization').text)

    def __get_links_information_xml(self, filename):
        """
        Get the information (speed and type) of all the links in the network
        :param filename: file name with the relative path of the network input xml file
        :return: 
        """
        # Open the file if exists
        try:
            tree = Xml.parse(filename)
        except:
            raise Exception("Could not read the xml file")
        root = tree.getroot()

        # Read all the links information
        links_xml = root.findall('NetworkDescription/Links/Link')
        for link_xml in links_xml:                                  # For all links in the network
            link_type = None
            if link_xml.attrib['category'] == 'Wired':              # Read if is wired or wireless
                link_type = LinkType.wired
            elif link_xml.attrib['category'] == 'Wireless':
                link_type = LinkType.wireless
            speed = int(link_xml.find('Speed').text)                # Read the speed
            self.__links.append(Link(speed, link_type))             # Add a new Link object to the list of links

        # Little check to see if everything is going as planned
        if self.__num_links != len(self.__links):
            raise Exception('Something wrong with the links')

    def __get_collision_domains_xml(self, filename):
        """
        Get the collision domains information from the network input XML file
        :param filename: name of the input xml file and the relative direction
        :return: 
        """
        # Open the file if exists
        try:
            tree = Xml.parse(filename)
        except:
            raise Exception("Could not read the xml file")
        root = tree.getroot()

        # For all collision domains read its link and add them in the collision domain matrix
        collision_domains_xml = root.findall('NetworkDescription/CollisionDomains/CollisionDomain')
        for collision_domain_xml in collision_domains_xml:          # For all collision domains
            links_xml = collision_domain_xml.findall('Link')
            links = []
            for link_xml in links_xml:                              # For all links save it on the links list
                links.append(int(link_xml.text))
            self.__collision_domains.append(links)                  # Add the list to the collision domain

    def __get_frames_information_xml(self, filename):
        """
        Get the information of all the frames in the network
        :param filename: file name and relative path of the network input XML file
        :return: 
        """
        # Open the file if exists
        try:
            tree = Xml.parse(filename)
        except:
            raise Exception("Could not read the xml file")
        root = tree.getroot()

        # Get the needed information of all the frames
        frames_xml = root.findall('TrafficInformation/Frames/Frame')
        for frame_xml in frames_xml:
            self.__frames.append(Frame())           # Add to the list an empty frame object that we will fill later one

            # Add basic information to the frame Object
            self.__frames[-1].set_period(int(frame_xml.find('Period').text))
            self.__frames[-1].set_deadline(int(frame_xml.find('Deadline').text))
            self.__frames[-1].set_size(int(frame_xml.find('Size').text))

            # Add paths
            paths_xml = frame_xml.findall('Paths/Path')
            for path_xml in paths_xml:              # For every path, we transform the string to integer list and add it
                path = [int(x) for x in path_xml.text.split(';')]
                self.__frames[-1].add_path(path)

            # Add splits
            splits_xml = frame_xml.findall('Splits/Split')
            for split_xml in splits_xml:            # For every split, we transform the string to integer list
                split = [int(x) for x in split_xml.text.split(';')]
                self.__frames[-1].add_split(split)

    def __get_dependencies_information_xml(self, filename):
        """
        Get the information of all the dependencies and save it in the list of dependency trees
        :param filename: name of the network input xml file and the relative path
        :return: 
        """
        # Open the file if exists
        try:
            tree = Xml.parse(filename)
        except:
            raise Exception("Could not read the xml file")
        root = tree.getroot()

        # Get the information of all dependencies
        dependencies_xml = root.findall('TrafficInformation/Dependencies/Dependency')
        self.__dependencies = DependencyTree()
        for dependency_xml in dependencies_xml:
            predecessor_frame = int(dependency_xml.find('PredecessorFrame').text)
            predecessor_link = int(dependency_xml.find('PredecessorLink').text)
            successor_frame = int(dependency_xml.find('SuccessorFrame').text)
            successor_link = int(dependency_xml.find('SuccessorLink').text)
            waiting_time = int(dependency_xml.find('WaitingTime').text)
            deadline_time = int(dependency_xml.find('DeadlineTime').text)
            self.__dependencies.add_dependency(predecessor_frame, predecessor_link, successor_frame, successor_link,
                                               waiting_time, deadline_time)

    def parse_network_xml(self, filename):
        """
        Parse the given network and initialize all the information in the class
        :param filename: name and relative direction of the network XML input file
        :return: 
        """

        # Get the needed information from the file and save it in this class
        self.__get_network_information_xml(filename)
        self.__get_links_information_xml(filename)
        self.__get_collision_domains_xml(filename)
        self.__get_frames_information_xml(filename)
        self.__get_dependencies_information_xml(filename)

        # Update the frame object to be prepared for allocate all the offsets
        self.update_frames(self.__links, self.__hyper_period, self.__list_replicas, self.__collision_domains)
