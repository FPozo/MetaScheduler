"""* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 *                                                                                                                     *
 *  Z3Synthesizer Class                                                                                                *
 *  Scheduler                                                                                                          *
 *                                                                                                                     *
 *  Created by Francisco Pozo on 26/04/17.                                                                             *
 *  Copyright © 2017 Francisco Pozo. All rights reserved.                                                              *
 *                                                                                                                     *
 *  Class that contains calls of the assertions in the SMT solver Z3 with the Python API to solve the schedule.        *
 *                                                                                                                     *
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * ** * * * * * * * * * * * * * * *"""

from z3 import *
from Scheduler.Network import Network
from math import ceil


class Z3Synthesizer:
    """
    Class that contains the functions to assert constraints to the SMT solver Z3 and its configuration
    """

    # Variable definitions #

    __solver = None
    __model = None

    # Standard function definitions #

    def __init__(self):
        self.__solver = SolverFor('QF_LIA')
        self.__model = None

    def init_z3_variables(self, network, frames, starting_time, ending_time):
        """
        Init the Z3 variables in the frames to be scheduled and constraint them to the starting and ending time
        :param network: network class with all the information
        :param frames: list of frames in a frame queue
        :param starting_time: starting time to init the constraints
        :param ending_time: ending time to init the constraints
        :type network: Network
        :type frames: list of FrameBlock
        :type starting_time: int
        :type ending_time: int
        :return: 
        """
        # For all frames in the list create the z3 variables and assert them with the range
        for frame in frames:
            frame_index = frame.get_frame_index()

            for path in network.get_frame_paths(frame_index):

                # Set the name of the z3 integer variable (or at least what we know now)
                name = 'Offset_' + str(frame_index) + '_' + str(path.get_link_id())
                path.init_z3_offset(name)

                # Remove the time for the retransmissions from the deadline so they can accomplish it
                deadline = network.get_frame_deadline(frame_index)
                replica_interval = 0
                if path.get_num_replicas() > 1:         # If there are retransmissions
                    if network.get_replica_policy() == 'Spread':    # If consecutive, - num_replica * interval
                        replica_interval = network.get_replica_interval()
                        deadline -= (path.get_num_replicas() - 1) * replica_interval
                    else:                                               # If spread, the interval is the time of frame
                        replica_interval = path.get_transmission_time()
                        deadline -= (path.get_num_replicas() - 1) * replica_interval

                # If the deadline is larger than the given ending time, limit the frame to the ending time
                if deadline > ending_time:
                    end_time = ending_time
                else:
                    end_time = deadline

                # Set the first instance and first replica larger than starting_time (others do not need as they relate
                # with the [0][0] z3 integer variable)
                offset = path.get_z3_offset(0, 0)
                self.__solver.add(offset >= starting_time, offset < end_time)

                # Set the offsets for the rest of the offset matrix
                for instance in range(path.get_num_instances()):
                    for replica in range(path.get_num_replicas()):
                        if instance != 0 or replica != 0:
                            # Calculate the value between the offset [0][0] and the current one
                            value = (instance * network.get_frame_period(frame_index)) + (replica * replica_interval)
                            offset2 = path.get_z3_offset(instance, replica)
                            self.__solver.add(offset2 == offset + value)

        # Init the sensing and control also if is the first call of this function
        if starting_time == 0 and network.get_sensing_control_period():
            for path in network.get_sensing_control_path():

                # Set the name of the z3 integer variable
                name = 'Sensing_Control_' + str(path.get_link_id())
                path.init_z3_offset(name)

                # Set the offsets for the z3 variables and also save the value in the integer offsets (for forever)
                for instance in range(path.get_num_instances()):
                    value = instance * network.get_sensing_control_period()
                    offset = path.get_z3_offset(instance, 0)
                    self.__solver.add(offset == value)
                    path.set_offset(instance, 0, value)

    def contention_free(self, network, frames, previous_frames, starting_time, ending_time):
        """
        Assures that all the new frames introduced do not collide with others
        :param network: :param network: given network
        :param frames: list of frames to create the z3 constraints
        :param previous_frames: list of previous frames to avoid collision
        :param starting_time: starting time to init the constraints
        :param ending_time: ending time to init the constraints
        :type network: Network
        :type frames: list of FrameBlock
        :type previous_frames: list of FrameBlock, None
        :type starting_time: int
        :type ending_time: int
        :return: 
        """
        # For all given frames, go through all paths
        for index, frame in enumerate(frames):
            frame_index = frame.get_frame_index()
            for path in network.get_frame_paths(frame_index):

                # For all previous frames, go through all paths also
                for previous_index in range(0, index):
                    previous_frame_index = frames[previous_index].get_frame_index()
                    for previous_path in network.get_frame_paths(previous_frame_index):

                        # Check if they share the same link or collision domain
                        link = path.get_link_id()
                        previous_link = previous_path.get_link_id()
                        collision_domain = network.link_in_collision_domain(link)
                        previous_collision_domain = network.link_in_collision_domain(previous_link)
                        if link == previous_link or \
                                (collision_domain >= 0 and collision_domain == previous_collision_domain):

                            # Assert the constraint for all possible instances in the given range
                            min_instances = starting_time // network.get_frame_period(frame_index)
                            max_instances = int(ceil(ending_time / network.get_frame_period(frame_index)))
                            for instance in range(min_instances, max_instances):
                                for replica in range(path.get_num_replicas()):
                                    offset = path.get_z3_offset(instance, replica)

                                    # Assert with all possible instances of the previous frames
                                    prev_min_instances = starting_time // network.get_frame_period(previous_frame_index)
                                    prev_max_instances = int(ceil(ending_time /
                                                                  network.get_frame_period(previous_frame_index)))
                                    for previous_instance in range(prev_min_instances, prev_max_instances):
                                        for prev_replica in range(previous_path.get_num_replicas()):
                                            prev_offset = previous_path.get_z3_offset(previous_instance, prev_replica)

                                            self.__solver.add(Or(offset + path.get_transmission_time() < prev_offset,
                                                                 offset >=
                                                                 prev_offset + previous_path.get_transmission_time()))

                # For the sensing and control, also avoid transmission in its blocks
                for sensing_path in network.get_sensing_control_path():

                    # Check if there are links that are wireless and needed to avoid sensing and control blocks
                    link = path.get_link_id()
                    sensing_control_link = sensing_path.get_link_id()
                    if link == sensing_control_link:

                        # Assert the constraint for all possible instances in the given range
                        min_instances = starting_time // network.get_frame_period(frame_index)
                        max_instances = int(ceil(ending_time / network.get_frame_period(frame_index)))
                        for instance in range(min_instances, max_instances):
                            for replica in range(path.get_num_replicas()):
                                offset = path.get_z3_offset(instance, replica)

                                # Assert with all possible instances of the sensing and control
                                sensing_min_instances = starting_time // network.get_sensing_control_period()
                                sensing_max_instances = int(ceil(ending_time) / network.get_sensing_control_period())
                                for sensing_instance in range(sensing_min_instances, sensing_max_instances):
                                    sensing_offset = sensing_path.get_z3_offset(sensing_instance, 0)

                                    self.__solver.add(Or(offset + path.get_transmission_time() < sensing_offset,
                                                         offset >=
                                                         sensing_offset + sensing_path.get_transmission_time()))

    def path_dependent(self, network, frames):
        """
        Assure that all the given frames follow their path correctly
        :param network: given network
        :param frames: list of frames to create the z3 constraints
        :type network: Network
        :type frames: list of FrameBlock
        :return: 
        """
        for frame in frames:                                        # For all given frames
            frame_index = frame.get_frame_index()
            for path in network.get_frame_paths(frame_index):       # For all paths in the frame

                # For all children of the path, create the path dependent constraint
                offset_parent = path.get_z3_offset(0, 0)
                for child_path in path.get_children():
                    offset_child = child_path.get_z3_offset(0, 0)
                    # Offset_child_path > Offset_parent_path + minimum_time_switch
                    self.__solver.add(offset_child >= offset_parent + (network.get_minimum_time_switch()))

    def switch_memory(self, network, frames):
        """
        Assure that all the given frames do not surpass the time in the switch
        :param network: given network
        :param frames: list of frames to create the z3 constraints
        :type network: Network
        :type frames: list of FrameBlock
        :return: 
        """
        for frame in frames:                                        # For all given frames
            frame_index = frame.get_frame_index()
            for path in network.get_frame_paths(frame_index):       # For all paths in the frame

                # For all children of the path, create the path dependent constraint
                offset_parent = path.get_z3_offset(0, 0)
                for child_path in path.get_children():
                    offset_child = child_path.get_z3_offset(0, 0)
                    # Offset_child_path > Offset_parent_path + minimum_time_switch
                    self.__solver.add(offset_child < offset_parent + (network.get_maximum_time_switch()))

    def simultaneous_dispatch(self, network, frames):
        """
        Assure that all the given frames are transmitted at the same time in their splits
        :param network: given network
        :param frames: list of frames to create the z3 constraints
        :type network: Network
        :type frames: list of FrameBlock
        :return: 
        """
        for frame in frames:                                        # For all given frames
            frame_index = frame.get_frame_index()

            # For every split, get all the paths in it and assert all its transmissions as equal
            for split in network.get_frame_splits(frame_index):

                # Before anything, we check if any split has a link in the collision domain, as they do cannot follow
                # simultaneous dispatch constraints
                collision_domains = network.get_collision_domains()
                impossible = [1 for collision_domain in collision_domains for link in split if link in collision_domain]

                if not impossible:          # If any link in the split is in a collision domain, skip this iteration
                    list_paths = network.get_frame_paths_in_split(frame_index, split)
                    for index_path, path in enumerate(list_paths[:-1]):         # For all paths but the last one
                        offset1 = list_paths[index_path].get_z3_offset(0, 0)
                        offset2 = list_paths[index_path + 1].get_z3_offset(0, 0)
                        # actual path = next_path (both in split) => all offsets in paths in split are the same
                        self.__solver.add(offset1 == offset2)

    def dependencies_constraints(self, network, frames):
        """
        Assures that all the given frames satisfy the dependencies constraints
        :param network: given network
        :param frames: list of frames to create the z3 constraints
        :type network: Network
        :type frames: list of FrameBlock
        :return: 
        """
        for frame in frames:            # For all frames
            dependency = frame.get_dependency_linker()
            if dependency:              # If the frame has a dependency add it

                # Get the z3 variables from the predecessor and the successor dependency
                predecessor_dependency = dependency.get_parent()
                if predecessor_dependency:  # If the dependency has a parent (if not is the top and nothing to do)
                    predecessor_path = network.get_frame_path_from_link(predecessor_dependency.get_frame_index(),
                                                                        predecessor_dependency.get_link_index())
                    predecessor_offset = predecessor_path.get_z3_offset(0, 0)

                    successor_path = network.get_frame_path_from_link(dependency.get_frame_index(),
                                                                      dependency.get_link_index())
                    successor_offset = successor_path.get_z3_offset(0, 0)

                    if dependency.get_deadline() > 0:       # If there are deadline dependency
                        self.__solver.add(successor_offset < (predecessor_offset + dependency.get_deadline()))
                    if dependency.get_waiting() > 0:        # If there are waiting dependency
                        self.__solver.add(successor_offset > (predecessor_offset + dependency.get_waiting()))

    def check_satisfiability(self):
        """
        Check if the current context is satisfiable or not
        :return: 1 if satisfiable, 0 is not
        :rtype: int
        """
        return self.__solver.check() == sat

    def create_model(self):
        """
        Create the model of the current context and save it in the object
        :return: 
        """
        self.__model = self.__solver.model()

    def fix_offsets(self, network, frames):
        """
        Fix the offsets from the given frames in the smt solver and also saves them as integers in the matrix offset
        :param network: network object
        :param frames: list of frames to fix
        :type network: Network
        :type frames: list of FrameBlock
        :return: 
        """
        # For all frames in the list, get through all its paths and fix the offsets
        for frame in frames:
            frame_index = frame.get_frame_index()

            # For all paths, go through every offset in the offset matrix
            for path in network.get_frame_paths(frame_index):
                for instance in range(path.get_num_instances()):
                    for replica in range(path.get_num_replicas()):
                        # Get the value from the model, and then save it in the integer offset matrix
                        offset = path.get_z3_offset(instance, replica)
                        path.set_offset(instance, replica, self.__model[offset])
