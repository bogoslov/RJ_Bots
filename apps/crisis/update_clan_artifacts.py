#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Purpose: 
Created: 28.08.2015
Author : Aleksey Bogoslovskyi
"""

from utils import Utils

if __name__ == '__main__':
    try:
        utils = Utils()
        utils.update_artefats_info(days=0)
    except Exception, err:
        print err