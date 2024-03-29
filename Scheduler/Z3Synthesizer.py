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

from Scheduler.Network import Network
from math import ceil
import subprocess


class Z3Synthesizer:
    """
    Class that contains the functions to assert constraints to the SMT solver Z3 and its configuration
    """

    # Variable definitions #

    __smt_lib_file = None
    __solution_file = None

    # Standard function definitions #

    def __init__(self):
        self.__smt_lib_file = open("Constraints.smt", "w")
        self.__smt_lib_file.write("(set-logic QF_LIA)\n")
        self.__time_checking = 0

    def init_variables(self, network, frames, starting_time, ending_time):
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
                path.init_name_offset(self.__smt_lib_file, name)

                # Remove the time for the retransmissions from the deadline so they can accomplish it
                deadline = network.get_frame_deadline(frame_index)

                # If the deadline is larger than the given ending time, limit the frame to the ending time
                if deadline > ending_time:
                    end_time = ending_time
                else:
                    end_time = deadline

                # Remove the time for replicas and transmission time to be sure it does not go outside
                end_time -= path.get_transmission_time()

                replica_interval = 0
                if path.get_num_replicas() > 1:  # If there are retransmissions
                    if network.get_replica_policy() == 'Spread':  # If consecutive, - num_replica * interval
                        replica_interval = network.get_replica_interval()
                        end_time -= (path.get_num_replicas() - 1) * replica_interval
                    else:  # If spread, the interval is the time of frame
                        replica_interval = path.get_transmission_time()
                        end_time -= (path.get_num_replicas() - 1) * replica_interval

                # Set the first instance and first replica larger than starting_time (others do not need as they relate
                # with the [0][0] z3 integer variable)
                offset = path.get_name_offset(0, 0)
                # self.__smt_lib_file.write("(assert (>= " + offset + " " + str(starting_time) + "))\n")
                # self.__smt_lib_file.write("(assert (< " + offset + " " + str(end_time) + "))\n")
                self.__smt_lib_file.write("(assert (<= " + offset + " (- " + str(starting_time) + ")))\n")
                self.__smt_lib_file.write("(assert (> " + offset + " (- " + str(end_time) + ")))\n")

                # Set the offsets for the rest of the offset matrix
                for instance in range(path.get_num_instances()):
                    for replica in range(path.get_num_replicas()):
                        if instance != 0 or replica != 0:
                            # Calculate the value between the offset [0][0] and the current one
                            value = (instance * network.get_frame_period(frame_index)) + (replica * replica_interval)
                            offset2 = path.get_name_offset(instance, replica)
                            # self.__smt_lib_file.write("(assert (= " + offset2 + " (+ " + offset + " " +
                            #                          str(value) + ")))\n")
                            self.__smt_lib_file.write("(assert (= " + offset2 + " (- " + offset + " " +
                                                      str(value) + ")))\n")

        # Init the sensing and control also if is the first call of this function
        if starting_time == 0 and network.get_sensing_control_period():
            for path in network.get_sensing_control_path():

                # Set the name of the z3 integer variable
                name = 'Sensing_Control_' + str(path.get_link_id())
                path.init_name_offset(self.__smt_lib_file, name)

                # Set the offsets for the z3 variables and also save the value in the integer offsets (for forever)
                for instance in range(path.get_num_instances()):
                    value = instance * network.get_sensing_control_period()
                    offset = path.get_name_offset(instance, 0)
                    # self.__smt_lib_file.write("(assert (= " + offset + " " + str(value) + "))\n")
                    self.__smt_lib_file.write("(assert (= " + offset + " (- " + str(value) + ")))\n")
                    path.set_offset(instance, 0, value)

    def re_init_variables(self, network, frames, starting_time, ending_time):
        """
        For the given frames in the network, re-init them into the smt-lib file. This is done searching for all frames
        which one have any instance or replica appearing in the given time interval, and adding them to the file
        with the fixed value. At the end, returns a list with all frames which constraints where added
        :param network: network class with all the information
        :param frames: list of frames in a frame queue
        :param starting_time: starting time to init the constraints
        :param ending_time: ending time to init the constraints
        :type network: Network
        :type frames: list of FrameBlock
        :type starting_time: int
        :type ending_time: int
        :return: list of frames that where added
        :rtype: list of FrameBlock
        """
        # Open a new file and load the fixed values
        self.__smt_lib_file = open('Constraints.smt', 'w')
        self.__smt_lib_file.write("(set-logic QF_LIA)\n")

        init_frames = []        # List of frames that are added again
        # For all given frames, see if any value is in the given range
        for frame in frames:
            frame_index = frame.get_frame_index()
            for path in network.get_frame_paths(frame_index):
                for instance in range(path.get_num_instances()):
                    for replica in range(path.get_num_replicas()):

                        # If the frame is between the given range, init and add it
                        value = path.get_offset(instance, replica)
                        if starting_time <= value < ending_time:
                            if frame not in init_frames:
                                init_frames.append(frame)
                            name = 'Offset_' + str(frame_index) + '_' + str(path.get_link_id()) + '_' + \
                                   str(instance) + '_' + str(replica)
                            self.__smt_lib_file.write("(declare-fun " + name + " () Int)\n")
                            self.__smt_lib_file.write("(assert (= " + name + ' (- ' + str(value) + ')))\n')

        # Do the same for the sensing and control blocks that appear in the interval
        if network.get_sensing_control_period():
            for path in network.get_sensing_control_path():
                for instance in range(path.get_num_instances()):

                    # If the sensing and control block is in the given range, init and add it
                    value = path.get_offset(instance, 0)
                    if starting_time <= value < ending_time:
                        name = 'Sensing_Control_' + str(path.get_link_id()) + '_' + str(instance)
                        self.__smt_lib_file.write("(declare-fun " + name + " () Int)\n")
                        self.__smt_lib_file.write("(assert (= " + name + ' (- ' + str(value) + ')))\n')
        return init_frames

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

                # For all previous frames in the frames list, go through all paths also
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
                                    offset = path.get_name_offset(instance, replica)

                                    # Assert with all possible instances of the previous frames
                                    prev_min_instances = starting_time // network.get_frame_period(previous_frame_index)
                                    prev_max_instances = int(ceil(ending_time /
                                                                  network.get_frame_period(previous_frame_index)))
                                    for previous_instance in range(prev_min_instances, prev_max_instances):
                                        for prev_replica in range(previous_path.get_num_replicas()):
                                            prev_offset = previous_path.get_name_offset(previous_instance, prev_replica)

                                            # self.__smt_lib_file.write("(assert (or (< (+ " + offset + " " +
                                            #                          str(path.get_transmission_time()) + ") " +
                                            #                          prev_offset + ") (>= " + offset + " (+ " +
                                            #                          prev_offset + " " +
                                            #                          str(previous_path.get_transmission_time()) +
                                            #                          "))))\n")
                                            self.__smt_lib_file.write("(assert (or (> (- " + offset + " " +
                                                                      str(path.get_transmission_time()) + ") " +
                                                                      prev_offset + ") (<= " + offset + " (- " +
                                                                      prev_offset + " " +
                                                                      str(previous_path.get_transmission_time()) +
                                                                      "))))\n")

                # For all previous frames list, go through all paths also
                for previous_index, previous_frame in enumerate(previous_frames):
                    previous_frame_index = previous_frame.get_frame_index()
                    for previous_path in network.get_frame_paths(previous_frame_index):

                        # Check if they share the same link or collision domain
                        link = path.get_link_id()
                        previous_link = previous_path.get_link_id()
                        collision_domain = network.link_in_collision_domain(link)
                        previous_collision_domain = network.link_in_collision_domain(
                            previous_link)
                        if link == previous_link or \
                                (collision_domain >= 0 and collision_domain == previous_collision_domain):

                            # Assert the constraint for all possible instances in the given range
                            min_instances = starting_time // network.get_frame_period(frame_index)
                            max_instances = int(ceil(ending_time / network.get_frame_period(frame_index)))
                            for instance in range(min_instances, max_instances):
                                for replica in range(path.get_num_replicas()):
                                    offset = path.get_name_offset(instance, replica)

                                    # Assert with all possible instances of the previous frames
                                    prev_min_instances = starting_time // network.get_frame_period(previous_frame_index)
                                    prev_max_instances = int(ceil(
                                        ending_time / network.get_frame_period(previous_frame_index)))
                                    for previous_instance in range(prev_min_instances, prev_max_instances):
                                        for prev_replica in range(previous_path.get_num_replicas()):
                                            prev_offset = previous_path.get_name_offset(previous_instance, prev_replica)

                                            # self.__smt_lib_file.write("(assert (or (< (+ " + offset + " " +
                                            #                          str(path.get_transmission_time()) + ") " +
                                            #                          prev_offset + ") (>= " + offset + " (+ " +
                                            #                          prev_offset + " " +
                                            #                          str(previous_path.get_transmission_time()) +
                                            #                          "))))\n")
                                            self.__smt_lib_file.write("(assert (or (> (- " + offset + " " +
                                                                      str(path.get_transmission_time()) + ") " +
                                                                      prev_offset + ") (<= " + offset + " (- " +
                                                                      prev_offset + " " +
                                                                      str(previous_path.get_transmission_time()) +
                                                                      "))))\n")

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
                                offset = path.get_name_offset(instance, replica)

                                # Assert with all possible instances of the sensing and control
                                for sensing_instance in range(sensing_path.get_num_instances()):
                                    if starting_time <= sensing_path.get_offset(sensing_instance, 0) < ending_time:
                                        sensing_offset = sensing_path.get_name_offset(sensing_instance, 0)

                                        # self.__smt_lib_file.write("(assert (or (< (+ " + offset + " " +
                                        #                          str(path.get_transmission_time()) + ") " +
                                        #                          sensing_offset + ") (>= " + offset + " (+ " +
                                        #                          sensing_offset + " " +
                                        #                          str(sensing_path.get_transmission_time()) + "))))\n")
                                        self.__smt_lib_file.write("(assert (or (> (- " + offset + " " +
                                                                  str(path.get_transmission_time()) + ") " +
                                                                  sensing_offset + ") (<= " + offset + " (- " +
                                                                  sensing_offset + " " +
                                                                  str(sensing_path.get_transmission_time()) + "))))\n")

    def path_dependent(self, network, frames):
        """
        Assure that all the given frames follow their path correctly
        :param network: given network
        :param frames: list of frames to create the z3 constraints
        :type network: Network
        :type frames: list of FrameBlock
        :return: 
        """
        for frame in frames:  # For all given frames
            frame_index = frame.get_frame_index()
            for path in network.get_frame_paths(frame_index):  # For all paths in the frame

                # For all children of the path, create the path dependent constraint
                offset_parent = path.get_name_offset(0, 0)
                for child_path in path.get_children():
                    offset_child = child_path.get_name_offset(0, 0)
                    # Offset_child_path > Offset_parent_path + minimum_time_switch
                    # self.__smt_lib_file.write("(assert (>= " + offset_child + " (+ " + offset_parent + " " +
                    #                          str(network.get_minimum_time_switch()) + ")))\n")
                    self.__smt_lib_file.write("(assert (<= " + offset_child + " (- " + offset_parent + " " +
                                              str(network.get_minimum_time_switch()) + ")))\n")

    def switch_memory(self, network, frames):
        """
        Assure that all the given frames do not surpass the time in the switch
        :param network: given network
        :param frames: list of frames to create the z3 constraints
        :type network: Network
        :type frames: list of FrameBlock
        :return: 
        """
        for frame in frames:  # For all given frames
            frame_index = frame.get_frame_index()
            for path in network.get_frame_paths(frame_index):  # For all paths in the frame

                # For all children of the path, create the path dependent constraint
                offset_parent = path.get_name_offset(0, 0)
                for child_path in path.get_children():
                    offset_child = child_path.get_name_offset(0, 0)
                    # Offset_child_path > Offset_parent_path + minimum_time_switch
                    self.__smt_lib_file.write("(assert (> " + offset_child + " (- " + offset_parent + " " +
                                              str(network.get_maximum_time_switch()) + ")))\n")

    def simultaneous_dispatch(self, network, frames):
        """
        Assure that all the given frames are transmitted at the same time in their splits
        :param network: given network
        :param frames: list of frames to create the z3 constraints
        :type network: Network
        :type frames: list of FrameBlock
        :return: 
        """
        for frame in frames:  # For all given frames
            frame_index = frame.get_frame_index()

            # For every split, get all the paths in it and assert all its transmissions as equal
            for split in network.get_frame_splits(frame_index):

                # Before anything, we check if any split has a link in the collision domain, as they do cannot follow
                # simultaneous dispatch constraints
                collision_domains = network.get_collision_domains()
                impossible = [1 for collision_domain in collision_domains for link in split if link in collision_domain]

                if not impossible:  # If any link in the split is in a collision domain, skip this iteration
                    list_paths = network.get_frame_paths_in_split(frame_index, split)
                    for index_path, path in enumerate(list_paths[:-1]):  # For all paths but the last one
                        offset1 = list_paths[index_path].get_name_offset(0, 0)
                        offset2 = list_paths[index_path + 1].get_name_offset(0, 0)
                        # actual path = next_path (both in split) => all offsets in paths in split are the same
                        self.__smt_lib_file.write("(assert (= " + offset1 + " " + offset2 + "))\n")

    def dependencies_constraints(self, network, frames, starting_time):
        """
        Assures that all the given frames satisfy the dependencies constraints
        :param network: given network
        :param frames: list of frames to create the z3 constraints
        :param starting_time: starting time of the dependencies constraint, needed to avoid multiple initializations
        :type network: Network
        :type frames: list of FrameBlock
        :type starting_time: int
        :return: 
        """
        already_init_predecessor = []   # List of predecessor offsets that have been init already

        for frame in frames:  # For all frames
            dependency = frame.get_dependency_linker()
            if dependency:  # If the frame has a dependency add it

                # Get the z3 variables from the predecessor and the successor dependency
                predecessor_dependency = dependency.get_parent()
                if predecessor_dependency:  # If the dependency has a parent (if not is the top and nothing to do)
                    predecessor_path = network.get_frame_path_from_link(predecessor_dependency.get_frame_index(),
                                                                        predecessor_dependency.get_link_index())
                    predecessor_offset = predecessor_path.get_name_offset(0, 0)

                    successor_path = network.get_frame_path_from_link(dependency.get_frame_index(),
                                                                      dependency.get_link_index())
                    successor_offset = successor_path.get_name_offset(0, 0)

                    # Init the variable in the file again, just in case it appeared in previous segments
                    value = predecessor_path.get_offset(0, 0)
                    if value is not None and value < starting_time and \
                            (predecessor_dependency.get_frame_index() not in [other_frame.get_frame_index()
                                                                              for other_frame in frames]) \
                            and predecessor_offset not in already_init_predecessor:
                        self.__smt_lib_file.write("(declare-fun " + predecessor_offset + " () Int)\n")
                        self.__smt_lib_file.write("(assert (= " + predecessor_offset + ' (- ' + str(value) + ')))\n')
                        already_init_predecessor.append(predecessor_offset)

                    if dependency.get_deadline() > 0:  # If there are deadline dependency
                        # self.__smt_lib_file.write("(assert (< " + successor_offset + "(+ " + predecessor_offset + " "
                        #                          + str(dependency.get_deadline()) + ")))\n")
                        # self.__smt_lib_file.write("(assert (> " + successor_offset + " " +
                        # predecessor_offset + "))\n")
                        self.__smt_lib_file.write("(assert (> " + successor_offset + "(- " + predecessor_offset + " "
                                                  + str(dependency.get_deadline()) + ")))\n")
                        self.__smt_lib_file.write("(assert (< " + successor_offset + " " + predecessor_offset + "))\n")
                        # Also has to be after at least, so waiting > 0
                    if dependency.get_waiting() > 0:  # If there are waiting dependency
                        # self.__smt_lib_file.write("(assert (> " + successor_offset + "(+ " + predecessor_offset + " "
                        #                          + str(dependency.get_waiting()) + ")))\n")
                        self.__smt_lib_file.write("(assert (< " + successor_offset + "(- " + predecessor_offset + " "
                                                  + str(dependency.get_waiting()) + ")))\n")

    def check_satisfiability(self):
        """
        Check if the current context is satisfiable or not
        :return: 1 if satisfiable, 0 is not
        :rtype: int
        """
        self.__smt_lib_file.write("(check-sat)\n")
        self.__smt_lib_file.write("(get-model)")
        self.__smt_lib_file.close()

        subprocess.run('./yices-smt2 Constraints.smt > Solution.smt', stdout=subprocess.PIPE, shell=True)

        """ Uses z3 solver, but is shit
        start_time = time.time()
        subprocess.run('./z3 -smt2 Constraints.smt', stdout=subprocess.PIPE, shell=True)
        print("--- Check Time Z3 %s seconds ---" % (time.time() - start_time))
        """

        # Get if sat or not from the solution file
        self.__solution_file = open('Solution.smt', 'r')
        sat = self.__solution_file.readline()

        return sat == 'sat\n'

    def save_solution(self, network, frames):
        """
        Save offsets from the given frames in the smt solver and also saves them as integers in the matrix offset
        :param network: network object
        :param frames: list of frames to fix
        :type network: Network
        :type frames: list of FrameBlock
        :return: 
        """
        # Read all the solutions from the smt solver file
        values = self.__solution_file.readlines()
        for line_value in values:  # The first line says only sat, not interesting
            words = line_value.split(' ')
            offset_information = words[1].split('_')
            if offset_information[0] == 'Offset':  # If is the information of an offset
                frame = int(offset_information[1])
                for frame_index in frames:
                    if frame_index.get_frame_index() == frame:
                        link = int(offset_information[2])
                        instance = int(offset_information[3])
                        replica = int(offset_information[4])
                        path = network.get_frame_path_from_link(frame, link)
                        try:
                            offset_value = int(words[2].split(')')[0])
                        except ValueError:      # If we go here, the number is negative and is in the next position!
                            offset_value = int(words[3].split(')')[0])
                        path.set_offset(instance, replica, offset_value)
                        break
        self.__solution_file.close()

    def load_fixed_values(self, network, frames, starting_time, ending_time):
        """
        Fix the offsets as new constraints in a new SMT LIB file
        :param network: network object
        :param frames: list of frames to fix
        :param starting_time: starting time to init the constraints
        :param ending_time: ending time to init the constraints
        :type network: Network
        :type frames: list of FrameBlock
        :type starting_time: int
        :type ending_time: int
        :return: 
        """
        # Open a new file and load the fixed values
        self.__smt_lib_file = open('Constraints.smt', 'w')
        self.__smt_lib_file.write("(set-logic QF_LIA)\n")

        # Load values of the scheduled frames
        for frame in frames:  # For all given frames
            frame_index = frame.get_frame_index()
            for path in network.get_frame_paths(frame_index):
                for instance in range(path.get_num_instances()):
                    for replica in range(path.get_num_replicas()):
                        value = path.get_offset(instance, replica)
                        if starting_time < value < ending_time:
                            name = 'Offset_' + str(frame_index) + '_' + str(path.get_link_id()) + '_' + str(instance) \
                                   + '_' + str(replica)
                            self.__smt_lib_file.write("(declare-fun " + name + " () Int)\n")
                            self.__smt_lib_file.write("(assert (= " + name + " (- " + str(value) + ")))\n")

        """# Also load values of the sensing and control
        if network.get_sensing_control_period():
            for path in network.get_sensing_control_path():
                for instance in range(path.get_num_instances()):
                    name = 'Sensing_Control_' + str(path.get_link_id()) + '_' + str(instance)
                    value = instance * network.get_sensing_control_period()
                    self.__smt_lib_file.write("(assert (= " + name + " " + str(-value) + "))\n")
        """
