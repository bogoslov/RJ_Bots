#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Purpose: 
Created: 14.06.2013
Author:  Aleksey Bogoslovskyi
"""
from utils import Utils
# from pymongo import Connection, errors
TIMER = [{"value": "30 min", "data": "1800"},
         {"value": "1 hour", "data": "3600", "selected": True},
         {"value": "2 hour", "data": "7200"},
         {"value": "4 hour", "data": "14400"}]


def change_default_time(time_list, selected_value):
    result = []
    for item in time_list:
        if item.get("selected", False):
            item.update({"selected": False})
        if item.get("data", None) == selected_value:
            item.update({"selected": True})
        result.append(item)
    return result


if __name__ == '__main__':
    utils = Utils()
    for item in change_default_time(TIMER, "1800"):
        print item
    # flag, response = utils.get_user_info("vk:2342994", "8bf09888459a49e3c9cee77ad304343e")
    # print flag, response
    # print utils.avail_check({"money": False, "food": True, "fuel": False})




    # utils.add_user("alex", "2342994", "c7ab8df30c754399217bd7e051ddf690")

    # utils.add_user("yac", "18567045")
    # sid = utils.get_sid("2342994", "c7ab8df30c754399217bd7e051ddf690")
    # print "SID", sid
    # print utils.get_resource(sid, 592)
    # utils.set_resource(sid, "contract_stone_05", "9")
