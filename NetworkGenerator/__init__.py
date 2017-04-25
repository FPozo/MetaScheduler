# -*- coding: utf-8 -*-

"""* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 *                                                                                                                     *
 *  MetaScheduler Package                                                                                              *
 *  Network Generator                                                                                                  *
 *                                                                                                                     *
 *  Created by Francisco Pozo on 17/04/17.                                                                             *
 *  Copyright © 2017 Francisco Pozo. All rights reserved.                                                              *
 *                                                                                                                     *
 *  Package to create Deterministic Ethernet Networks                                                                  *
 *  The main purpose is to create network inputs to be scheduler for a scheduler later on. Then, it can create         *
 *  non-cyclic networks with period time-triggered frames.                                                             *
 *  Such frames have paths from a sender to one or multiple receivers, a period and a size (not exceeding the Ethernet *
 *  Standard). They may also have deadlines and dependencies between different frames in terms of minimum and maximum  *
 *  time to wait to be delivered.                                                                                      *
 *  Even though the package is designed to create synthesized networks, real networks also can be implemented.         *
 *  Some basic configurations will be provided to create some cases as the number of parameters can be large.          *
 *                                                                                                                     *
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * """