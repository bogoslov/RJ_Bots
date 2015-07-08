#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Purpose: 
Created: 14.06.2013
Author:  Aleksey Bogoslovskyi
"""
from time import sleep
from utils import Utils, ENDPOINT
from db_api import DB_API
NETS = ["vk", "mr", "od", "fb"]

if __name__ == '__main__':
    utils = Utils()
    # utils.update_participant()
    db = DB_API()
    # db.create_tables()
    # utils.update_statistics()

    # res = db.get_data(table="STATISTICS", multiple=True)
    # for item in res:
    #     res = db.get_data(table="STATISTICS", condition="UID='%s'" % item.get("UID"))
    #     name = utils.get_user_name(item.get("UID")).encode('utf-8')
    #     res.update({"NAME": name})
    #     db.upsert_data(table="STATISTICS", data=res)


    # res = db.get_data(table="STATISTICS", multiple=True)
    # for item in res:
    #     res = db.get_data(table="STATISTICS", condition="UID='%s'" % item.get("UID"))
    #     if int(res.get("WEEK_CLAN")) != 0:
    #         perc = round(100 * float(res.get("WEEK_CLAN_WIN")) / res.get("WEEK_CLAN"), 2)
    #         res.update({"WEEK_PERCENTAGE": perc, "NAME": res.get("NAME").encode('utf-8')})
    #         db.upsert_data(table="STATISTICS", data=res)



    # current = []
    # for clan_id in ["25c139b2f8c2420a5c1130c6f9a6f3ce"]:
    #     current.extend([item.keys()[0] for item in utils.get_clan_participant(clan_id)])  # Get clan participant from game
    #
    # print current
    # saved = utils.get_available("DYNAMIC")
    # print saved
    # for item in list(set(saved) - set(current)):
    #     print item
    #     db.delete_data(table="PARTICIPANT", condition="UID='%s'" % item)



# group 17027 448

    # utils.send_interactions()
    # add_recipient = [{user["UID"]: user["AUTH"]}
    #                   for user in db.get_data(table="ARCHIVE", multiple=True,
    #                                           condition="AUTH is not NULL and UID like '%s%%'" % net)]
    # for net in NETS:
    #     print [user["UID"] for user in db.get_data(table="ADD_RECIPIENTS",
    #                                                multiple=True,
    #                                                condition="UID like '%s%%'" % net)]
    # utils.get_group_plugin_present()


    # flag, info = utils.get_participant_info("vk:2342994", "c0a426784e761547e57afcc6d2bbc367")
    # utils.buy_trade_products("vk:2342994", "c0a426784e761547e57afcc6d2bbc367", info["sid"])




    # utils.get_present("vk:2342994", "c0a426784e761547e57afcc6d2bbc367", 17477)


    # utils.get_present(uid="vk:226723848", auth="5ae2b8d8c425d6744cf14068d91fe816", plugin=21439)
    # utils.get_present(uid="vk:12718015", auth="f83717f4879b627e274b3cba9e155db6", plugin=21439)
    # utils.get_present(uid="vk:2342994", auth="b8e1aa38f01e4a83a3fea39334d0edbf", group=18247)

    # db.create_tables()

    # db.upsert_data("PRESENT", {"TYPE": "PLUGIN", "COUNTER": 1, "START_POINT": 1, "FIRST_STEP": 1})
    # db.upsert_data("PRESENT", {"TYPE": "GROUP", "COUNTER": 2, "START_POINT": 16978, "FIRST_STEP": 421})




    # COUNTER starts from 0
    # On each cycle loop START_POINT + 63 and FIRST_STEP + 9

    # START_POINT + FIRST_STEP * COUNTER + (COUNTER - 1) * 2
    # START_POINT + (FIRST_STEP + 2) * COUNTER - 2
    # print 16978 + 421 * 2 + (2 - 1) * 2
    # print 16978 + (421 + 2) * 3 - 2  # 18245

    # utils.add_participant(uid="mr:16365741323372014699", auth="10fc990ae1a57a078e56ca2a6780c606")
    # utils.add_participant(uid="vk:2342994")
    # utils.add_participant(uid="vk:18567045")
    # utils.add_participant(uid="vk:229437930")
    # utils.add_participant(uid="vk:169354101")
    # utils.add_participant(uid="vk:169354101")
    # utils.update_users_clans()
    # utils.update_participant()

        # daily = user.get("DAILY_SCHEMA", None)
        # event = user.get("EVENT_SCHEMA", None)


    # db.create_tables()

    # print utils.get_current_merc("vk:2342994")
    # print utils.get_available()

    # result = []
    # res = db.get_data("participant", multiple=True)
    # for item in res:
    #     result.append(item.get("UID"))
    #
    # print result
    # utils.update_users_clans()
    # utils.update_participant()
    # utils.add_participant(uid="vk:2342994")
    # utils.add_participant(uid="mr:17273545492366541080", auth="77fdcf629194f89ff767e79d6843cedf")
    # for item in change_default_time(TIMER, "1800"):
    #     print item
    # flag, response = utils.get_user_info("vk:2342994", "8bf09888459a49e3c9cee77ad304343e")
    # print flag, response
    # print utils.avail_check({"money": False, "food": True, "fuel": False})




    # utils.add_user("alex", "2342994", "c7ab8df30c754399217bd7e051ddf690")

    # utils.add_user("yac", "18567045")
    # sid = utils.get_sid("2342994", "c7ab8df30c754399217bd7e051ddf690")
    # print "SID", sid
    # print utils.get_resource(sid, 592)
    # utils.set_resource(sid, "contract_stone_05", "9")


