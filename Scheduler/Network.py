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
from Scheduler.Frame import Frame, TreePath
from Scheduler.Dependency import DependencyTree
import xml.etree.ElementTree as Xml
import logging


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
    __sensing_control = None
    __replica_policy = None
    __replica_interval = None
    __list_replicas = []
    __minimum_time_switch = None
    __maximum_time_switch = None
    __hyper_period = None
    __utilization = None

    # Standard function definitions #

    def __init__(self):
        logging.basicConfig(level=logging.DEBUG)
        self.__num_frames = None
        self.__frames = []
        self.__num_links = None
        self.__links = []
        self.__collision_domains = []
        self.__num_dependencies = None
        self.__dependencies = None
        self.__sensing_control_period = None
        self.__sensing_control_time = None
        self.__sensing_control = None
        self.__replica_policy = None
        self.__replica_interval = None
        self.__list_replicas = []
        self.__minimum_time_switch = None
        self.__maximum_time_switch = None
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

    def get_number_frames(self):
        """
        Get the number of frames in the network
        :return: number of frames in the network
        """
        return self.__num_frames

    def get_hyper_period(self):
        """
        Get the hyper period of the network
        :return: hyper period of the network
        """
        return self.__hyper_period

    def get_utilization(self):
        """
        Get the utilization of the network
        :return: utilization of the network
        :rtype: float
        """
        return self.__utilization

    def get_frame_paths(self, frame_index):
        """
        Get the path root of a given frame index
        :param frame_index: frame index
        :return: path root
        :rtype: TreePath
        """
        return self.__frames[frame_index].get_path()

    def get_frame_splits(self, frame_index):
        """
        Get the frame splits matrix
        :param frame_index: index of the frame
        :type frame_index: int
        :return: splits matrix
        :rtype: list of list of int
        """
        return self.__frames[frame_index].get_splits()

    def get_frame_period(self, frame_index):
        """
        Get the period of a frame index
        :param frame_index: frame index
        :type frame_index: int
        :return: the frame period
        _:rtype: int
        """
        return self.__frames[frame_index].get_period()

    def get_frame_deadline(self, frame_index):
        """
        Get the frame deadline
        :param frame_index: frame index
        :type frame_index: int
        :return: frame deadline
        :rtype: int
        """
        return self.__frames[frame_index].get_deadline()

    def get_frame_paths_in_split(self, frame_index, split):
        """
        Get the list of paths that are in the split
        :param frame_index: index of the frame
        :param split: list of links index in a split
        :type frame_index: int
        :type split: list of in
        :return: list of paths in the split
        :rtype: list of TreePath
        """
        list_paths = []
        for path in self.get_frame_paths(frame_index):      # Go through all the paths of the frame
            if path.get_link_id() in split:                 # If the path link is in the split list
                list_paths.append(path)
                if len(list_paths) == len(split):           # If we found all paths, we finished
                    return list_paths
        return ValueError                                   # If we get here, we had an error

    def get_frame_path_from_link(self, frame_index, link):
        """
        Get the frame path for a given link
        :param frame_index: frame index
        :param link: link index in the path
        :type frame_index: int
        :type link: int
        :return: path
        :rtype: TreePath
        """
        for path in self.__frames[frame_index].get_path():      # For the paths in the frame
            if path.get_link_id() == link:                      # If the path link is the one we are searching, return
                return path

    def get_replica_policy(self):
        """
        Get the replica policy
        :return: replica policy
        :rtype: str
        """
        return self.__replica_policy

    def get_replica_interval(self):
        """
        Get the replica interval
        :return: replica interval
        :rtype: int
        """
        return self.__replica_interval

    def __create_sensing_control(self, period, time):
        """
        Creates a sensing and control block as a frame
        :param period: period of the sensing and control
        :param time: time of the sensing and control
        :return: 
        """
        # Create the sensing and control block as a frame
        self.__sensing_control = Frame()
        self.__sensing_control.set_period(period)

        # For the paths, it will be a unique path that contains all wireless links of the network
        path = [index for index, link in enumerate(self.__links) if link.get_type() == LinkType.wireless]
        self.__sensing_control.add_path(path)

        # For every path, add the time of the sensing and control
        for path in self.__sensing_control.get_path():
            path.set_transmission_time(time)
            path.init_offset(int(self.__hyper_period / period), 1)

    def get_sensing_control_path(self):
        """
        Get the sensing and control path
        :return: sensing and control path
        :rtype: list of TreePath
        """
        return self.__sensing_control.get_path()

    def get_sensing_control_period(self):
        """
        Get the sensing and control period
        :return: sensing and control period
        :rtype: int
        """
        return self.__sensing_control_period

    def get_minimum_time_switch(self):
        """
        Get the minimum time a frame has to stay in the switch
        :return: minimum time switch
        :rtype: int
        """
        return self.__minimum_time_switch

    def get_maximum_time_switch(self):
        """
        Get the maximum time a frame can stay in the switch
        :return: maximum time switch
        :rtype: int
        """
        return self.__maximum_time_switch

    def get_collision_domains(self):
        """
        Get the matrix of collision domains
        :return: collision domain matrix
        :rtype: list of list of int
        """
        return self.__collision_domains

    def link_in_collision_domain(self, link_index):
        """
        Search the link in the collision domain, if exists, return which collision domain, if not return None
        :param link_index: index of the link
        :type link_index: int
        :return: index of the collision domain if link is inside, None otherwise
        :rtype: int, None
        """
        for index, collision_domain in enumerate(self.__collision_domains):
            if link_index in collision_domain:
                return index
        return -1

    def get_dependencies(self):
        """
        Get the list of dependencies
        :return: list of dependencies
        :rtype: DependencyTree
        """
        return self.__dependencies

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
        self.__minimum_time_switch = int(general_information_xml.find('MinimumTimeSwitch').text)
        self.__maximum_time_switch = int(general_information_xml.find('MaximumTimeSwitch').text)
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

        # Create the sensing and control blocks if they exist
        if self.__sensing_control_period:
            self.__create_sensing_control(self.__sensing_control_period, self.__sensing_control_time)

        # Update the frame object to be prepared for allocate all the offsets
        self.update_frames(self.__links, self.__hyper_period, self.__list_replicas, self.__collision_domains)

    # Checker functions

    def check_schedule(self):
        """
        Check if all the constraints in the schedule are satisfied
        :return: True if satisfied, False if not
        """
        for frame_index, frame in enumerate(self.__frames):     # For all frames
            for path in frame.get_path():                   # For all paths of the frame
                for instance in range(path.get_num_instances()):  # For all instances and replicas
                    for replica in range(path.get_num_replicas()):

                        offset = path.get_offset(instance, replica)
                        # Check all other frames to see if there are collisions
                        for other_frame_index, other_frame in enumerate(self.__frames):
                            if frame_index != other_frame_index:
                                for other_path in other_frame.get_path():
                                    collision_domain = self.link_in_collision_domain(path.get_link_id())
                                    previous_collision_domain = self.link_in_collision_domain(other_path.get_link_id())
                                    if path.get_link_id() == other_path.get_link_id() or \
                                            (collision_domain >= 0 and collision_domain == previous_collision_domain):
                                        for other_instance in range(other_path.get_num_instances()):
                                            for other_replica in range(other_path.get_num_replicas()):
                                                other_offset = other_path.get_offset(other_instance, other_replica)
                                                if (offset < other_offset + other_path.get_transmission_time()) and \
                                                        (offset + path.get_transmission_time() > other_offset):
                                                    logging.debug('Checked error in contention free')
                                                    return False

                        # Check if frames are being send in sensing and control blocks
                        if self.__sensing_control_period:                           # If there is sensing and control
                            if self.link_in_collision_domain(path.get_link_id()) >= 0:   # If the link is wireless
                                for sensing_path in self.__sensing_control.get_path():
                                    for sensing_instance in range(sensing_path.get_num_instances()):
                                        other_offset = sensing_path.get_offset(sensing_instance, 0)
                                        if (offset < other_offset + sensing_path.get_transmission_time()) and \
                                                (offset + path.get_transmission_time() > other_offset):
                                            logging.debug('Checked error in contention free for sensing and control')
                                            return False

                        offset = path.get_offset(instance, replica)
                        # Check if the frame offsets satisfy its period
                        if offset > (frame.get_period() * (instance + 1)):
                            logging.debug('Checked error in frame period')
                            return False

                        # Check if the frame offsets satisfy its deadlines
                        if offset > ((frame.get_period() * instance) + frame.get_deadline()):
                            logging.debug('Checked error in frame deadline')
                            return False

                        # Check if replicas are working properly
                        if replica > 0:
                            distance = offset - path.get_offset(instance, replica - 1)
                            # If the distance is not the interval distance
                            if self.__replica_policy == 'Spread':
                                if distance != self.__replica_interval:
                                    logging.debug('Checked error in replica interval')
                                    return False
                            elif self.__replica_policy == 'Continuous':
                                if distance != path.get_transmission_time():
                                    logging.debug('Checked error in replica interval')
                                    return False

                        # Check if instances are ok
                        if instance > 0:
                            distance = offset - path.get_offset(instance - 1, replica)
                            if distance != frame.get_period():
                                logging.debug('Checked error in instance interval')
                                return False

                        # For all children paths of the current path
                        for index_child, child_path in enumerate(path.get_children()):

                            try:
                                # Check if the distance is between min and max
                                distance = child_path.get_offset(instance, replica) - path.get_offset(instance, replica)
                                if distance < self.__minimum_time_switch or distance > self.__maximum_time_switch:
                                    logging.debug('Checked error in time in switch for frame')
                                    return False

                                # Check if simultaneous dispatch is working
                                if index_child > 0:
                                    # Remember: If there are replicas, the simultaneous dispatch does not apply!
                                    if path.get_child(index_child - 1).get_offset(instance, replica) != \
                                            path.get_child(index_child).get_offset(instance, replica) and \
                                            path.get_num_replicas() == 0:
                                        logging.debug('Checked error in simultaneous dispatch')
                                        return False

                            except IndexError:              # Exception in cases one path has replicas and other not
                                pass

            # Check if dependencies hold
            if self.__num_dependencies > 0:
                dependency = self.__dependencies.get_dependency_by_frame(frame_index)
                if dependency:                              # If there is dependency
                    if dependency.get_parent():             # And is not the parent dependency of the tree
                        link = dependency.get_link_index()  # Get the offsets of the frame and its parent dependency
                        path = frame.get_path().get_path_by_link(link)
                        parent_link = dependency.get_parent().get_link_index()
                        parent_frame = self.__frames[dependency.get_parent().get_frame_index()]
                        parent_path = parent_frame.get_path().get_path_by_link(parent_link)

                        # Get the distance between both frames on the dependency and check if it holds
                        distance = path.get_offset(0, 0) - parent_path.get_offset(0, 0)
                        if (distance < dependency.get_waiting()) or \
                                (dependency.get_deadline() != 0 and distance > dependency.get_deadline()):
                            logging.debug('Checked error in dependency')
                            logging.debug('Frame => ' + str(frame_index))
                            logging.debug('Link => ' + str(link))
                            logging.debug('Offset => ' + str(path.get_offset(0, 0)))
                            logging.debug('Parent Frame => ' + str(dependency.get_parent().get_frame_index()))
                            logging.debug('Parent Link => ' + str(parent_link))
                            logging.debug('Parent Offset => ' + str(parent_path.get_offset(0, 0)))
                            logging.debug('Waiting => ' + str(dependency.get_waiting()))
                            logging.debug('Deadline => ' + str(dependency.get_deadline()))
                            logging.debug('Distance => ' + str(distance))
                            return False

        return True
