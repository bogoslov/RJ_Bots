#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Purpose: 
Created: 06.05.2015
Author : Aleksey Bogoslovskyi
"""

from django.template.defaulttags import register


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def get_slice(data_list, slicer):
    start, finish = slicer.split(":")
    try:
        start = int(start)
    except:
        start = 0
    try:
        finish = int(finish)
    except:
        finish = len(data_list)

    return data_list[start:finish]


@register.filter
def concatenate(arg1, arg2):
    return "%s%s" % (arg1, arg2)