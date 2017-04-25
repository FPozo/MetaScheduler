# -*- coding: utf-8 -*-

"""* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 *                                                                                                                     *
 *  MetaScheduler Package                                                                                              *
 *  Scheduler                                                                                                          *
 *                                                                                                                     *
 *  Created by Francisco Pozo on 25/04/17.                                                                             *
 *  Copyright © 2017 Francisco Pozo. All rights reserved.                                                              *
 *                                                                                                                     *
 *  Package to create Deterministic Ethernet Schedules                                                                 *
 *  The main purpose of this package is, given a Deterministic Ethernet Network with traffic, create its schedule.     *
 *  To do so, it will use a Satisfiability Modulo Theory (SMT) Solver, Z3, with the Python API.                        *
 *  As SMT solvers are not as powerful to schedule very large networks, we will use a divide and conquer strategy,     *
 *  the segmented approach, to divide the schedule in segments easy to solve for the SMT solver. On top of that, every *
 *  segment will be schedule with a incremental approach to further speed the process.                                 *
 *  Also, different optimizations will be implemented to reduce the synthesis time and improve the compactness of the  *
 *  schedule.
 *                                                                                                                     *
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * """