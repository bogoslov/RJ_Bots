#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Purpose: 
Created: 05.05.2015
Author : Aleksey Bogoslovskyi
"""

import sys
from utils import Utils


if __name__ == '__main__':
    if len(sys.argv) == 2:
        try:
            utils = Utils()
            if sys.argv[1] == "mercs":

                utils.update_participant()
                utils.get_participants_present()
                utils.send_interactions()
            elif sys.argv[1] == "present":
                utils.get_group_plugin_present()
            else:
                pass
        except Exception, err:
            print err
    else:
        print "Not enough params"