from NetworkGenerator.Network import Network as nx
from Scheduler.Network import *
from Scheduler.Scheduler import *

from z3 import *

"""
description, links = network.get_network_topology_from_xml('Configuration.xml', 0)

print(description)
print(links)

num_frames, single, local, multiple, broadcast = network.get_traffic_information_from_xml('Configuration.xml', 0)

print(num_frames)
print(single)
print(local)
print(multiple)
print(broadcast)

periods, per_periods, deadlines, sizes = network.get_frames_description_from_xml('Configuration.xml', 0)

print(per_periods)
print(periods)
print(deadlines)
print(sizes)

num_dependencies, min_depth, max_depth, min_children, max_children, min_time_waiting, max_time_waiting, \
            min_time_deadline, max_time_deadline, waiting, deadline, waiting_deadline = \
            network.get_dependencies_from_xml('Configuration.xml', 0)

print(num_dependencies, min_depth, max_depth, min_children, max_children, min_time_waiting, max_time_waiting,
      min_time_deadline, max_time_deadline, waiting, deadline, waiting_deadline)

list_replicas = network.get_number_replicas_from_xml('Configuration.xml', 0, 0)

print(list_replicas)

policy = network.get_replica_policy_from_xml('Configuration.xml', 0, 1)

print(policy)

interval = network.get_replica_interval_from_xml('Configuration.xml', 0, 1)

print(interval)

min_time_switch = network.get_minimum_time_switch_from_xml('Configuration.xml', 0, 1)

print(min_time_switch)

max_time_switch = network.get_maximum_time_switch_from_xml('Configuration.xml', 0, 1)

print(max_time_switch)

sensing_control_period = network.get_sensing_control_period_from_xml('Configuration.xml', 0, 0)

print(sensing_control_period)

sensing_control_time = network.get_sensing_control_time_from_xml('Configuration.xml', 0, 0)

print(sensing_control_time)
"""
import time



#network = nx()
#network.create_networks_from_xml('Configuration.xml')

solver = Scheduler()

start_time = time.time()
solver.incremental_approach('networks/db95cb5826b5018e3ec0adb367721e07/db95cb5826b5018e3ec0adb367721e07', 'Shit')
print("--- Total Time Incremental Process  %s seconds ---" % (time.time() - start_time))

start_time = time.time()
solver.check_schedule()
print("--- Check Time %s seconds ---" % (time.time() - start_time))

start_time = time.time()

solver.check_schedule()

print("--- Check Time %s seconds ---" % (time.time() - start_time))

solver = Scheduler()

start_time = time.time()
solver.one_shot_scheduler('networks/db95cb5826b5018e3ec0adb367721e07/db95cb5826b5018e3ec0adb367721e07', 'Shit')
print("--- Total Time One-Shot Process  %s seconds ---" % (time.time() - start_time))

start_time = time.time()
solver.check_schedule()
print("--- Check Time %s seconds ---" % (time.time() - start_time))