"""* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 *                                                                                                                     *
 *  Frame Class                                                                                                        *
 *  Scheduler                                                                                                          *
 *                                                                                                                     *
 *  Created by Francisco Pozo on 25/04/17.                                                                             *
 *  Copyright © 2017 Francisco Pozo. All rights reserved.                                                              *
 *                                                                                                                     *
 *  Class that contains the information of a single frame in the network.                                              *
 *  A frame should contain the information of period, deadline, size, and the tree path it is following, including in  *
 *  which switches it is splinting to multiple links.                                                                  *
 *  It also contains the offset matrix (instance/replica) for every link.                                              *
 *                                                                                                                     *
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * """

from itertools import chain
from z3 import *


class TreePath:
    """
    Class with the tree path of a frame that contains the information over all links with the transmission time
    """

    # Variable definitions #

    __link_id = None
    __transmission_time = None
    __offset = []
    __name_offset = []
    __parent = None
    __children = []

    # Standard function definitions #

    def __init__(self):
        self.__link_id = None
        self.__transmission_time = None
        self.__offset = []
        self.__name_offset = []
        self.__parent = None
        self.__children = []

    def __iter__(self):
        """
        Modified iterator that does a pre-traversal of the tree path
        :return: current path
        """
        yield self
        for v in chain(*map(iter, self.__children)):
            yield v

    def get_link_id(self):
        """
        Get the link id
        :return: link id
        """
        return self.__link_id

    def set_link_id(self, link_id):
        """
        Set the link id
        :param link_id: link id
        :return: 
        """
        self.__link_id = link_id

    def get_transmission_time(self):
        """
        Get the transmission time of the frame through this link
        :return: the transmission time
        """
        return self.__transmission_time

    def set_transmission_time(self, transmission_time):
        """
        Set the transmission time of the frame through the link
        :param transmission_time: transmission time of the frame through the link
        :return: 
        """
        self.__transmission_time = int(transmission_time)

    def get_parent(self):
        """
        Get the parent path of the current path
        :return: parent path
        :rtype: TreePath
        """
        return self.__parent

    def set_parent(self, parent):
        """
        Set a link to the parent path object
        :param parent: parent path object
        :return: 
        """
        self.__parent = parent

    def init_offset(self, num_instances, num_replicas):
        """
        Init the offset matrix for the number of instances and replicas in that link
        :param num_instances: number of instances (depends of the period and hyper_period)
        :param num_replicas: number of replicas (depends of the replicas of the collision domain)
        :return: 
        """
        for _ in range(num_instances):
            self.__offset.append([])
            self.__name_offset.append([])
            for __ in range(num_replicas):
                self.__offset[-1].append(None)
                self.__name_offset[-1].append(None)

    def get_children(self):
        """
        Get the list of path children
        :return: list of path children
        """
        return self.__children

    def set_children(self, list_paths):
        """
        Set the list of path object children
        :param list_paths: list of children path object
        :return: 
        """
        self.__children = list_paths

    def get_child(self, index_child):
        """
        Get a child path object
        :param index_child: index to the path
        :return: the indicated child path
        """
        return self.__children[index_child]

    def set_child(self, index_child, child_path):
        """
        Set the path child for the given index
        :param index_child: index of the path
        :param child_path: children path
        :return: 
        """
        self.__children[index_child] = child_path

    def set_offset(self, index_instance, index_replica, time):
        """
        Set the offset transmission time
        :param index_instance: instance index
        :param index_replica: replica index
        :param time: transmission time
        :type time: int, IntNumRef
        :return: 
        """
        # If the time is a IntNumRef, convert it to normal time
        if isinstance(time, IntNumRef):
            self.__offset[index_instance][index_replica] = time.as_long()
        else:
            self.__offset[index_instance][index_replica] = time

    def get_name_offset(self, index_instance, index_replica):
        """
        Get the name variable
        :param index_instance: instance index 
        :param index_replica: replica index
        :return: the name variable
        :rtype: str
        """
        return self.__name_offset[index_instance][index_replica]

    def get_offset(self, index_instance, index_replica):
        """
        Get the offset for the instance and replica given
        :param index_instance: index of the instance
        :param index_replica: index of the replica
        :type index_replica: int
        :type index_instance: int
        :return: offset
        :rtype: int
        """
        return self.__offset[index_instance][index_replica]

    def init_name_offset(self, file, name):
        """
        Set all the name offsets in the matrix
        :param name: the start of the name o_frame_link, it needs _instance_replica
        :param file: file where to write the declaration of names
        :type name: str
        :return: 
        :rtype: 
        """
        # For all values in the matrix, complete the final name
        for row_index, row in enumerate(self.__name_offset):
            for column_index, _ in enumerate(row):
                final_name = name + '_' + str(row_index) + '_' + str(column_index)
                self.__name_offset[row_index][column_index] = final_name
                file.write("(declare-fun " + final_name + " () Int)\n")

    def add_new_path(self, path):
        """
        If the link in the path is on children, continue recursion, if not, create new children and continue until the
        path is empty
        :param path: list of index links in the path
        :return: 
        """
        if self.__link_id is None:  # If the link id is None, this link has not appear
            self.__link_id = path[0]  # We create it adding the link id
            path = path[1:]  # Advance the path
            if path:  # If there are more links in the path
                self.__children.append(TreePath())  # Add it as new children
                self.__children[-1].set_parent(self)  # Set the actual path as parent of the child
                self.__children[-1].add_new_path(path)  # Continue the recursion
        elif len(path) > 1:  # If the path is larger than 1 (if 1, we finished!)
            child_found = False
            for child in self.__children:  # Search if any children has the next link in the path
                if child.get_link_id() == path[1]:  # If it has, continue the recursion with the child path
                    child.add_new_path(path[1:])
                    child_found = True
                    break
            if not child_found:  # If the link is not in a child create it
                self.__children.append(TreePath())
                self.__children[-1].add_new_path(path[1:])  # Call recursion, it will create add the information

    def get_num_replicas(self):
        """
        Get the number of replicas of the path
        :return: number of replicas
        _:rtype: int
        """
        return len(self.__name_offset[0])

    def get_num_instances(self):
        """
        Get the number of instances of the z3 offset matrix
        :return: number of instances
        _rtype: int
        """
        return len(self.__name_offset)

    def get_path_by_link(self, index_link):
        """
        Get the path that has the same index link
        :param index_link: index of the link
        :type index_link: int
        :return: path
        :rtype: TreePath
        """
        if self.__link_id == index_link:        # If we found it, return it
            return self
        else:
            for children in self.__children:    # For all children of the path, call it recursively, if found return
                found = children.get_path_by_link(index_link)
                if found:
                    return found
        return None                             # The link is not in this path


class Frame:
    """
    Class with information about the a frame, including the tree path with the transmission links over all its links
    """

    # Variable definitions #

    __period = None
    __deadline = None
    __size = None
    __tree_path = None
    __splits = []

    # Standard function definitions #

    def __init__(self):
        self.__period = None
        self.__deadline = None
        self.__size = None
        self.__tree_path = None
        self.__splits = []

    def get_period(self):
        """
        Get the period
        :return: period
        """
        return self.__period

    def set_period(self, period):
        """
        Set the period of the frame
        :param period: period
        :return: 
        """
        self.__period = period

    def get_deadline(self):
        """
        Get the deadline of the frame
        :return: deadline
        """
        return self.__deadline

    def set_deadline(self, deadline):
        """
        Set the deadline of the frame
        :param deadline: deadline
        :return: 
        """
        self.__deadline = deadline

    def get_size(self):
        """
        Get the size of the frame
        :return: size in bytes
        """
        return self.__size

    def set_size(self, size):
        """
        Set the size of the frame
        :param size: size in bytes
        :return: 
        """
        self.__size = size

    def get_path(self):
        """
        Get the path root of the frame
        :return: path root of the path tree
        :rtype: TreePath
        """
        return self.__tree_path

    def add_path(self, path):
        """
        Add path to the Tree Path
        :param path: list of links in the path
        :return: 
        """
        if self.__tree_path is None:  # If is the first path, initialize the root of the tree path
            self.__tree_path = TreePath()
        self.__tree_path.add_new_path(path)

    def get_splits(self):
        """
        Get the matrix of splits
        :return: matrix of splits
        :rtype: list of list of int
        """
        return self.__splits

    def add_split(self, split):
        """
        Add a split to the matrix of splits
        :param split: list of links in the split
        :return: 
        """
        self.__splits.append(split)

    def update_frame(self, links, hyper_period, list_replicas, collision_domains):
        """
        Init the frame to be prepared to allocate all instances and replicas of frames (init offsets and time)
        :param links: list of links objects of the network that contains information of the speed
        :param hyper_period: hyper period of the network
        :param list_replicas: list of replicas for every collision domain
        :param collision_domains: matrix with the links in every collision domain
        :return: 
        """
        for path in self.__tree_path:  # For every path in the tree path, update the time and the offsets
            path.set_transmission_time((self.__size * 1000) / links[path.get_link_id()].get_speed())
            num_instances = int(hyper_period / self.__period)  # Get the number of instances

            # Get the list of replicas if the link is in a collision domain + 1, 1 if not
            collision_domain = [index for index, row in enumerate(collision_domains) if path.get_link_id() in row]
            num_replicas = 1 if not collision_domain else list_replicas[collision_domain[0]] + 1

            path.init_offset(num_instances, num_replicas)
