"""* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 *                                                                                                                     *
 *  Dependency Class                                                                                                   *
 *  Scheduler                                                                                                          *
 *                                                                                                                     *
 *  Created by Francisco Pozo on 25/04/17.                                                                             *
 *  Copyright © 2017 Francisco Pozo. All rights reserved.                                                              *
 *                                                                                                                     *
 *  Class that contains the information of dependencies in a list of trees                                             *
 *  A node contains information of the frame, link and the deadline and waiting time of its parent node.               *
 *  It also contains an array of children, which means that this node is the parent of all its children                *
 *                                                                                                                     *
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * """


class DependencyNode:

    # Variable definitions #

    __frame_index = None
    __link_index = None
    __waiting = None
    __deadline = None
    __children = []
    __parent = None

    # Standard function definitions #

    def __init__(self, frame_index, link_index, waiting, deadline, parent=None):
        self.__frame_index = frame_index
        self.__link_index = link_index
        self.__waiting = waiting
        self.__deadline = deadline
        self.__children = []
        self.__parent = parent

    def add_new_children(self, frame_index, link_index, waiting, deadline):
        """
        Add a new children to the dependency node
        :param frame_index: frame index
        :param link_index: link index
        :param waiting: waiting time
        :param deadline: deadline time
        :return: 
        """
        self.__children.append(DependencyNode(frame_index, link_index, waiting, deadline, self))

    def search_and_add_dependency(self, predecessor_frame, predecessor_link, successor_frame, successor_link, waiting,
                                  deadline):
        """
        Search recursively if the predecessor frame and index appear in the tree, if yes, add a new children 
        and return 1, else 0
        :param predecessor_frame: predecessor frame index
        :param predecessor_link: predecessor frame link
        :param successor_frame: successor frame index
        :param successor_link: successor frame index
        :param waiting: waiting time
        :param deadline: deadline time
        :return: 1 if found and added, 0 otherwise
        """
        # If the current dependency is the predecessor, add a new children
        if self.__frame_index == predecessor_frame and self.__link_index == predecessor_link:
            self.add_new_children(successor_frame, successor_link, waiting, deadline)
            return 1            # Return that we found it
        else:   # If not, iterate over all the children of the dependency
            for child in self.__children:
                found = child.search_and_add_dependency(predecessor_frame, predecessor_link, successor_frame,
                                                        successor_link, waiting, deadline)
                if found:       # If we found it, return 1 to go back
                    return 1
        return 0


class DependencyTree:

    # Variable definitions #

    __list_trees = []

    # Standard function definitions #

    def __init__(self):
        self.__list_trees = []

    def add_dependency(self, predecessor_frame, predecessor_link, successor_frame, successor_link, waiting, deadline):
        """
        Add a new dependency to the list of dependency trees
        :param predecessor_frame: predecessor frame index
        :param predecessor_link: predecessor link index
        :param successor_frame: successor frame index
        :param successor_link: successor frame index
        :param waiting: waiting time
        :param deadline: deadline time
        :return: 
        """
        if self.__list_trees:                      # If there are already dependencies in the tree
            for tree in self.__list_trees:
                found = tree.search_and_add_dependency(predecessor_frame, predecessor_link, successor_frame,
                                                       successor_link, waiting, deadline)
                if found:                           # if we found it, stop the search
                    return

        # If we did not found anything or the list of trees is empty, add a new tree, and a child to it
        self.__list_trees.append(DependencyNode(predecessor_frame, predecessor_link, 0, 0))
        self.__list_trees[-1].add_new_children(successor_frame, successor_link, waiting, deadline)