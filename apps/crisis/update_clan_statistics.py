#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Purpose: 
Created: 07.07.2015
Author : Aleksey Bogoslovskyi
"""

from utils import Utils

if __name__ == '__main__':
    try:
        utils = Utils()
        utils.update_participant()
        utils.update_statistics()
    except Exception, err:
        print err