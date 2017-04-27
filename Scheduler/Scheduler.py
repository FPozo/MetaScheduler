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
from xml.dom import minidom
import xml.etree.ElementTree as Xml
import logging


class FrameBlock:
    """
    Frame block of the frame queue, it only contains the frame index and its absolute deadline
    """

    # Variable definitions #

    __frame = None
    __absolute_deadline = None

    # Standard function definitions #

    def __init__(self, frame_index, absolute_deadline):
        self.__frame = frame_index
        self.__absolute_deadline = absolute_deadline

    def get_frame_index(self):
        """
        Get the frame index
        :return: frame index
        """
        return self.__frame


class Scheduler:
    """
    Scheduler Class that contains the one-shot and segmented algorithms and the general solve function
    """

    # Variable definitions #

    __frame_queue = []
    __SMT_solver = None
    __network = None

    # Standard function definitions #

    def __init__(self):
        logging.basicConfig(level=logging.DEBUG)
        self.__frame_queue = []
        self.__SMT_solver = None
        self.__network = None

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

        # Create the frame queue (without absolute deadline as is not needed in the one shot scheduler)
        for index in range(self.__network.get_number_frames()):
            self.__frame_queue.append(FrameBlock(index, None))

        # Init the solver and the constraints
        self.__SMT_solver = Z3Synthesizer()                 # Init the SMT solver Z3
        # Init the Z3 variables in the frames
        self.__SMT_solver.init_z3_variables(self.__network, self.__frame_queue, 0, self.__network.get_hyper_period())

        if self.__SMT_solver.check_satisfiability():
            logging.debug('Eureka')
        else:
            logging.debug('We miserably failed')
            return False

        self.__SMT_solver.create_model()
        self.__SMT_solver.fix_offsets(self.__network, self.__frame_queue)

        self.__generate_schedule_xml(input_name, output_name)

        return True

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
        for frame in self.__frame_queue:                                # For every frame in the network
            frame_index = frame.get_frame_index()
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
