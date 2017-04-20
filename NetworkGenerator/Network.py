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
import xml.etree.ElementTree as Xml
import networkx as nx
import logging
import copy


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
    __collision_domains_preprocessed = []  # Matrix with list of links of that are in the collision domain before
    # creating the network and knowing the REAL link placement for the link
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
        self.__graph = None
        self.__switches = []
        self.__end_systems = []
        self.__links = []
        self.__collision_domains = []
        self.__collision_domains_preprocessed = []
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

    def __add_link_information(self, links, num_links, branch, parent_node):
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
        for index_col, collision_domain in enumerate(self.__collision_domains):
            for index_link, link in enumerate(collision_domain):
                # If the link is included in the collision domain preprocessed array, save it now with the
                # correct link value now that we know it (both directions)
                if self.__collision_domains_preprocessed[index_col][index_link] == (
                            num_links + branch) + 1:
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

    def __init_collision_domain(self, number_collision_domains):
        """
        Initialize the matrix with the number of collision domains
        :param number_collision_domains: number of collision domains
        :return: 
        """
        for _ in range(number_collision_domains):
            self.__collision_domains.append([])

    def __recursive_create_network(self, description, links, parent_node, num_calls, num_links):
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
                    self.__add_link_information(links, num_links, leaf, parent_node)
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
                    self.__add_link_information(links, num_links, branch, parent_node)

                    # Check which link is calling, if last call is bigger, set it to last call
                    if last_call_link > it_links + (int(description[num_calls]) - branch):
                        links_to_call = last_call_link
                    else:
                        links_to_call = it_links + (int(description[num_calls] - branch))
                    # Call the recursive for the new branch, we save the last call link to recover it when we return
                    # after the branch created by this recursive call is finished
                    last_call_link, num_calls = self.__recursive_create_network(description, links, new_parent,
                                                                                num_calls + 1, links_to_call)

                return last_call_link, num_calls  # Return when all branches have been created and closed

        except IndexError:
            raise ValueError("The network description is wrongly formulated, there are open branches")

    # Public function definitions #

    def create_network(self, network_description, link_description=None):
        """
        Creates a network with the description received
        :param network_description: string with the data of the network, it follows an special description
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
        logging.debug(network_description)
        self.__init__()
        description_array = network_description.split(';')  # Separate the description string in an array
        description = [int(numeric_string) for numeric_string in description_array]  # Parse the string into int
        if link_description is not None:  # Separate also the link description if exist
            links = link_description.split(';')
        else:
            links = None

        # Start the recursive call with parent switch 0
        self.__add_switch()
        # Num links and num calls are auxiliary variables to map the order in which the links are created and to check
        # if the creation of the network was successful
        num_links, num_calls = self.__recursive_create_network(description, links, 0, 0, 0)

        # Check if there are additional elements that should not be in the network
        if num_calls != len(description) - 1:
            raise ValueError("The network description is wrongly formulated, there are extra elements")
        logging.debug("End Systems => " + str(len(self.__end_systems)))
        logging.debug("Switches => " + str(len(self.__switches)))
        logging.debug("Links => " + str(len(self.__links)))
        logging.debug(self.__collision_domains)

    def define_collision_domains(self, collision_domains):
        """
        Defines the wireless links that share the same frequency
        :param collision_domains: matrix, every x is a list of links that are in the same collision domain
        :return:
        """
        self.__collision_domains = map(list, collision_domains)  # Copy the matrix to the local object

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
            if frame % 1000 == 0:
                logging.debug("Frame => " + str(frame))
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

                    if deadlines is not None or deadlines[j] is not None:
                        self.__frames[i].set_deadline(int(deadlines[j]))  # Set the deadline
                    else:
                        self.__frames[i].set_deadline(periods[j])  # If not, deadline = period

                    if sizes is not None or sizes[j] is not None:  # If there are sizes, set it
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

    # Input and Output function definitions #

    def get_network_topology_from_xml(self, name, index_network):
        """
        Returns the network description (including the link description if exist) from the xml file
        :param name: name of the xml file
        :param index_network: position of the network in the xml to read
        :return: array with network description and array with link description (formatted to work in the network
        function)
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
        for _ in range(num_collision_domains):  # For all the collision domains, add an empty list to the matrix
            self.__collision_domains_preprocessed.append([])

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
                            self.__collision_domains_preprocessed[int(collision_domain) - 1].append(link)

            # Check if the number of links said by the bifurcation and the encounter links match
            if abs(number_links) != links_counter:
                logging.debug(number_links)
                logging.debug(links_counter)
                raise ValueError('The number of links is incorrect, they should be the same as the bifurcations')

        # Return the description string, and the link description string if exists
        if not links_found:
            return network_description_line[0:-1], None
        else:
            return network_description_line[0:-1], link_info_line[0:-1]

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
        return num_dependencies, min_depth, max_depth, min_children, max_children, min_time_waiting, max_time_waiting, \
            min_time_deadline, max_time_deadline, waiting, deadline, waiting_deadline
