"""* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 *                                                                                                                     *
 *  Network Class                                                                                                      *
 *  Network Generator                                                                                                  *
 *                                                                                                                     *
 *  Created by Francisco Pozo on 14/04/17.                                                                             *
 *  Copyright © 2017 Francisco Pozo. All rights reserved.                                                              *
 *  Class with the information of the network and algorithms to create them                                            *
 *  Networks are generated with a description language capable to describe any network that has no cycles.             *
 *  Different number of frames and types of frames frames (single, broadcast, etc) and dependencies and attributes of  *
 *  the network are also created.                                                                                      *
 *  As the number of parameters is large, standard configuration of parameters are also available.                     *
 *                                                                                                                     *
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * """

from NetworkGenerator.Node import *
from NetworkGenerator.Dependency import *
from NetworkGenerator.Frame import *
from NetworkGenerator.Link import *
from random import random, choice, shuffle, randint
from copy import deepcopy
from functools import reduce
from xml.dom import minidom
import xml.etree.ElementTree as Xml
import networkx as nx
import logging
import copy
import os
import shutil
import hashlib


# Auxiliary functions

def gcd(a, b):
    """Return greatest common divisor using Euclid's Algorithm."""
    while b:
        a, b = b, a % b
    return a


def lcm(a, b):
    """Return lowest common multiple."""
    return a * b // gcd(a, b)


def lcm_multiple(*args):
    """Return lcm of args."""
    return reduce(lcm, args)


class NetworkConfiguration:
    """
    Class that contains all the needed parameters to create a network, it also provides some functions to remove 
    impossible configurations
    """

    network = None
    link = None
    preprocessed_collision_domains = []
    replicas = []
    replica_policy = None
    replica_interval = None
    minimum_switch = None
    maximum_switch = None
    sensing_control_period = None
    sensing_control_time = None
    num_frames = None
    single = None
    local = None
    multi = None
    broad = None
    periods = []
    per_periods = []
    deadlines = []
    sizes = []
    num_dependencies = None
    min_depth = None
    max_depth = None
    min_children = None
    max_children = None
    min_time_waiting = None
    max_time_waiting = None
    min_time_deadline = None
    max_time_deadline = None
    waiting = None
    deadline = None
    waiting_deadline = None
    hyper_period = None
    utilization = None

    def set_topology_parameters(self, network, link):
        """
        Sets the topology parameters
        :param network: network description
        :param link: link description
        :return: 
        """
        self.network = network
        self.link = link

    def set_collision_domains_parameter(self, collision_domains):
        """
        Set the number of collision domains parameter
        :param collision_domains: number of collision domains
        :return: 
        """
        self.preprocessed_collision_domains = collision_domains

    def set_replicas_parameter(self, list_replicas):
        """
        Set the list of replicas parameters
        :param list_replicas: list of replicas
        :return: 
        """
        self.replicas = list_replicas

    def set_replica_policy_parameter(self, replica_policy):
        """
        Set the replica policy parameter
        :param replica_policy: replica policy string
        :return: 
        """
        self.replica_policy = replica_policy

    def set_replica_interval_parameter(self, replica_interval):
        """
        Set the replica interval parameter
        :param replica_interval: replica interval
        :return: 
        """
        self.replica_interval = replica_interval

    def set_minimum_switch_parameter(self, minimum_switch):
        """
        Set the minimum switch time parameter
        :param minimum_switch: minimum time parameter
        :return: 
        """
        self.minimum_switch = minimum_switch

    def set_maximum_switch_parameter(self, maximum_switch):
        """
        Set the maximum time in the switch parameter
        :param maximum_switch: maximum time in switch parameter
        :return: 
        """
        self.maximum_switch = maximum_switch

    def set_sensing_control_period_parameter(self, sensing_control_period):
        """
        Set the sensing and control period parameter
        :param sensing_control_period: sensing and control period
        :return: 
        """
        self.sensing_control_period = sensing_control_period

    def set_sensing_control_time_parameter(self, sensing_control_time):
        """
        Set the sensing and control time parameter
        :param sensing_control_time: sensing and control time
        :return: 
        """
        self.sensing_control_time = sensing_control_time

    def set_traffic_information_parameters(self, num_frames, single, local, multiple, broadcast):
        """
        Set the traffic information parameters
        :param num_frames: number of frames
        :param single: percentage of frames that are sent to a single end system
        :param local: percentage of frames that have length of 2 
        :param multiple: percentage of frames that are sent to [2, number of frames - 1] end systems
        :param broadcast: percentage of frames that are sent to all the end systems
        :return: 
        """
        self.num_frames = num_frames
        self.single = single
        self.local = local
        self.multi = multiple
        self.broad = broadcast

    def set_frames_description_parameters(self, periods, per_periods, deadlines, sizes):
        """
        Set the frame description parameters
        :param periods: list of periods
        :param per_periods: list of per_periods
        :param deadlines: list of deadlines
        :param sizes: list of sizes
        :return: 
        """
        self.periods = periods
        self.per_periods = per_periods
        self.deadlines = deadlines
        self.sizes = sizes

    def set_dependency_parameters(self, num_dependencies, min_depth, max_depth, min_children, max_children,
                                  min_time_waiting, max_time_waiting, min_time_deadline, max_time_deadline, waiting,
                                  deadline, waiting_deadline):
        """
        Set the dependency parameters
        :param num_dependencies: 
        :param min_depth: 
        :param max_depth: 
        :param min_children: 
        :param max_children: 
        :param min_time_waiting: 
        :param max_time_waiting: 
        :param min_time_deadline: 
        :param max_time_deadline: 
        :param waiting: 
        :param deadline: 
        :param waiting_deadline: 
        :return: 
        """
        self.num_dependencies = num_dependencies
        self.min_depth = min_depth
        self.max_depth = max_depth
        self.min_children = min_children
        self.max_children = max_children
        self.min_time_waiting = min_time_waiting
        self.max_time_waiting = max_time_waiting
        self.min_time_deadline = min_time_deadline
        self.max_time_deadline = max_time_deadline
        self.waiting = waiting
        self.deadline = deadline
        self.waiting_deadline = waiting_deadline

    def formalize_configuration(self):
        """
        Changes the variables that are useless to a None value
        :return: 
        """
        # If there is no replicas, then we do not have replica configuration parameters
        if self.replicas is None or all(replica == 0 for replica in self.replicas):
            self.replica_interval = None
            self.replica_policy = None

        # If one of the values of the sensing and control is 0, then both are not valid
        if self.sensing_control_time == 0 or self.sensing_control_period == 0:
            self.sensing_control_period = None
            self.sensing_control_time = None

        # If the replica policy is continuous, the interval is irrelevant
        if self.replica_policy == 'Continuous':
            self.replica_interval = None

        # If there are no collision domains, it means there is no wireless transmissions, and then no need of wireless
        # configurations
        if len(self.preprocessed_collision_domains) == 0:
            self.replicas = None
            self.replica_interval = None
            self.replica_policy = None
            self.sensing_control_time = None
            self.sensing_control_period = None

        # If there is no dependencies make irrelevant the other values
        if self.num_dependencies == 0:
            self.min_depth = None
            self.max_depth = None
            self.min_children = None
            self.max_children = None
            self.min_time_waiting = None
            self.max_time_waiting = None
            self.min_time_deadline = None
            self.max_time_deadline = None
            self.waiting = None
            self.deadline = None
            self.waiting_deadline = None

    def is_it_valid(self):
        """
        Check if the current configuration is valid (There is a possibility that the network can be scheduled)
        :return: True if valid, False if not valid
        """
        # If the sensing and control time is larger than the period
        if (self.sensing_control_time is not None and self.sensing_control_period is not None) and \
                self.sensing_control_time > self.sensing_control_period:
            return False

        # If the minimum time for a frame in the switch is larger than the maximum
        if self.minimum_switch > self.maximum_switch:
            return False

        return True

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return self.__dict__ != other.__dict__


class Network:
    """
    Network class with the information of the network, frames and dependencies on it and algorithms to construct them
    """

    # Variable definitions #

    __graph = None  # Network Graph built with the NetworkX package
    __switches = []  # List with all the switches identifiers in the network
    __end_systems = []  # List with all the end systems identifiers  in the network
    __links = []  # List with all the links IDENTIFIERS in the network
    __links_object_container = []  # List with all the links OBJECTS in the network (cannot be saved in graph)
    __collision_domains = []  # Matrix with list of links that share the same wireless frequency
    __paths = []  # Matrix with the number of end systems as index for x and y, it contains
    # a list of links to describe the path from end system x to end system y, None if x = y
    __aux_frames = []  # Auxiliary list with all frames in the network to help create dependencies
    __frames = []  # List with all the frames OBJECTS in the network
    __num_dependencies = 0  # Number of dependencies
    __dependencies = []  # List of dependencies

    # Standard function definitions #

    def __init__(self):
        """
        Initialization of an empty network
        """
        logging.basicConfig(level=logging.DEBUG)
        self.__graph = nx.Graph()
        self.__switches = []
        self.__end_systems = []
        self.__links = []
        self.__links_object_container = []
        self.__collision_domains = []
        self.__paths = []
        self.__frames = []
        self.__aux_frames = []
        self.__num_dependencies = 0
        self.__dependencies = []

    # Private function definitions #

    def __add_switch(self):
        """
        Add a new switch into the network
        :return: None
        """
        # Add into the Networkx graph a new node with type => object.switch node, id => switch number
        self.__graph.add_node(self.__graph.number_of_nodes(), type=Node(NodeType.switch), id=len(self.__switches))
        self.__switches.append(self.__graph.number_of_nodes() - 1)  # Save the identifier of Networkx

    def __add_end_system(self):
        """
        Add a new end system into the network
        :return:
        """
        # Add into the Networkx graph a new node with type => object.end_system node, id => end system number
        self.__graph.add_node(self.__graph.number_of_nodes(), type=Node(NodeType.end_system), id=len(self.__switches))
        self.__end_systems.append(self.__graph.number_of_nodes() - 1)  # Save the identifier of Networkx

    def __add_link(self, source, destination, link_type=LinkType.wired, speed=100):
        """
        Adds a bi-directional link (two logical links) between a source node and a destination node
        :param source: node source
        :param destination: node destination
        :param link_type: type of link (wired/wireless)
        :param speed: link speed
        :return: None
        """
        # Add into the Networkx graph a new link between two node with type => object.link, id => link number
        self.__graph.add_edge(source, destination, type=Link(speed=speed, link_type=link_type),
                              id=self.__graph.number_of_edges() - 1)
        self.__links.append([source, destination])  # Saves the same info in our link list with nodes
        self.__links.append([destination, source])
        self.__links_object_container.append(Link(speed=speed, link_type=link_type))  # Saves the object with same index
        self.__links_object_container.append(Link(speed=speed, link_type=link_type))

    def __add_link_information(self, pre_col_dom, links, num_links, branch, parent_node):
        """
        Reads the link information and check if is needed to add it to the collision domain, then creates the link
        :param links: links description
        :param num_links: index of the number of links in the execution
        :param branch: branch to add the link
        :param parent_node: parent node to link to
        :return: 
        """
        if links is not None:  # If there is a description of the link, add the information
            # Add the link type wired if is 'w' or wireless if is 'x'
            # IMPORTANT: Note that we take the link id from num_links (as they are not sorted in the
            # links array!)
            link_type = LinkType.wired if links[num_links + branch][0] == 'w' else LinkType.wireless
            speed = int(links[num_links + branch][1:])  # The speed is the rest of the string
        else:  # If not, we assume all links are wired with 100MB/s speed
            link_type = LinkType.wired
            speed = 100

        # If the link is included in a collision domain, it is added to the collision domain matrix
        for index_col, collision_domain in enumerate(pre_col_dom):
            for index_link, link in enumerate(collision_domain):
                # If the link is included in the collision domain preprocessed array, save it now with the
                # correct link value now that we know it (both directions)
                if pre_col_dom[index_col][index_link] == (num_links + branch) + 1:
                    # The real number of link is the last added link, this information is in the graph
                    self.__collision_domains[index_col].append((self.__graph.number_of_edges()) * 2)
                    self.__collision_domains[index_col].append(((self.__graph.number_of_edges()) * 2) + 1)

        # Add the link with all the information
        self.__add_link(parent_node, self.__graph.number_of_nodes() - 1, link_type, speed)

    def __change_switch_to_end_system(self, switch):
        """
        Change an already introduced switch to an end system (needed for the create network function)
        :param switch: id of the switch
        :return: None
        """
        self.__graph.node[switch]['type'] = Node(NodeType.end_system)  # Update the information into the graph
        self.__graph.node[switch]['id'] = len(self.__end_systems)
        self.__end_systems.append(switch)  # Update the information into our lists
        self.__switches.remove(switch)

    def __recursive_create_network(self, description, pre_col_dom, links, parent_node, num_calls, num_links):
        """
        Auxiliary recursive function for create network
        :param description: description of the network already parsed into integers
        :param links: list with description of the links parameters in tuples
        :param parent_node: number of the parent node of the actual call
        :param num_calls: number of calls that has been done to the function (to iterate the description string)
        :param num_links: number of links that has been done to the function (to map the links in the correct order as
        they are not correctly ordered in the links array for the perspective of the recursive function)
        :return: the updated number of calls and the number of links to track correctly during the recursion
        """
        try:  # Try to catch wrongly formulated network descriptions
            if description[num_calls] < 0:  # Create new leads as end systems and link them to the parent node
                # For all the new leafs, add the end system to the network and link it to the parent node
                for leaf in range(abs(description[num_calls])):
                    self.__add_end_system()
                    self.__add_link_information(pre_col_dom, links, num_links, leaf, parent_node)
                # Return subtracting the last links created by the last branch from the number of links, we want the
                # number of links when the branch is starting, no after (due to recursion)
                return num_links - int(description[num_calls]), num_calls

            elif description[num_calls] == 0:  # Finished branch, change switch parent node into an end system
                self.__change_switch_to_end_system(parent_node)
                return num_links, num_calls  # Return as the branch is finished

            elif description[num_calls] > 0:  # Create new branches with switches
                it_links = num_links  # Save the starting number of links to iterate
                last_call_link = 0  # Create variable to save the last link that was call (to return after)

                for branch in range(description[num_calls]):  # For all new branches, create the switch and link it
                    self.__add_switch()
                    new_parent = self.__graph.number_of_nodes() - 1  # Save the new parent node for later
                    # Read all the information of the link and add it
                    self.__add_link_information(pre_col_dom, links, num_links, branch, parent_node)

                    # Check which link is calling, if last call is bigger, set it to last call
                    if last_call_link > it_links + (int(description[num_calls]) - branch):
                        links_to_call = last_call_link
                    else:
                        links_to_call = it_links + (int(description[num_calls] - branch))
                    # Call the recursive for the new branch, we save the last call link to recover it when we return
                    # after the branch created by this recursive call is finished
                    last_call_link, num_calls = self.__recursive_create_network(description, pre_col_dom, links,
                                                                                new_parent, num_calls + 1,
                                                                                links_to_call)

                return last_call_link, num_calls  # Return when all branches have been created and closed

        except IndexError:
            raise ValueError("The network description is wrongly formulated, there are open branches")

    # Public function definitions #

    def create_topology(self, network_description, pre_col_dom=None, link_description=None):
        """
        Creates a network with the description received
        :param network_description: string with the data of the network, it follows an special description
        :param pre_col_dom: matrix with the collision domains saved from before (but links are not normalized yet)
        :param link_description: string with the description of all the links, if None, all are wired and 100 MBs
        There are numbers divided by semicolons, every number indicates the number of children for the actual switch
        If the number is negative, it means it has x end systems: ex: -5 means 5 end systems
        If the number is 0, it means the actual switch is actually an end_system
        The order of the descriptions goes with depth. If a node has no more children you backtrack to describe the next
        node.
        Every link has a description of its speed and its type (wired/wireless), first letter is the type and number
        w100 => wired with 100 MBs
        x10 => wireless with 10 MBs
        :return: None
        """
        # Copy the preprocessed collision domain before deleting it
        self.__init__()                     # Clean everything when creating a new topology
        for _ in range(len(pre_col_dom)):   # Create the real collision domain matrix
            self.__collision_domains.append([])
        description_array = network_description.split(';')  # Separate the description string in an array
        description = [int(numeric_string) for numeric_string in description_array]  # Parse the string into int
        if link_description is not None:    # Separate also the link description if exist
            links = link_description.split(';')
        else:
            links = None

        # Start the recursive call with parent switch 0
        self.__add_switch()
        # Num links and num calls are auxiliary variables to map the order in which the links are created and to check
        # if the creation of the network was successful
        num_links, num_calls = self.__recursive_create_network(description, pre_col_dom, links, 0, 0, 0)

        # Check if there are additional elements that should not be in the network
        if num_calls != len(description) - 1:
            raise ValueError("The network description is wrongly formulated, there are extra elements")

    def generate_paths(self):
        """
        Generate all the shortest paths from every end systems to every other end system
        Fills the 3 dimensions path matrix, first dimension is the sender, second dimension is the receiver,
        third dimension is a list of INDEXES for the dataflow link list (not links ids, pointers to the link lists)
        :return: None
        """
        for i in range(self.__graph.number_of_nodes()):  # Init the path 3-dimension matrix with empty arrays
            self.__paths.append([])
            for j in range(self.__graph.number_of_nodes()):
                self.__paths[i].append([])

        # We iterate over all the senders and receivers
        for sender in self.__end_systems:
            for receiver in self.__end_systems:
                if sender != receiver:  # If they are not the same search the path
                    # As the paths save the indexes, of the links, we need to search them with tuples of nodes, we then
                    # iterate through all nodes find by the shortest path function of Networkx, and skip the first
                    # iteration as we do not have a tuple of nodes yet
                    first_iteration = False
                    previous_node = None
                    for node in nx.shortest_path(self.__graph, sender, receiver):  # For all nodes in the path
                        if not first_iteration:
                            first_iteration = True
                        else:  # Find the index in the link list with the actual and previous node
                            self.__paths[sender][receiver].append(self.__links.index([previous_node, node]))
                        previous_node = node

    @staticmethod
    def __calculate_splits(paths):
        """
        Calculate the splits matrix of a given path matrix.
        For every column on the matrix path, search if there are different links and add then in a new split row.
        :param paths: 3-dimensional path matrix
        :return: 3-dimensional split matrix
        """
        splits = []  # Matrix to save all the splits
        path_index = 0  # Horizontal index of the path matrix
        split_index = 0  # Vertical index of the split matrix
        first_path_flag = False  # Flag to identify a first found path
        found_split_flag = False  # Flag to identify a split has been found
        paths_left = len(paths)  # Paths left to be checked
        while paths_left > 1:  # While we did not finish all different splits
            paths_left = 0  # Initialize the paths left
            for i in range(len(paths)):  # For all the different paths
                try:  # The try is needed because a path ended will raise an exception
                    if not first_path_flag:  # Check if it is the first path found
                        first_split = paths[i][path_index]  # Save to compare with other paths to check new splits
                        first_path_flag = True
                    else:
                        if paths[i][path_index] != first_split:  # If it is difference, a new split has been found
                            if not found_split_flag:  # If is the first split, save both links
                                splits.append([])
                                splits[split_index].append(first_split)
                                found_split_flag = True
                            if paths[i][path_index] not in splits[split_index]:  # If the split is not in the list
                                splits[split_index].append(paths[i][path_index])  # Save the link split
                    paths_left += 1  # The path has not ended if no exception had been raised
                except IndexError:  # If there is an exception, the path ended and we continue
                    pass
            if found_split_flag:  # If a split has been found
                split_index += 1  # Increase the split index
                found_split_flag = False
            first_path_flag = False  # Update the path flags and the path index for next iteration
            path_index += 1
        return splits  # Return the filled splits matrix

    def generate_frames(self, number_frames, per_broadcast=1.0, per_single=0.0, per_locally=0.0, per_multi=0.0):
        """
        Generate frames for the network. You can choose the number of frames and the percentage of every type
        This is the basic function and will create all possible attributes of the network to default
        Percentages will be balanced alone
        :param number_frames: number of frames for the network
        :param per_broadcast: percentage of frames to be sent to all the end systems
        :param per_single: percentage of frames to be sent to a single receiver
        :param per_locally: percentage of frames to be send to all receivers with minimum path length
        :param per_multi: percentage of frames to be send to a random number of end systems
        :return: None
        """
        # Normalize the percentage so the sum is always 1.0
        sum_per = float(per_broadcast + per_single + per_locally + per_multi)
        per_broadcast /= sum_per
        per_multi /= sum_per
        per_locally /= sum_per
        per_single /= sum_per

        # Iterate for all the frames that needs to be created
        for frame in range(number_frames):
            frame_type = random()  # Generate random to see which type of frame is
            sender = choice(self.__end_systems)  # Select the sender end system

            # Select receivers depending of the frame type
            if frame_type < per_broadcast:  # Broadcast frame
                receivers = list(self.__end_systems)  # List of all end systems but the sender
                receivers.remove(sender)

            elif frame_type < per_broadcast + per_single:  # Single frame
                receivers = list(self.__end_systems)  # Select single receiver that is not the sender
                receivers.remove(sender)
                receivers = [choice(receivers)]

            elif frame_type < per_broadcast + per_single + per_multi:  # Multi frame
                receivers = list(self.__end_systems)  # Select a random number of receivers
                receivers.remove(sender)
                shuffle(receivers)
                num_receivers = randint(1, len(receivers))
                receivers = receivers[0:num_receivers]

            else:  # Locally frame
                possible_receivers = list(self.__end_systems)
                possible_receivers.remove(sender)
                distances = [len(self.__paths[sender][receiver]) for receiver in possible_receivers]
                min_distance = min(distance for distance in distances)  # Find the minimum distance
                receivers = []
                for receiver in possible_receivers:  # Copy receivers with min_distance
                    if len(self.__paths[sender][receiver]) == min_distance:
                        receivers.append(receiver)

            self.__frames.append(Frame(sender, receivers))  # Add the frame to the list of frames

    def add_frame_params(self, periods, per_periods, deadlines=None, sizes=None):
        """
        Add the frame parameters to the already created frames
        :param periods: list with all the different periods in microseconds
        :param per_periods: percentage of frames for every period
        :param deadlines: percentage of deadline time into the period 1.0 => deadline = period
        :param sizes: list with sizes of the frames in bytes
        :return: None
        """
        # Normalize percentages
        per_periods = [float(per_period) / sum(per_periods) for per_period in per_periods]

        # For all frames, add the new parameters
        for i in range(len(self.__frames)):
            type_period = random()
            accumulate_period = 0
            # For all possible periods
            for j, per_period in enumerate(per_periods):
                if type_period < per_period + accumulate_period:  # Choice one period for the frame
                    self.__frames[i].set_period(periods[j])  # Set a period to the frame

                    if deadlines is not None and deadlines[j] is not None:
                        self.__frames[i].set_deadline(int(deadlines[j]))  # Set the deadline
                    else:
                        self.__frames[i].set_deadline(periods[j])  # If not, deadline = period

                    if sizes is not None and sizes[j] is not None:  # If there are sizes, set it
                        self.__frames[i].set_size(sizes[j])

                    break  # Once selected, go out
                else:
                    accumulate_period += per_period  # If not, advance in the list

    def __add_dependencies(self, number_dep, min_successor, max_successor, actual_depth, min_depth, max_depth,
                           min_time_waiting, max_time_waiting, min_time_deadline, max_time_deadline, per_waiting,
                           per_deadline, per_both, predecessor_frame_index, predecessor_link):
        """
        Fills the dependency tree from its root with a max depth and successors with a recursive function
        :param number_dep: number of desired dependencies
        :param min_successor: min successor of dependencies at the tree
        :param max_successor: max successor of dependencies at the tree
        :param actual_depth: depth of the dependency tree in this recursive call
        :param min_depth: min depth of dependencies at the tree
        :param max_depth: max depth of dependencies at the tree
        :param min_time_waiting: min time offset desired for waiting dependencies
        :param min_time_waiting: max time offset desired for waiting dependencies
        :param min_time_deadline: min time offset desired for deadline dependencies
        :param max_time_deadline: max time offset desired for deadline dependencies
        :param per_waiting: percentage of waiting dependencies
        :param per_deadline: percentage of deadline dependencies
        :param per_both: percentage of both dependencies
        :param predecessor_frame_index: index of the predecessor frame of the dependency
        :param predecessor_link: index of the predecessor link of the dependency
        :return:
        """
        # For all the successors of the predecessor frame, we find a successor frame and link it with a new dependency
        for i in range(max_successor):
            if len(self.__dependencies) == number_dep:  # If we generated enough dependencies, end
                break
            if len(self.__aux_frames) == 0:  # If we cannot generate more dependencies, end
                break
            # If lord random wants a successor or we do not have more than the min successors, continue creating
            if (i < min_successor) or (random() < ((max_successor - i) / max_successor)):

                # Select the successor of the dependency with the SAME PERIOD and SAME DEADLINE
                aux_aux_frames = copy.copy(self.__aux_frames)  # Copy the remaining frames, to easily select
                successor_frame = choice(aux_aux_frames)  # Select a random frame
                # While the randomly selected frame has not the same period, continue selecting a new one
                while successor_frame.get_period() != self.__frames[predecessor_frame_index].get_period() and \
                        len(aux_aux_frames) != 0 and successor_frame.get_deadline() != \
                        self.__frames[predecessor_frame_index].get_deadline():
                    aux_aux_frames.remove(successor_frame)
                    # We try to select a new one if we fail to find the requirements, if we are out of index, no more
                    # frames available and we end
                    try:
                        successor_frame = choice(aux_aux_frames)
                    except IndexError:
                        break

                # If there is no more frames to search for a successor frame, we end
                if len(aux_aux_frames) == 0:
                    break

                successor_frame_index = self.__frames.index(successor_frame)
                self.__aux_frames.remove(successor_frame)

                # Get the link of the successor
                successor_sender = successor_frame.get_sender()
                successor_receiver = choice(successor_frame.get_receivers())
                successor_link = self.__paths[successor_sender][successor_receiver][-1]

                # Get the waiting and/or deadline times
                random_value = random()
                if random_value < per_waiting:
                    wait_time = randint(min_time_waiting, max_time_waiting)
                    dead_time = 0
                elif random_value < per_waiting + per_deadline:
                    wait_time = 0
                    dead_time = randint(min_time_deadline, max_time_deadline)
                else:
                    wait_time = randint(min_time_waiting, max_time_waiting)
                    dead_time = randint(min_time_deadline, max_time_deadline)

                # Add the dependency
                self.__dependencies.append(Dependency(predecessor_frame_index, predecessor_link, successor_frame_index,
                                                      successor_link, wait_time, dead_time))

                # If lord random wants more depth or the actual depth is smaller than the minimum depth
                if (actual_depth < min_depth) or (random() < ((max_depth - actual_depth) / max_depth)):
                    self.__add_dependencies(number_dep, min_successor, max_successor, actual_depth + 1, min_depth,
                                            max_depth, min_time_waiting, max_time_waiting, min_time_deadline,
                                            max_time_deadline, per_waiting, per_deadline, per_both,
                                            successor_frame_index, successor_link)
            else:
                break

    def generate_dependencies(self, number_dep, min_successor, max_successor, min_depth, max_depth, min_time_waiting,
                              max_time_waiting, min_time_deadline, max_time_deadline, per_waiting, per_deadline,
                              per_both):
        """
        Generate the dependencies for a given array of frames. It generates roots of dependency trees and call a
        recursive function to start building the tree.
        It builds trees until the desired number of dependencies is accomplished or until no more dependencies can be
        created.
        It creates two different dependencies with different predefined ranges.
        Per waiting/deadline/both should be equal to 1.0, but we normalize just in case
        :param number_dep: number of desired dependencies
        :param min_successor: min successor of dependencies at the tree
        :param max_successor: max successor of dependencies at the tree
        :param min_depth: min depth of dependencies at the tree
        :param max_depth: max depth of dependencies at the tree
        :param min_time_waiting: min time offset desired for waiting dependencies
        :param max_time_waiting: max time offset desired for waiting dependencies
        :param min_time_deadline: min time offset desired for deadline dependencies
        :param max_time_deadline: max time offset desired for deadline dependencies
        :param per_waiting: percentage of waiting dependencies
        :param per_deadline: percentage of deadline dependencies
        :param per_both: percentage of both dependencies
        :return:
        """
        # If there is no dependencies, just go out
        if number_dep == 0:
            return

        # Normalize the percentage so the sum is always 1.0
        sum_per = float(per_waiting + per_deadline + per_both)
        per_waiting /= sum_per
        per_deadline /= sum_per
        per_both /= sum_per

        # Copy all frames to the auxiliary list, so it is easier to find frames without dependencies
        self.__aux_frames = copy.copy(self.__frames)

        # While there are dependencies to make, or it is not possible to do more
        while (len(self.__dependencies) < number_dep) and (len(self.__aux_frames) > 0):
            # Choose predecessor frame and remove it from the frames list
            predecessor_frame = choice(self.__aux_frames)
            predecessor_frame_index = self.__frames.index(predecessor_frame)
            self.__aux_frames.remove(predecessor_frame)

            # Get sender and receivers to take the last link of its path
            predecessor_sender = predecessor_frame.get_sender()
            predecessor_receiver = choice(predecessor_frame.get_receivers())
            predecessor_link = self.__paths[predecessor_sender][predecessor_receiver][-1]

            # Call the recursive function to start building the tree from that root dependency
            self.__add_dependencies(number_dep, min_successor, max_successor, 0, min_depth, max_depth, min_time_waiting,
                                    max_time_waiting, min_time_deadline, max_time_deadline, per_waiting, per_deadline,
                                    per_both, predecessor_frame_index, predecessor_link)
            self.__num_dependencies = len(self.__dependencies)

    @staticmethod
    def calculate_hyper_period(periods):
        """
        Calculates the hyper_period of the network
        :param periods: list of periods to calculate the hyper_period
        :return: the hyper_period
        """
        return lcm_multiple(*periods)

    def calculate_utilization(self, hyper_period, replicas, sensing_period, sensing_time):
        """
        Calculates the utilization on all its links, and then return the total utilization of the network
        :param hyper_period: Hyper_period of the network
        :param replicas: list of number of replicas per collision domain
        :param sensing_period: sensing and control period
        :param sensing_time: sensing and control time
        :return: utilization of the network and True if all links have less than 1 utilization
        """
        # Init the list where the utilization will be saved for every link
        link_utilization = []
        for _ in self.__links:
            link_utilization.append(0)

        # For all frames in the network
        for frame in self.__frames:
            # Get all the unique links in the paths of the frame
            unique_links = []
            for receiver in frame.get_receivers():
                # For all links in the path
                for link in self.__paths[frame.get_sender()][receiver]:
                    if link not in unique_links:        # If is unique, add it
                        unique_links.append(link)

            # Once we have all the links in the path, calculate the ns to transmit for all links
            for link in unique_links:
                # First calculate the time occupied by normal transmissions and its period instances
                link_utilization[link] += int(((frame.get_size() * 1000) /
                                               self.__links_object_container[link].get_speed()) *
                                              (hyper_period / frame.get_period()))

                # Then, add the retransmissions if the link has any
                if self.__links_object_container[link].get_type() == LinkType.wireless:
                    for index, collision_domain in enumerate(self.__collision_domains):
                        if link in collision_domain:
                            link_utilization[link] += int((((frame.get_size() * 1000) /
                                                            self.__links_object_container[link].get_speed()) *
                                                           (hyper_period / frame.get_period())) * replicas[index])

        # Last, add the time occupied by sensing and control
        if sensing_period is not None:
            for index, link in enumerate(self.__links_object_container):
                if link.get_type() == LinkType.wireless:
                    link_utilization[index] += int((hyper_period / sensing_period) * sensing_time)

        # Now calculate the utilization in float for every link and calculate the total utilization of the network
        utilization = 0.0
        possible = True
        for index, link in enumerate(link_utilization):
            link_utilization[index] /= hyper_period
            if link_utilization[index] > 1.0:       # Check if is possible to schedule all of its links
                possible = False
            utilization += link_utilization[index]
        return utilization / len(link_utilization), possible

    # Input and Output function definitions #

    # Input function definitions #

    @staticmethod
    def get_network_topology_from_xml(name, index_network):
        """
        Returns the network description (including the link description if exist) from the xml file
        :param name: name of the xml file
        :param index_network: position of the network in the xml to read
        :return: array with network description, the preprocessed collision domain array and array with link 
        description (formatted to work in the network function)
        """
        # Open the file if exists
        try:
            tree = Xml.parse(name)
        except:
            raise Exception("Could not read the xml file")
        root = tree.getroot()

        # Position the branch to the network that is going to be read
        network_description_xml = root.findall('NetworkGenerator/Topology')[index_network]  # Select the network

        # Read Initialize the number of collision domains from the topology information
        topology_information_xml = network_description_xml.find('TopologyInformation')
        num_collision_domains = int(topology_information_xml.find('NumberCollisionDomains').text)

        collision_domains_preprocessed = []
        for _ in range(num_collision_domains):  # For all the collision domains, add an empty list to the matrix
            collision_domains_preprocessed.append([])

        # Initialize strings to be returned with the description
        network_description_line = ''
        link_info_line = ''
        links_found = False

        # For all bifurcations in the topology, read the links information
        network_description_xml = network_description_xml.find('Description')
        link = 0
        for bifurcation in network_description_xml.findall('Bifurcation'):

            # Find the number of links in the bifurcation
            network_description_line += bifurcation.find('NumberLinks').text + ';'
            number_links = int(bifurcation.find('NumberLinks').text)
            links_xml = bifurcation.find('Link')
            links_counter = 0
            links_found = False

            # See if there is also links description
            if links_xml is not None:
                links_found = True
                for link_xml in bifurcation.findall('Link'):  # For all links information
                    links_counter += 1

                    # Save the type information and check if is correct
                    if link_xml.attrib['category'] == 'wired':
                        link_info_line += 'w'
                    elif link_xml.attrib['category'] == 'wireless':
                        link_info_line += 'x'
                    else:
                        raise TypeError('The type of the link is not wired neither wireless')
                    link += 1

                    # Save the speed of the link and convert it to MB/s (standard used in the Network Class)
                    speed_xml = link_xml.find('Speed')
                    speed = speed_xml.text
                    if speed_xml.attrib['unit'] == 'KB/s':  # Convert the speed if is in KB/s
                        speed /= 1000
                    if speed_xml.attrib['unit'] == 'GB/s':  # Convert the speed if is in GB/s
                        speed *= 1000
                    link_info_line += str(speed) + ';'

                    # Save the collision domain if there exist
                    if link_xml.find('CollisionDomain') is not None:
                        collision_domain_string = link_xml.find('CollisionDomain').text
                        collision_domains = collision_domain_string.split(';')
                        for collision_domain in collision_domains:  # For every collision domain in the link, save it
                            collision_domains_preprocessed[int(collision_domain) - 1].append(link)

            # Check if the number of links said by the bifurcation and the encounter links match
            if abs(number_links) != links_counter:
                logging.debug(number_links)
                logging.debug(links_counter)
                raise ValueError('The number of links is incorrect, they should be the same as the bifurcations')

        # Return the description string, and the link description string if exists
        if not links_found:
            return network_description_line[0:-1], collision_domains_preprocessed, None
        else:
            return network_description_line[0:-1], collision_domains_preprocessed, link_info_line[0:-1]

    @staticmethod
    def get_number_replicas_from_xml(name, index_network, index_replica):
        """
        Get the number or replicas of every collision domain in the network
        :param name: name of the configuration file
        :param index_network: index of the network
        :param index_replica: index of the replica
        :return: list with the number of retransmissions
        """
        # Open the file if exists
        try:
            tree = Xml.parse(name)
        except:
            raise Exception("Could not read the xml file")
        root = tree.getroot()

        # Position the branch to the network that is going to be read
        network_description_xml = root.findall('NetworkGenerator/Topology')[index_network]  # Select the network

        # Read the replicas and convert it to a list
        topology_information_xml = network_description_xml.find('TopologyInformation')
        num_replica_xml = topology_information_xml.findall('NumberReplicas')[index_replica]
        # For all replicas in the list, we separate them by ";" and then add them to the list converting them to int
        num_replicas = num_replica_xml.text.split(';')
        list_replicas = []
        for replica in num_replicas:
            list_replicas.append(int(replica))

        return list_replicas

    @staticmethod
    def get_replica_policy_from_xml(name, index_network, index_policy):
        """
        Get the replica policy from the configuration file for the given network
        :param name: configuration file name
        :param index_network: network index
        :param index_policy: policy index
        :return: the policy in string format
        """
        # Open the file if exists
        try:
            tree = Xml.parse(name)
        except:
            raise Exception("Could not read the xml file")
        root = tree.getroot()

        # Position the branch to the network that is going to be read
        network_description_xml = root.findall('NetworkGenerator/Topology')[index_network]  # Select the network

        # Read the policy and return it
        topology_information_xml = network_description_xml.find('TopologyInformation')
        policy_xml = topology_information_xml.findall('ReplicaPolicy')[index_policy]

        return policy_xml.text

    @staticmethod
    def get_replica_interval_from_xml(name, index_network, index_interval):
        """
        Get the interval arrival time of the replica from the configuration file for the given network
        :param name: configuration file name
        :param index_network: network index
        :param index_interval: interval index
        :return: the interval arrival time
        """
        # Open the file if exists
        try:
            tree = Xml.parse(name)
        except:
            raise Exception("Could not read the xml file")
        root = tree.getroot()

        # Position the branch to the network that is going to be read
        network_description_xml = root.findall('NetworkGenerator/Topology')[index_network]  # Select the network

        # Read the policy and return it
        topology_information_xml = network_description_xml.find('TopologyInformation')
        interval_xml = topology_information_xml.findall('ReplicaInterArrivalTime')[index_interval]
        interval = int(interval_xml.text)
        # Check the unit and change to fit us
        if interval_xml.attrib['unit'] == 'ms':
            interval *= 1000000
        elif interval_xml.attrib['unit'] == 'ns':
            interval = interval
        elif interval_xml.attrib['unit'] == 's':
            interval *= 1000000000
        elif interval_xml.attrib['unit'] == 'us':
            interval *= 1000
        else:
            raise TypeError('I do not know this unit for the interval arrival time between replicas => '
                            + interval_xml.attrib['unit'])
        interval = (int(interval))

        return interval

    @staticmethod
    def get_minimum_time_switch_from_xml(name, index_network, index_minimum_switch):
        """
        Get the minimum time of a frame to stay in the switch from the configuration file for the given network
        :param name: configuration file name
        :param index_network: network index
        :param index_minimum_switch: minimum time in switch index
        :return: the interval arrival time
        """
        # Open the file if exists
        try:
            tree = Xml.parse(name)
        except:
            raise Exception("Could not read the xml file")
        root = tree.getroot()

        # Position the branch to the network that is going to be read
        network_description_xml = root.findall('NetworkGenerator/Topology')[index_network]  # Select the network

        # Read the policy and return it
        topology_information_xml = network_description_xml.find('TopologyInformation')
        minimum_switch_xml = topology_information_xml.findall('MinTimeSwitch')[index_minimum_switch]
        minimum_switch = int(minimum_switch_xml.text)
        # Check the unit and change to fit us
        if minimum_switch_xml.attrib['unit'] == 'ms':
            minimum_switch *= 1000000
        elif minimum_switch_xml.attrib['unit'] == 'ns':
            minimum_switch = minimum_switch
        elif minimum_switch_xml.attrib['unit'] == 's':
            minimum_switch *= 1000000000
        elif minimum_switch_xml.attrib['unit'] == 'us':
            minimum_switch *= 1000
        else:
            raise TypeError('I do not know this unit for the minimum time for a frame in a switch => '
                            + minimum_switch_xml.attrib['unit'])
        minimum_switch = (int(minimum_switch))

        return minimum_switch

    @staticmethod
    def get_maximum_time_switch_from_xml(name, index_network, index_maximum_switch):
        """
        Get the maximum time of a frame to stay in the switch from the configuration file for the given network
        :param name: configuration file name
        :param index_network: network index
        :param index_maximum_switch: maximum time in switch index
        :return: the interval arrival time
        """
        # Open the file if exists
        try:
            tree = Xml.parse(name)
        except:
            raise Exception("Could not read the xml file")
        root = tree.getroot()

        # Position the branch to the network that is going to be read
        network_description_xml = root.findall('NetworkGenerator/Topology')[index_network]  # Select the network

        # Read the policy and return it
        topology_information_xml = network_description_xml.find('TopologyInformation')
        maximum_switch_xml = topology_information_xml.findall('MaxTimeSwitch')[index_maximum_switch]
        maximum_switch = int(maximum_switch_xml.text)
        # Check the unit and change to fit us
        if maximum_switch_xml.attrib['unit'] == 'ms':
            maximum_switch *= 1000000
        elif maximum_switch_xml.attrib['unit'] == 'ns':
            maximum_switch = maximum_switch
        elif maximum_switch_xml.attrib['unit'] == 's':
            maximum_switch *= 1000000000
        elif maximum_switch_xml.attrib['unit'] == 'us':
            maximum_switch *= 1000
        else:
            raise TypeError('I do not know this unit for the maximum time for a frame in a switch => '
                            + maximum_switch_xml.attrib['unit'])
        maximum_switch = (int(maximum_switch))

        return maximum_switch

    @staticmethod
    def get_sensing_control_period_from_xml(name, index_network, index_sensing_control_period):

        """
        Get the sensing and control period from the configuration file for the given network
        :param name: configuration file name
        :param index_network: network index
        :param index_sensing_control_period: sensing and control period index
        :return: the interval arrival time
        """
        # Open the file if exists
        try:
            tree = Xml.parse(name)
        except:
            raise Exception("Could not read the xml file")
        root = tree.getroot()

        # Position the branch to the network that is going to be read
        network_description_xml = root.findall('NetworkGenerator/Topology')[index_network]  # Select the network

        # Read the policy and return it
        topology_information_xml = network_description_xml.find('TopologyInformation')
        sensing_control_period_xml = \
            topology_information_xml.findall('SensingControlPeriod')[index_sensing_control_period]
        sensing_control_period = int(sensing_control_period_xml.text)
        # Check the unit and change to fit us
        if sensing_control_period_xml.attrib['unit'] == 'ms':
            sensing_control_period *= 1000000
        elif sensing_control_period_xml.attrib['unit'] == 'ns':
            sensing_control_period = sensing_control_period
        elif sensing_control_period_xml.attrib['unit'] == 's':
            sensing_control_period *= 1000000000
        elif sensing_control_period_xml.attrib['unit'] == 'us':
            sensing_control_period *= 1000
        else:
            raise TypeError('I do not know this unit for the sensing and control period => '
                            + sensing_control_period_xml.attrib['unit'])
        sensing_control_period = (int(sensing_control_period))

        return sensing_control_period

    @staticmethod
    def get_sensing_control_time_from_xml(name, index_network, index_sensing_control_time):
        """
        Get the sensing and control time from the configuration file for the given network
        :param name: configuration file name
        :param index_network: network index
        :param index_sensing_control_time: sensing and control time index
        :return: the interval arrival time
        """
        # Open the file if exists
        try:
            tree = Xml.parse(name)
        except:
            raise Exception("Could not read the xml file")
        root = tree.getroot()

        # Position the branch to the network that is going to be read
        network_description_xml = root.findall('NetworkGenerator/Topology')[index_network]  # Select the network

        # Read the policy and return it
        topology_information_xml = network_description_xml.find('TopologyInformation')
        sensing_control_time_xml = \
            topology_information_xml.findall('SensingControlTime')[index_sensing_control_time]
        sensing_control_time = int(sensing_control_time_xml.text)
        # Check the unit and change to fit us
        if sensing_control_time_xml.attrib['unit'] == 'ms':
            sensing_control_time *= 1000000
        elif sensing_control_time_xml.attrib['unit'] == 'ns':
            sensing_control_time = sensing_control_time
        elif sensing_control_time_xml.attrib['unit'] == 's':
            sensing_control_time *= 1000000000
        elif sensing_control_time_xml.attrib['unit'] == 'us':
            sensing_control_time *= 1000
        else:
            raise TypeError('I do not know this unit for the sensing and control time => '
                            + sensing_control_time_xml.attrib['unit'])
        sensing_control_time = (int(sensing_control_time))

        return sensing_control_time

    @staticmethod
    def get_traffic_information_from_xml(name, index_traffic):
        """
        Get the traffic information from the configuration file
        :param name: name of the configuration file
        :param index_traffic: number of the traffic information
        :return: the number of frames, percentage of single, local, multiple and broadcast, in this order
        """
        # Open the file if exists
        try:
            tree = Xml.parse(name)
        except:
            raise Exception("Could not read the xml file")
        root = tree.getroot()

        # Position the branch to the traffic that is going to be read
        traffic_information_xml = root.findall('NetworkGenerator/Traffic/TrafficInformation')[index_traffic]

        # Read the information and save it in local variables to return later
        num_frames = int(traffic_information_xml.find('NumberFrames').text)
        single = float(traffic_information_xml.find('Single').text)
        local = float(traffic_information_xml.find('Local').text)
        multiple = float(traffic_information_xml.find('Multiple').text)
        broadcast = float(traffic_information_xml.find('Broadcast').text)

        # Return everything
        return num_frames, single, local, multiple, broadcast

    @staticmethod
    def get_frames_description_from_xml(name, index_frames_description):
        """
        Get the frames description from the configuration file
        :param name: name of the configuration file
        :param index_frames_description: number of the frame description
        :return: list with all periods, percentages, deadlines and sizes in this order
        """
        # Open the file if exists
        try:
            tree = Xml.parse(name)
        except:
            raise Exception("Could not read the xml file")
        root = tree.getroot()

        # Position the branch to the traffic that is going to be read
        frames_description_xml = root.findall('NetworkGenerator/Traffic/FrameDescription')[index_frames_description]

        # Init lists of variables to return
        periods = []
        per_periods = []
        deadlines = []
        sizes = []

        # For all frame types, add the period, percentage, deadlines and sizes to the list of variables
        frame_types_xml = frames_description_xml.findall('FrameType')
        for frame_type_xml in frame_types_xml:
            per_periods.append(float(frame_type_xml.find('Percentage').text))

            period_xml = frame_type_xml.find('Period')
            period = int(period_xml.text)
            # Check the unit and change the period to fit us
            if period_xml.attrib['unit'] == 'ms':
                period *= 1000000
            elif period_xml.attrib['unit'] == 'ns':
                period = period
            elif period_xml.attrib['unit'] == 's':
                period *= 1000000000
            elif period_xml.attrib['unit'] == 'us':
                period *= 1000
            else:
                raise TypeError('I do not know this unit for the period => ' + period_xml.attrib['unit'])
            periods.append(int(period))

            if frame_type_xml.find('Deadline') is None:  # If there is no deadline, add None
                deadlines.append(None)
            else:
                # Check the unit and change the period to fit us
                deadline_xml = frame_type_xml.find('Deadline')
                deadline = int(deadline_xml.text)
                # Check the unit and change the period to fit us
                if deadline_xml.attrib['unit'] == 'ms':
                    deadline *= 1000000
                elif deadline_xml.attrib['unit'] == 'ns':
                    deadline = deadline
                elif deadline_xml.attrib['unit'] == 's':
                    deadline *= 1000000000
                elif deadline_xml.attrib['unit'] == 'us':
                    deadline *= 1000
                else:
                    raise TypeError('I do not know this unit for the deadline => ' + deadline_xml.attrib['unit'])
                deadlines.append(int(deadline))

            if frame_type_xml.find('Size') is None:  # If there is no size, add None
                sizes.append(None)
            else:
                sizes.append(int(frame_type_xml.find('Size').text))

        # Check if all values on deadline or sizes are None, to just return a None instead of a list of Nones
        if all(deadline is None for deadline in deadlines):
            deadlines = None
        if all(size is None for size in sizes):
            sizes = None

        return periods, per_periods, deadlines, sizes

    @staticmethod
    def get_dependencies_from_xml(name, index_dependencies):
        """
        Get the dependencies parameters from the configuration file
        :param name: name of the configuration file
        :param index_dependencies: index of the dependency parameters to read
        :return: the number of dependencies, the minimum depth, the maximum depth, the minimum children, the maximum
        children, the minimum time waiting, the maximum time waiting, the minimum time deadline, the maximum time
        deadline, the waiting percentage, the deadline percentage and the waiting/deadline together percentage, in 
        order
        """
        # Open the file if exists
        try:
            tree = Xml.parse(name)
        except:
            raise Exception("Could not read the xml file")
        root = tree.getroot()

        # Position the branch to the dependency parameters that is going to be read
        dependencies_parameter_xml = root.findall('NetworkGenerator/Traffic/Dependencies')[index_dependencies]

        # Read all the variables and save them in local variables to be returned
        num_dependencies = int(dependencies_parameter_xml.find('NumberDependencies').text)
        min_depth = int(dependencies_parameter_xml.find('MinDepth').text)
        max_depth = int(dependencies_parameter_xml.find('MaxDepth').text)
        min_children = int(dependencies_parameter_xml.find('MinChildren').text)
        max_children = int(dependencies_parameter_xml.find('MaxChildren').text)

        min_time_waiting_xml = dependencies_parameter_xml.find('MinTimeWaiting')
        min_time_waiting = int(min_time_waiting_xml.text)
        # Check the unit and change to fit us
        if min_time_waiting_xml.attrib['unit'] == 'ms':
            min_time_waiting *= 1000000
        elif min_time_waiting_xml.attrib['unit'] == 'ns':
            min_time_waiting = min_time_waiting
        elif min_time_waiting_xml.attrib['unit'] == 's':
            min_time_waiting *= 1000000000
        elif min_time_waiting_xml.attrib['unit'] == 'us':
            min_time_waiting *= 1000
        else:
            raise TypeError('I do not know this unit for the minimum time waiting => '
                            + min_time_waiting_xml.attrib['unit'])
        min_time_waiting = (int(min_time_waiting))

        max_time_waiting_xml = dependencies_parameter_xml.find('MaxTimeWaiting')
        max_time_waiting = int(max_time_waiting_xml.text)
        # Check the unit and change to fit us
        if max_time_waiting_xml.attrib['unit'] == 'ms':
            max_time_waiting *= 1000000
        elif max_time_waiting_xml.attrib['unit'] == 'ns':
            max_time_waiting = max_time_waiting
        elif max_time_waiting_xml.attrib['unit'] == 's':
            max_time_waiting *= 1000000000
        elif max_time_waiting_xml.attrib['unit'] == 'us':
            max_time_waiting *= 1000
        else:
            raise TypeError('I do not know this unit for the maximum time waiting => '
                            + max_time_waiting_xml.attrib['unit'])
        max_time_waiting = (int(max_time_waiting))

        min_time_deadline_xml = dependencies_parameter_xml.find('MinTimeDeadline')
        min_time_deadline = int(min_time_deadline_xml.text)
        # Check the unit and change to fit us
        if min_time_deadline_xml.attrib['unit'] == 'ms':
            min_time_deadline *= 1000000
        elif min_time_deadline_xml.attrib['unit'] == 'ns':
            min_time_deadline = min_time_deadline
        elif min_time_deadline_xml.attrib['unit'] == 's':
            min_time_deadline *= 1000000000
        elif min_time_deadline_xml.attrib['unit'] == 'us':
            min_time_deadline *= 1000
        else:
            raise TypeError('I do not know this unit for the minimum time deadline => '
                            + min_time_deadline_xml.attrib['unit'])
        min_time_deadline = (int(min_time_deadline))

        max_time_deadline_xml = dependencies_parameter_xml.find('MaxTimeDeadline')
        max_time_deadline = int(max_time_deadline_xml.text)
        # Check the unit and change to fit us
        if max_time_deadline_xml.attrib['unit'] == 'ms':
            max_time_deadline *= 1000000
        elif max_time_deadline_xml.attrib['unit'] == 'ns':
            max_time_deadline = max_time_deadline
        elif max_time_deadline_xml.attrib['unit'] == 's':
            max_time_deadline *= 1000000000
        elif max_time_deadline_xml.attrib['unit'] == 'us':
            max_time_deadline *= 1000
        else:
            raise TypeError('I do not know this unit for the maximum time deadline => '
                            + max_time_deadline_xml.attrib['unit'])
        max_time_deadline = (int(max_time_deadline))

        waiting = float(dependencies_parameter_xml.find('Waiting').text)
        deadline = float(dependencies_parameter_xml.find('Deadline').text)
        waiting_deadline = float(dependencies_parameter_xml.find('WaitingDeadline').text)

        # Return everything
        return num_dependencies, min_depth, max_depth, min_children, max_children, min_time_waiting, \
            max_time_waiting, min_time_deadline, max_time_deadline, waiting, deadline, waiting_deadline

    # Output function definitions #

    def __generate_network_description_xml(self, top):
        """
        Generates the network description, including the nodes, links and collision domains information
        :param top: top of the xml tree where to add the network description
        :return: 
        """
        # Create the node to attach all the network description
        network_description_xml = Xml.SubElement(top, 'NetworkDescription')

        # For all nodes, attach its information
        nodes_xml = Xml.SubElement(network_description_xml, 'Nodes')
        for index, node in self.__graph.nodes_iter(data=True):
            node_type = ''
            if node['type'].get_type() == NodeType.end_system:     # Check the type of the node (End system or Switch)
                node_type = 'End System'
            elif node['type'].get_type() == NodeType.switch:
                node_type = 'Switch'
            node_xml = Xml.SubElement(nodes_xml, 'Node')
            node_xml.set('category', node_type)         # Set the category to either End System or Wireless

            # Add the information of the node
            Xml.SubElement(node_xml, 'ID').text = str(index)

            # Add the links connected to that node
            connections_xml = Xml.SubElement(node_xml, 'Connections')
            for link in self.__links:
                if link[0] == index or link[1] == index:    # If the link is connected to the node, add its ID
                    Xml.SubElement(connections_xml, 'Link').text = str(self.__links.index(link))

        # For all links, attach its information
        links_xml = Xml.SubElement(network_description_xml, 'Links')
        for index, link in enumerate(self.__links_object_container):
            link_type = ''
            if link.get_type() == LinkType.wireless:        # Check if the link type is wired or wireless
                link_type = 'Wireless'
            elif link.get_type() == LinkType.wired:
                link_type = 'Wired'
            link_xml = Xml.SubElement(links_xml, 'Link')
            link_xml.set('category', link_type)
            Xml.SubElement(link_xml, 'ID').text = str(index)
            Xml.SubElement(link_xml, 'Speed').text = str(link.get_speed())
            Xml.SubElement(link_xml, 'Source').text = str(self.__links[index][0])
            Xml.SubElement(link_xml, 'Destination').text = str(self.__links[index][1])

        # For all the collision domains, attach its information
        collision_domains_xml = Xml.SubElement(network_description_xml, 'CollisionDomains')
        for collision_domain in self.__collision_domains:
            collision_domain_xml = Xml.SubElement(collision_domains_xml, 'CollisionDomain')
            for link in collision_domain:                   # For all links in the collision domain, add it
                Xml.SubElement(collision_domain_xml, 'Link').text = str(link)

    def __generate_frames_xml(self, top):
        """
        Generate the output XML for the frames
        :param top: top element where to add the frames
        :return: 
        """
        # For all frames, attach the frame information
        frames_xml = Xml.SubElement(top, 'Frames')
        for index, frame in enumerate(self.__frames):
            frame_xml = Xml.SubElement(frames_xml, 'Frame')
            Xml.SubElement(frame_xml, 'ID').text = str(index)
            Xml.SubElement(frame_xml, 'Period').text = str(frame.get_period())
            Xml.SubElement(frame_xml, 'Deadline').text = str(frame.get_deadline())
            Xml.SubElement(frame_xml, 'Size').text = str(frame.get_size())

            # Write all paths
            paths_xml = Xml.SubElement(frame_xml, 'Paths')
            paths = []                  # List to save the paths, necessary to calculate the splits
            for receiver in frame.get_receivers():      # Every path is from the sender to one of the frame receivers
                path_str = ''
                paths.append([])        # Init the current path
                for link in self.__paths[frame.get_sender()][receiver]:     # For all links in the path
                    path_str += str(link) + ';'
                    paths[-1].append(link)              # Save the link to calculate the split later on
                Xml.SubElement(paths_xml, 'Path').text = path_str           # Save the path once finished

            # Write all splits
            splits_xml = Xml.SubElement(frame_xml, 'Splits')
            splits = self.__calculate_splits(paths)     # Calculate the paths for the given splits
            if len(splits) > 0:                         # If there are any splits
                for split in splits:                    # For all splits
                    split_str = ''
                    for link in split:                  # For all links in the split, do the same that in paths
                        split_str += str(link) + ';'
                    Xml.SubElement(splits_xml, 'Split').text = split_str

    def __generate_dependencies_xml(self, top):
        """
        Generate the output XML for the dependencies
        :param top: node where to add the dependencies
        :return: 
        """
        # For all dependencies, add them
        dependencies_xml = Xml.SubElement(top, 'Dependencies')
        for index, dependency in enumerate(self.__dependencies):
            dependency_xml = Xml.SubElement(dependencies_xml, 'Dependency')
            Xml.SubElement(dependency_xml, 'ID').text = str(index)
            Xml.SubElement(dependency_xml, 'PredecessorFrame').text = str(dependency.get_predecessor_frame())
            Xml.SubElement(dependency_xml, 'PredecessorLink').text = str(dependency.get_predecessor_link())
            Xml.SubElement(dependency_xml, 'SuccessorFrame').text = str(dependency.get_successor_frame())
            Xml.SubElement(dependency_xml, 'SuccessorLink').text = str(dependency.get_successor_link())
            Xml.SubElement(dependency_xml, 'WaitingTime').text = str(dependency.get_waiting_time())
            Xml.SubElement(dependency_xml, 'DeadlineTime').text = str(dependency.get_deadline_time())

    def __generate_xml_output(self, name, configuration):
        """
        Generates the XML output file with the information of the network to schedule
        :param name: hash name of the network, including the folder relative direction
        :param configuration: configuration parameters needed for the general information
        :return: 
        """
        # Create top of the xml file
        network_input_xml = Xml.Element('Network')

        # Write the General Information of the network
        general_information_xml = Xml.SubElement(network_input_xml, 'GeneralInformation')
        Xml.SubElement(general_information_xml, 'NumberFrames').text = str(len(self.__frames))
        Xml.SubElement(general_information_xml, 'NumberDependencies').text = str(self.__num_dependencies)
        Xml.SubElement(general_information_xml, 'NumberSwitches').text = str(len(self.__switches))
        Xml.SubElement(general_information_xml, 'NumberEndSystems').text = str(len(self.__end_systems))
        Xml.SubElement(general_information_xml, 'NumberLinks').text = str(len(self.__links))
        Xml.SubElement(general_information_xml, 'NumberCollisionDomains').text = str(len(self.__collision_domains))
        Xml.SubElement(general_information_xml, 'SensingControlPeriod').text = str(configuration.sensing_control_period)
        Xml.SubElement(general_information_xml, 'SensingControlTime').text = str(configuration.sensing_control_time)
        Xml.SubElement(general_information_xml, 'ReplicaPolicy').text = configuration.replica_policy
        Xml.SubElement(general_information_xml, 'ReplicaInterval').text = str(configuration.replica_interval)
        Xml.SubElement(general_information_xml, 'HyperPeriod').text = str(configuration.hyper_period)
        Xml.SubElement(general_information_xml, 'Utilization').text = str(configuration.utilization)
        replica_str = ''
        for replica in configuration.replicas:
            replica_str += str(replica) + ';'
        Xml.SubElement(general_information_xml, 'Replicas').text = replica_str

        # Write the Network Description
        self.__generate_network_description_xml(network_input_xml)

        # Write the Traffic Information
        traffic_information_xml = Xml.SubElement(network_input_xml, 'TrafficInformation')
        self.__generate_frames_xml(traffic_information_xml)
        self.__generate_dependencies_xml(traffic_information_xml)

        # Write the final file
        output_xml = minidom.parseString(Xml.tostring(network_input_xml)).toprettyxml(indent="   ")
        with open(name, "w") as f:
            f.write(output_xml)

    def create_networks_from_xml(self, name):
        """
        Create all the networks possible from the configuration xml file. They are nested under a folder "network" and
        for every network, a folder with a hashed name is created, that contains the xml that describes the network and
        all its traffic. The xml network file will have the same hashed name as the folder
        :param name: name of the configuration xml file
        :return: 
        """
        # Open the file if exists
        try:
            tree = Xml.parse(name)
        except:
            raise Exception("Could not read the xml file")
        root = tree.getroot()

        # Create the folder "networks", if already exists, delete it and create it empty again
        try:
            os.makedirs("networks")
        except FileExistsError:
            shutil.rmtree("networks")
            os.makedirs("networks")

        # Variables for statistics of creation of networks
        total_networks = 0          # Count the number of all networks configurations
        schedulable_networks = 0    # Count the number of networks that will be created to schedule

        # Start reading how many different values are in the configuration file to create every possible network
        num_topologies = len(root.findall('NetworkGenerator/Topology'))
        num_traffic_information = len(root.findall('NetworkGenerator/Traffic/TrafficInformation'))
        num_frame_descriptions = len(root.findall('NetworkGenerator/Traffic/FrameDescription'))
        num_dependencies_configurations = len(root.findall('NetworkGenerator/Traffic/Dependencies'))

        # Init variables to enter the for loop if there is 0 configuration of that variable
        dependency_configuration_null = False
        replica_null = False
        policy_null = False
        interval_null = False
        minimum_switch_null = False
        maximum_switch_null = False
        sensing_control_period_null = False
        sensing_control_time_null = False

        conf = NetworkConfiguration()
        list_unique_conf = []           # List of all unique configurations

        # For all topologies found in the configuration file, read the number of different configurations
        for topology_index in range(num_topologies):
            # Get the network description for the topology

            # Get the number of different configurations for that topology
            topology_xml = root.findall('NetworkGenerator/Topology')[topology_index]
            topology_information_xml = topology_xml.find('TopologyInformation')

            num_replicas = len(topology_information_xml.findall('NumberReplicas'))
            num_policies = len(topology_information_xml.findall('ReplicaPolicy'))
            num_intervals = len(topology_information_xml.findall('ReplicaInterArrivalTime'))
            num_minimum_switch = len(topology_information_xml.findall('MinTimeSwitch'))
            num_maximum_switch = len(topology_information_xml.findall('MaxTimeSwitch'))
            num_sensing_control_period = len(topology_information_xml.findall('SensingControlPeriod'))
            num_sensing_control_time = len(topology_information_xml.findall('SensingControlTime'))

            # If there is no configuration, we enter the for, but we do not extract anything from the
            # configuration file (because nothing is there!)
            if num_replicas == 0:
                num_replicas = 1
                replica_null = True
            if num_policies == 0:
                num_policies = 1
                policy_null = True
            if num_intervals == 0:
                num_intervals = 1
                interval_null = True
            if num_minimum_switch == 0:
                num_minimum_switch = 1
                minimum_switch_null = True
            if num_maximum_switch == 0:
                num_maximum_switch = 1
                maximum_switch_null = True
            if num_sensing_control_period == 0:
                num_sensing_control_period = 1
                sensing_control_period_null = True
            if num_sensing_control_time == 0:
                num_sensing_control_time = 1
                sensing_control_time_null = True

            for traffic_information_index in range(num_traffic_information):
                for frame_description_index in range(num_frame_descriptions):
                    # If there is no configuration, we enter the for, but we do not extract anything from the
                    # configuration file (because nothing is there!) This is special case, because is outside the
                    # topology configuration
                    if num_dependencies_configurations == 0:
                        num_dependencies_configurations = 1
                        dependency_configuration_null = True
                    for dependencies_index in range(num_dependencies_configurations):
                        for replica_index in range(num_replicas):
                            for policy_index in range(num_policies):
                                for interval_index in range(num_intervals):
                                    for minimum_switch_index in range(num_minimum_switch):
                                        for maximum_switch_index in range(num_maximum_switch):
                                            for period_index in range(num_sensing_control_period):
                                                for time_index in range(num_sensing_control_time):

                                                    total_networks += 1

                                                    # Create the configuration
                                                    network_description, pre_col_dom, link_description = \
                                                        self.get_network_topology_from_xml(name, topology_index)
                                                    conf.set_topology_parameters(network_description, link_description)

                                                    conf.set_collision_domains_parameter(pre_col_dom)

                                                    num_frames, single, local, multiple, broadcast = \
                                                        self.get_traffic_information_from_xml(name,
                                                                                              traffic_information_index)
                                                    conf.set_traffic_information_parameters(num_frames, single, local,
                                                                                            multiple, broadcast)
                                                    periods, per_periods, deadlines, sizes = \
                                                        self.get_frames_description_from_xml(name,
                                                                                             frame_description_index)
                                                    conf.set_frames_description_parameters(periods, per_periods,
                                                                                           deadlines, sizes)
                                                    if not dependency_configuration_null:
                                                        num_dependencies, min_depth, max_depth, min_children, \
                                                            max_children, min_time_waiting, max_time_waiting, \
                                                            min_time_deadline, max_time_deadline, waiting, deadline, \
                                                            waiting_deadline = \
                                                            self.get_dependencies_from_xml(name, dependencies_index)
                                                        conf.set_dependency_parameters(num_dependencies, min_depth,
                                                                                       max_depth, min_children,
                                                                                       max_children, min_time_waiting,
                                                                                       max_time_waiting,
                                                                                       min_time_deadline,
                                                                                       max_time_deadline, waiting,
                                                                                       deadline, waiting_deadline)
                                                    if not replica_null:
                                                        list_replicas = \
                                                            self.get_number_replicas_from_xml(name, topology_index,
                                                                                              replica_index)
                                                        conf.set_replicas_parameter(list_replicas)
                                                    else:
                                                        conf.set_replicas_parameter(None)

                                                    if not policy_null:
                                                        policy = self.get_replica_policy_from_xml(name, topology_index,
                                                                                                  policy_index)
                                                        conf.set_replica_policy_parameter(policy)
                                                    else:
                                                        conf.set_replica_policy_parameter(None)

                                                    if not interval_null:
                                                        interval = self.get_replica_interval_from_xml(name,
                                                                                                      topology_index,
                                                                                                      interval_index)
                                                        conf.set_replica_interval_parameter(interval)
                                                    else:
                                                        conf.set_replica_interval_parameter(None)

                                                    if not minimum_switch_null:
                                                        minimum_switch = \
                                                            self.get_minimum_time_switch_from_xml(name, topology_index,
                                                                                                  minimum_switch_index)
                                                        conf.set_minimum_switch_parameter(minimum_switch)
                                                    else:
                                                        conf.set_minimum_switch_parameter(None)

                                                    if not maximum_switch_null:
                                                        maximum_switch = \
                                                            self.get_maximum_time_switch_from_xml(name, topology_index,
                                                                                                  maximum_switch_index)
                                                        conf.set_maximum_switch_parameter(maximum_switch)
                                                    else:
                                                        conf.set_maximum_switch_parameter(None)

                                                    if not sensing_control_period_null:
                                                        sensing_control_period = \
                                                            self.get_sensing_control_period_from_xml(name,
                                                                                                     topology_index,
                                                                                                     period_index)
                                                        conf.set_sensing_control_period_parameter(
                                                            sensing_control_period)
                                                    else:
                                                        conf.set_sensing_control_period_parameter(None)

                                                    if not sensing_control_time_null:
                                                        sensing_control_time = \
                                                            self.get_sensing_control_time_from_xml(name, topology_index,
                                                                                                   time_index)
                                                        conf.set_sensing_control_time_parameter(
                                                            sensing_control_time)
                                                    else:
                                                        conf.set_sensing_control_time_parameter(None)

                                                    # Skip the configuration if is not valid
                                                    if conf.is_it_valid():
                                                        # Formalize the configuration to spot identical later on
                                                        conf.formalize_configuration()

                                                        # Add the configuration if there is no same configuration
                                                        if conf not in list_unique_conf:
                                                            list_unique_conf.append(deepcopy(conf))

        logging.debug("Number of total networks => %d", total_networks)
        logging.debug("Number of unique networks = > %d", len(list_unique_conf))

        # For all configurations, create the network and its traffic
        for configuration in list_unique_conf:
            self.create_topology(configuration.network, configuration.preprocessed_collision_domains,
                                 configuration.link)
            self.generate_paths()
            self.generate_frames(configuration.num_frames, configuration.broad, configuration.single,
                                 configuration.local, configuration.multi)
            self.add_frame_params(configuration.periods, configuration.per_periods, configuration.deadlines,
                                  configuration.sizes)
            if configuration.num_dependencies is not None:
                self.generate_dependencies(configuration.num_dependencies, configuration.min_depth,
                                           configuration.max_depth, configuration.min_children,
                                           configuration.max_children, configuration.min_time_waiting,
                                           configuration.max_time_waiting, configuration.min_time_deadline,
                                           configuration.max_time_deadline, configuration.waiting,
                                           configuration.deadline, configuration.waiting_deadline)

            hyper_period = self.calculate_hyper_period(configuration.periods)
            utilization, schedulable = self.calculate_utilization(hyper_period, configuration.replicas,
                                                                  configuration.sensing_control_period,
                                                                  configuration.sensing_control_time)

            configuration.hyper_period = hyper_period
            configuration.utilization = utilization

            # If schedulable then, create the network
            if schedulable:
                schedulable_networks += 1

                # Generate hashing
                hash_string = "net-" + configuration.network + "&col_dom-"
                hash_string += str(configuration.preprocessed_collision_domains) + "&link-" + configuration.link
                hash_string += "&frame-" + str(configuration.num_frames) + "&per-" + str(configuration.broad) + ","
                hash_string += str(configuration.single) + "," + str(configuration.local) + ","
                hash_string += str(configuration.multi) + "&periods-" + str(configuration.periods)
                hash_string += "&per_periods-" + str(configuration.per_periods) + "&deadlines-"
                hash_string += str(configuration.deadlines) + "&sizes-" + str(configuration.sizes) + "&num_dep-"
                hash_string += str(configuration.num_dependencies) + "&min_depth-" + str(configuration.min_depth)
                hash_string += "&max_depth-" + str(configuration.max_depth) + "&min_children-"
                hash_string += str(configuration.min_children) + "&max_children-" + str(configuration.max_children)
                hash_string += "&min_time_waiting-" + str(configuration.min_time_waiting) + "&max_time_waiting-"
                hash_string += str(configuration.max_time_waiting) + "&min_time_deadline-"
                hash_string += str(configuration.min_time_deadline) + "&max_time_deadline-"
                hash_string += str(configuration.max_time_deadline) + "&waiting-" + str(configuration.waiting)
                hash_string += "&deadline-" + str(configuration.deadline) + "&waiting_deadline-"
                hash_string += str(configuration.waiting_deadline) + "&replica_policy-"
                hash_string += str(configuration.replica_policy) + "&replica_interval-"
                hash_string += str(configuration.replica_interval) + "&replicas-" + str(configuration.replicas)
                hash_string += "&sensing_control_period-" + str(configuration.sensing_control_period)
                hash_string += "&sensing_control_time-" + str(configuration.sensing_control_time)
                print(hash_string)
                hash_num = hashlib.md5(hash_string.encode())
                print(hash_num.hexdigest())

                os.makedirs("networks/" + str(hash_num.hexdigest()))
                os.makedirs("networks/" + str(hash_num.hexdigest()) + "/schedules")
                name_network = "networks/" + str(hash_num.hexdigest()) + "/" + str(hash_num.hexdigest())
                self.__generate_xml_output(name_network, configuration)

        logging.debug(logging.debug("Number of schedulable networks = > %d", schedulable_networks))
