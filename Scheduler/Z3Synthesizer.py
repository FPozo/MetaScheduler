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
        if starting_time == 0:
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
