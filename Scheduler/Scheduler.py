"""* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 *                                                                                                                     *
 *  Scheduler Class                                                                                                    *
 *  Scheduler                                                                                                          *
 *                                                                                                                     *
 *  Created by Francisco Pozo on 26/04/17.                                                                             *
 *  Copyright © 2017 Francisco Pozo. All rights reserved.                                                              *
 *                                                                                                                     *
 *  Class that contains the information and algorithms to build the Schedule.                                          *
 *  Different algorithms to build the schedule and store it in a sorted list of all frames in the network. Such        *
 *  list will the sorted by the order in which the frames will be scheduled (in segmented approaches).                 *
 *  It also contains auxiliary structures to save characteristics of the frames and the network in order to perform    *
 *  the scheduling.                                                                                                    *
 *  The main approaches used are one-shot and segmented. Every technique has a different performance.                  *
 *  The better performance, the worse "quality" or compactness the final schedule will have.                           *
 *  Also numerous optimizations can be applied to different techniques to try to modify the "quality" of the schedules *
 *                                                                                                                     *
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * ** * * * * * * * * * * * * * * *"""

from Scheduler.Z3Synthesizer import Z3Synthesizer
from Scheduler.Network import Network
from Scheduler.Dependency import DependencyNode
from xml.dom import minidom
import xml.etree.ElementTree as Xml
import logging
import time


class FrameBlock:
    """
    Frame block of the frame queue, it only contains the frame index and its absolute deadline
    """

    # Variable definitions #

    __frame = None
    __absolute_deadline = None
    __dependency_linker = None

    # Standard function definitions #

    def __init__(self, frame_index, absolute_deadline):
        self.__frame = frame_index
        self.__absolute_deadline = absolute_deadline
        self.__dependency_linker = None

    def get_frame_index(self):
        """
        Get the frame index
        :return: frame index
        """
        return self.__frame

    def set_deadline(self, deadline):
        """
        Sets the deadline
        :param deadline: deadline
        :type deadline: int
        :return: 
        """
        self.__absolute_deadline = deadline

    def get_deadline(self):
        """
        Gets the absolute deadline
        :return: absolute deadline
        :rtype: int
        """
        return self.__absolute_deadline

    def get_dependency_linker(self):
        """
        Get the dependency linker
        :return: dependency linker
        :rtype: DependencyNode
        """
        return self.__dependency_linker

    def set_dependency_linker(self, dependency_node):
        """
        Set a link to the dependency tree object
        :param dependency_node: dependency node
        :type dependency_node: DependencyNode
        :return: 
        """
        self.__dependency_linker = dependency_node


class Scheduler:
    """
    Scheduler Class that contains the one-shot and segmented algorithms and the general solve function
    """

    # Variable definitions #

    __frame_queue = []
    __SMT_solver = None
    __network = None
    __time_checking = None
    __time_init = None
    __time_re_init = None
    __time_dependencies = None
    __time_path = None
    __time_switch = None
    __time_simultaneous = None
    __time_contention = None
    __save_solution = None

    # Standard function definitions #

    def __init__(self):
        logging.basicConfig(level=logging.DEBUG)
        self.__frame_queue = []
        self.__SMT_solver = None
        self.__network = None
        self.__time_checking = 0
        self.__time_init = 0
        self.__time_re_init = 0
        self.__time_dependencies = 0
        self.__time_path = 0
        self.__time_switch = 0
        self.__time_simultaneous = 0
        self.__time_contention = 0
        self.__save_solution = 0

    def one_shot_scheduler(self, input_name, output_name):
        """
        Schedules the network in one call of the smt solver
        :param input_name: network input xml file name with the relative direction
        :param output_name: schedule output xml file name with the relative direction
        :return: True if schedule was found, False otherwise
        r:type: Boolean
        """
        # Read the network and add all information
        self.__network = Network()
        self.__network.parse_network_xml(input_name)

        dependencies = self.__network.get_dependencies()       # Get the dependency trees to accelerate everything
        # Create the frame queue (without absolute deadline as is not needed in the one shot scheduler)
        for index in range(self.__network.get_number_frames()):
            self.__frame_queue.append(FrameBlock(index, None))
            # If the frame has a dependency, link it
            self.__frame_queue[-1].set_dependency_linker(dependencies.get_dependency_by_frame(index))

        # Init the solver and the constraints
        self.__SMT_solver = Z3Synthesizer()                 # Init the SMT solver Z3

        # Init the Z3 variables in the frames
        self.__SMT_solver.init_variables(self.__network, self.__frame_queue, 0, self.__network.get_hyper_period())

        # Add all the constraints
        self.__SMT_solver.contention_free(self.__network, self.__frame_queue, [], 0,
                                          self.__network.get_hyper_period())
        self.__SMT_solver.path_dependent(self.__network, self.__frame_queue)
        self.__SMT_solver.switch_memory(self.__network, self.__frame_queue)
        self.__SMT_solver.simultaneous_dispatch(self.__network, self.__frame_queue)
        self.__SMT_solver.dependencies_constraints(self.__network, self.__frame_queue, 0)

        if self.__SMT_solver.check_satisfiability():
            logging.debug('Eureka')
        else:
            logging.debug('We miserably failed')
            return False

        self.__SMT_solver.save_solution(self.__network, self.__frame_queue)

        self.__generate_schedule_xml(input_name, output_name)

        return True

    def incremental_approach(self, input_name, output_name):
        """
        Schedules the network in incremental calls of the smt solver
        :param input_name: network input xml file name with the relative direction
        :param output_name: schedule output xml file name with the relative direction
        :return: True if schedule was found, False otherwise
        r:type: Boolean
        """
        # Read the network and add all information
        self.__network = Network()
        self.__network.parse_network_xml(input_name)

        dependencies = self.__network.get_dependencies()       # Get the dependency trees to accelerate everything
        # Create the frame queue (without absolute deadline as is not needed in the one shot scheduler)
        for index in range(self.__network.get_number_frames()):
            self.__frame_queue.append(FrameBlock(index, None))
            # If the frame has a dependency, link it
            self.__frame_queue[-1].set_dependency_linker(dependencies.get_dependency_by_frame(index))

        # Variables for the iteration of the scheduler
        starting_frame = 0
        step_size = 5

        # Init the solver and the constraints
        self.__SMT_solver = Z3Synthesizer()                 # Init the SMT solver Z3

        # While there are frames to schedule, iterate
        while starting_frame < self.__network.get_number_frames():

            # Create the frame queues that we are going to use
            current_frame_queue = self.__frame_queue[starting_frame:starting_frame + step_size]
            if starting_frame - 1 >= 0:
                previous_frame_queue = self.__frame_queue[:starting_frame]
            else:
                previous_frame_queue = []

            # Add all the constraints
            self.__SMT_solver.init_variables(self.__network, current_frame_queue, 0,
                                             self.__network.get_hyper_period())
            self.__SMT_solver.contention_free(self.__network, current_frame_queue, previous_frame_queue, 0,
                                              self.__network.get_hyper_period())
            self.__SMT_solver.path_dependent(self.__network, current_frame_queue)
            self.__SMT_solver.switch_memory(self.__network, current_frame_queue)
            self.__SMT_solver.simultaneous_dispatch(self.__network, current_frame_queue)
            self.__SMT_solver.dependencies_constraints(self.__network, current_frame_queue, 0)

            # If it is satisfiable, create the model and save the values
            if self.__SMT_solver.check_satisfiability():
                self.__SMT_solver.save_solution(self.__network, current_frame_queue)
                starting_frame += step_size
                self.__SMT_solver.load_fixed_values(self.__network, self.__frame_queue[:starting_frame], 0,
                                                    self.__network.get_hyper_period())
            else:
                logging.debug('We miserably failed')
                return False

        self.__generate_schedule_xml(input_name, output_name)
        logging.debug('Eureka')
        return True

    def segmented_approach(self, input_name, output_name):
        """
        Divides the network in segments and schedules every single one with an incremental approach
        :param input_name: network input xml file name with the relative direction
        :param output_name: schedule output xml file name with the relative direction
        :return: True if schedule was found, False otherwise
        r:type: Boolean
        """
        # Read the network and add all information
        self.__network = Network()
        self.__network.parse_network_xml(input_name)

        dependencies = self.__network.get_dependencies()       # Get the dependency trees to accelerate everything

        # Create the frame queue (without absolute deadline as is not needed in the one shot scheduler)
        for index in range(self.__network.get_number_frames()):
            dependency = dependencies.get_dependency_by_frame(index)
            waiting_time = 0 if dependency is None else dependency.get_maximum_waiting_time_node()
            deadline = self.__network.get_frame_deadline(index) - waiting_time
            self.__frame_queue.append(FrameBlock(index, deadline))
            # If the frame has a dependency, link it
            self.__frame_queue[-1].set_dependency_linker(dependency)

        # Sort the frame queues from smaller to largest deadline
        self.__frame_queue.sort(key=lambda x: x.get_deadline())

        # Variables for the iteration of the scheduler
        free_space_segment = True                               # True when more frames can be scheduled in the segment
        all_frames_schedules = False                            # True if we scheduled all frames
        step_size = 5                                           # Number of frames scheduled per incremental iteration
        segment_size = 1000000                                  # Size of the segment to schedule
        starting_frame = 0                                      # Starting frame to schedule in the incremental approach
        starting_time = 0                                       # Starting time of the segment being scheduled
        ending_time = segment_size                              # Ending time of the segment being scheduled
        previous_frame_queue = []                               # Frame queue of previous scheduled frames that appear
        # in the current segment being scheduled

        # Init the solver and the constraints
        self.__SMT_solver = Z3Synthesizer()  # Init the solver class

        # While we did not schedule all segments or all frames, keep scheduling segments
        while not all_frames_schedules and starting_time < self.__network.get_hyper_period():

            # Adjust the segment size if it is bigger than the hyper period
            if ending_time > self.__network.get_hyper_period():
                ending_time = self.__network.get_hyper_period()

            if starting_frame > 0:
                start = time.time()
                previous_frame_queue = self.__SMT_solver.re_init_variables(self.__network,
                                                                           self.__frame_queue[:starting_frame],
                                                                           starting_time, ending_time)
                self.__time_re_init += time.time() - start

            # While more frames can be scheduled in the segment, continue
            while free_space_segment:
                # Adjust the frames to be scheduled if it is bigger than the number of frames
                # Also, if it is the same as the frames, we exit of the main loop after schedule this segment
                if starting_frame + step_size >= self.__network.get_number_frames():
                    step_size = self.__network.get_number_frames() - step_size

                # Create the frame queues that we are going to use
                current_frame_queue = self.__frame_queue[starting_frame:starting_frame + step_size]

                # Add all the constraints
                start = time.time()
                self.__SMT_solver.init_variables(self.__network, current_frame_queue, starting_time, ending_time)
                self.__time_init += time.time() - start

                start = time.time()
                self.__SMT_solver.contention_free(self.__network, current_frame_queue, previous_frame_queue,
                                                  starting_time, ending_time)
                self.__time_contention += time.time() - start

                start = time.time()
                self.__SMT_solver.path_dependent(self.__network, current_frame_queue)
                self.__time_path += time.time() - start

                start = time.time()
                self.__SMT_solver.switch_memory(self.__network, current_frame_queue)
                self.__time_switch += time.time() - start

                start = time.time()
                self.__SMT_solver.simultaneous_dispatch(self.__network, current_frame_queue)
                self.__time_simultaneous += time.time() - start

                start = time.time()
                self.__SMT_solver.dependencies_constraints(self.__network, current_frame_queue, starting_time)
                self.__time_dependencies += time.time() - start

                # If it is satisfiable, create the model and save the values
                start = time.time()
                sat = self.__SMT_solver.check_satisfiability()
                self.__time_checking += time.time() - start
                if sat:
                    start = time.time()
                    self.__SMT_solver.save_solution(self.__network, current_frame_queue)
                    self.__save_solution += time.time() - start

                    # If all frames have been scheduled, end all the loops
                    if (starting_frame + step_size + 1) >= len(self.__frame_queue):
                        all_frames_schedules = True
                        free_space_segment = False

                    starting_frame += step_size
                    start = time.time()
                    previous_frame_queue = self.__SMT_solver.re_init_variables(self.__network,
                                                                               self.__frame_queue[:starting_frame],
                                                                               starting_time, ending_time)
                    self.__time_re_init += time.time() - start

                # If it is not satisfiable, we set the segment as full, and move to schedule the next segment
                else:
                    logging.debug('Segment is full')
                    free_space_segment = False
                    starting_time = ending_time
                    ending_time += segment_size

            free_space_segment = True

        self.__generate_schedule_xml(input_name, output_name)
        logging.debug('Eureka')

        print("--- Init Time %s seconds ---" % self.__time_init)
        print("--- Re Init Time %s seconds ---" % self.__time_re_init)
        print("--- Contention Time %s seconds ---" % self.__time_contention)
        print("--- Path Time %s seconds ---" % self.__time_path)
        print("--- Switch Time %s seconds ---" % self.__time_switch)
        print("--- Simultaneous Time %s seconds ---" % self.__time_simultaneous)
        print("--- Dependencies Time %s seconds ---" % self.__time_dependencies)
        print("--- Save Time %s seconds ---" % self.__save_solution)
        print("--- Check Time %s seconds ---" % self.__time_checking)

        return True

    def check_schedule(self):
        """
        Checks if the generated schedule satisfies the constraints
        :return: 
        """
        print('The schedule found is => ' + str(self.__network.check_schedule()))

    # Output XML functions

    def __generate_schedule_xml(self, input_name, output_name):
        """
        Writes the schedule in a XML file
        :param input_name: name of the input xml file, needed for the relative direction
        :param output_name: name of the output xml file
        :type input_name: str
        :type output_name: str
        :return: 
        """
        # Create top of the xml file
        schedule_xml = Xml.Element('Schedule')

        # Write the general information of the network
        general_information_xml = Xml.SubElement(schedule_xml, 'GeneralInformation')
        Xml.SubElement(general_information_xml, 'HyperPeriod').text = str(self.__network.get_hyper_period())
        Xml.SubElement(general_information_xml, 'Utilization').text = str(self.__network.get_utilization())

        # Write the frames
        frames_xml = Xml.SubElement(schedule_xml, 'Frames')
        for frame_index, frame in enumerate(self.__network.get_frames()):           # For every frame in the network
            frame_xml = Xml.SubElement(frames_xml, 'Frame')
            Xml.SubElement(frame_xml, 'FrameID').text = str(frame_index)
            for path in self.__network.get_frame_paths(frame_index):    # For every path in the frame
                path_xml = Xml.SubElement(frame_xml, 'Link')
                Xml.SubElement(path_xml, 'LinkID').text = str(path.get_link_id())
                for instance in range(path.get_num_instances()):
                    instance_xml = Xml.SubElement(path_xml, 'Instance')

                    for replica in range(path.get_num_replicas()):
                        replica_xml = Xml.SubElement(instance_xml, 'Replica')

                        # Write which instance and replica is the actual transmission
                        Xml.SubElement(replica_xml, 'NumberInstance').text = str(instance)
                        Xml.SubElement(replica_xml, 'NumberReplica').text = str(replica)

                        # Write the transmission time
                        value = path.get_offset(instance, replica)
                        transmission_xml = Xml.SubElement(replica_xml, 'TransmissionTime')
                        transmission_xml.text = str(value)
                        transmission_xml.set('unit', 'ns')

                        # Write the ending time
                        value += int(path.get_transmission_time())
                        ending_xml = Xml.SubElement(replica_xml, 'EndingTime')
                        ending_xml.text = str(value)
                        ending_xml.set('unit', 'ns')

        # Write the sensing and control blocks
        if self.__network.get_sensing_control_period():
            sensing_control_xml = Xml.SubElement(schedule_xml, 'SensingControl')
            for path in self.__network.get_sensing_control_path():
                path_xml = Xml.SubElement(sensing_control_xml, 'Link')
                Xml.SubElement(path_xml, 'LinkID').text = str(path.get_link_id())

                for instance in range(path.get_num_instances()):
                    instance_xml = Xml.SubElement(path_xml, 'Instance')

                    # Write which instance and replica is the actual transmission
                    Xml.SubElement(instance_xml, 'NumberInstance').text = str(instance)

                    # Write the transmission time
                    value = path.get_offset(instance, 0)
                    transmission_xml = Xml.SubElement(instance_xml, 'TransmissionTime')
                    transmission_xml.text = str(value)
                    transmission_xml.set('unit', 'ns')

                    # Write the ending time
                    value += int(path.get_transmission_time())
                    ending_xml = Xml.SubElement(instance_xml, 'EndingTime')
                    ending_xml.text = str(value)
                    ending_xml.set('unit', 'ns')

        # Write the final file
        output_xml = minidom.parseString(Xml.tostring(schedule_xml)).toprettyxml(indent="   ")
        name = input_name.split('/')
        name = name[0] + '/' + name[1] + '/schedules/' + output_name
        with open(name, "w") as f:
            f.write(output_xml)
