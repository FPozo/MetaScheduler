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
 *  It also contains the offset matrix (appearance/transmission) for every link.                                       *
 *                                                                                                                     *
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * """


class TreePath:
    """
    Class with the tree path of a frame that contains the information over all links with the transmission time
    """

    # Variable definitions #

    __link = None
    __size = None
    __offset = [[]]
    __z3_offset = [[]]
    __parent = None
    __children = []

    # Standard function definitions #


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
