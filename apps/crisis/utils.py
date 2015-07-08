#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Purpose: 
Created: 11.08.2014
Author:  Aleksey Bogoslovskyi
"""

import urllib2
import logging
from time import sleep, time
from datetime import datetime
from random import choice
from threading import Thread, Event
from re import match, compile
from xml.dom.minidom import parseString
from json import loads

# import additional_senders
from db_api import DB_API


NETS = ["vk", "mr", "od", "fb"]
ENDPOINT = "https://game-r03ww.rjgplay.com/command"
ENDPOINT_DATA = "https://data-r03ww.rjgplay.com"

# icon links https://media-r03ru.rjgplay.com/resources/common/common/media/icons/items/64x64/rating_64x64.png

RESOURCES = ["food", "money", "fuel"]
ADD_TIMEOUT = 0.5
TIMEOUT = 60
RESOURCE_TIMEOUT = 7200  # 2 hours
DAILY_HOUR = 03
DAILY_MINUTE = 00
BLOCK_TIMEOUT = int(30 * 60)  # 30 minutes

MERCS = ["sniper", "tank_abrams", "commando", "soldier"]

ENTITY = ["kevlar_fiber", "laser_aimer", "gun_receiver", "powder_charge", "armor_composite", "armor_plate",
          "control_block", "tnt_charge", "rare_item"]
PARTS = ["soldier_gun", "gunner_gun", "gunner_armor", "sniper_gun", "sniper_armor", "thrower_gun", "thrower_armor",
         "tank_chassis", "jeep_gun", "jeep_armor",
         "artillery_armor", "artillery_chassis", "artillery_shell", "detonator", "wave_emitter"]
ARMY = ["soldier", "gunner", "sniper", "thrower",
        "base_tank", "jeep",
        "base_artillery", "artillery", "artillery_cassete", "artillery_emp", "artillery_antitank"]

STATISTIC = ["clan_pvp_tournament_play_item", "clan_pvp_tournament_win_item"]

DETAIL_INFO = ["rating", "honor", "infantry_reputation_item",
               "strength_item", "rate_lose_item", "rate_win_item",
               "universal_scheme_item", "event_scheme_item",
               "gold_overall_real", "gold_overall_spent"]

UNITS = {"soldier":             {"building": "infantry", "count": 3, "requirements": []},
         "gunner":              {"building": "infantry", "count": 2, "requirements": ["gunner_armor"]},
         "sniper":              {"building": "infantry", "count": 1, "requirements": ["sniper_armor", "sniper_gun"]},
         "thrower":             {"building": "infantry", "count": 1, "requirements": ["thrower_armor", "thrower_gun"]},

         "base_tank":           {"building": "armor",    "count": 1, "requirements": ["tank_chassis"]},
         "jeep":                {"building": "armor",    "count": 1, "requirements": ["jeep_armor", "jeep_gun"]},

         "base_artillery":      {"building": "support",  "count": 2, "requirements": ["artillery_chassis"]},
         "artillery":           {"building": "support",  "count": 1, "requirements": ["artillery_chassis", "artillery_shell", "artillery_armor"]},
         "artillery_cassete":   {"building": "support",  "count": 1, "requirements": ["detonator"]},
         "artillery_emp":       {"building": "support",  "count": 1, "requirements": ["wave_emitter"]},
         "artillery_antitank":  {"building": "support",  "count": 1, "requirements": ["artillery_chassis"]},
         }


ADDITIONAL = ["gold", "diamonds", "rating"]


ORDER_TEMPLATE = '<start_contract uid="%s" auth_key="%s" sid="%s">' \
                 '<contract>contract_%s_%s</contract>' \
                 '<building>%s</building>' \
                 '</start_contract>'

ITEM_TEMPLATE = '<start_contract uid="%s" auth_key="%s" sid="%s">' \
                '<building>%s</building>' \
                '<contract>contract_item_%s_%s</contract>' \
                '</start_contract>'

RESOURCE_TEMPLATE = '<execute uid="%s" auth_key="%s" sid="%s"><arguments/>' \
                    '<command>%s_factory_reset_script</command></execute>'

INTERACTION = {"daily": '<interaction uid="%s" auth_key="%s" sid="%s">'
                        '<type>gift_scheme</type>'
                        '<group>schemes_gift_interaction_group</group>'
                        '<friend>%s</friend>'
                        '</interaction>',
               "event": '<interaction uid="%s" auth_key="%s" sid="%s">'
                        '<type>event_scheme</type>'
                        '<group>schemes_event_interaction_group</group>'
                        '<friend>%s</friend>'
                        '</interaction>'}

PRESENT_TEMPLATE = '<execute uid="%s" auth_key="%s" sid="%s">' \
                   '<command>input_data_script</command>' \
                   '<arguments>' \
                   '<gift_type>daily%s_gift</gift_type>' \
                   '<gift_subtype>%s</gift_subtype>' \
                   '</arguments>' \
                   '</execute>'

PRESENTS = ["gold", "money", "marine", "food", "units", "fuel", "schemes", "commando"]

# STAT_USER = {"uid": "mr:17273545492366541080", "auth": "77fdcf629194f89ff767e79d6843cedf"}
STAT_USER = {"uid": "mr:16365741323372014699", "auth": "5914b4525bae999a2da5c1f60ced1ff2"}
FREEDOMS = ["25c139b2f8c2420a5c1130c6f9a6f3ce"]


def humanize_time(time):
    """
    Convert inputed time in seconds to hours, minutes and seconds format
    """
    minutes, seconds = divmod(int(time), 60)
    hours, minutes = divmod(int(minutes), 60)
    return hours, minutes, seconds


class Utils(object):
    """ Class for additional necessaries """

    def __init__(self):
        self.thread_list = []
        self.logger = logging.getLogger("CRISIS")
        hdlr = logging.FileHandler("/tmp/crisis.log")
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                                      datefmt="%d-%m-%Y %H:%M:%S")
        hdlr.setFormatter(formatter)
        self.logger.addHandler(hdlr)
        self.logger.setLevel(logging.INFO)
        self.stat_sid = None
        self.order_lock = False

    def watch_dog_runner(self):
        thread = Thread(target=self.watch_dog)
        thread.start()
        sleep(1)
        # self.thread_list.append(thread)

    def watch_dog(self):
        current = datetime.now()

        if (3 * 60 + 30) <= (int(current.hour) * 60 + int(current.minute)) < (15 * 60 + 30):
            start_point = 15
        else:
            start_point = 3

        # start_point = DAILY_HOUR
        remain_time = int(start_point - current.hour) * 60 * 60 + (DAILY_MINUTE - current.minute) * 60
        on_block = BLOCK_TIMEOUT
        if remain_time >= 0:
            timeout = remain_time
        elif abs(remain_time) < BLOCK_TIMEOUT:
            timeout = 0
            on_block = BLOCK_TIMEOUT + remain_time
        else:
            timeout = 24 * 60 * 60 + remain_time

        # print "Remain time: %s:%s" % (timeout/3600, timeout%3600)
        # print "On block time: %s:%s" % (on_block/3600, (on_block/60)%60)
        while True:
            sleep(timeout)
            self.order_lock = True
            sleep(on_block)
            self.order_lock = False
            timeout = 11 * 60 * 60 + 30 * 60
            # timeout = 23 * 60 * 60 + 30 * 60
            on_block = BLOCK_TIMEOUT

    def send_request(self, url, data):
        """ Send POST request """
        try:
            headers = {"Content-type": "application/x-www-form-urlencoded"}
            req = urllib2.Request(url, data, headers)
            response = urllib2.urlopen(req)
            # <error>101</error>
            return response.read()
        except Exception, err:
            # print "%s - Error during processing http request:\n<%s>" % (str(datetime.now()), err)
            self.logger.warning("Error during processing http request:\n<%s>" % err)
            sleep(10)
            return None

    def response_parse(self, uid=None, response=None):
        """ Parse response for get necessary user information """
        result = {}
        try:
            if response is not None:
                dom = parseString(str(response))
                try:
                    sid = dom.getElementsByTagName("user")[0].attributes["sid"].value
                    result.update({"sid": sid})
                except:
                    pass
                army_mask = ["card_%s_count_item" % unit for unit in ARMY]
                resource, parts, entity, current_army, detail_info, statistic = {}, {}, {}, {}, {}, {}
                for item in dom.getElementsByTagName("item"):
                    if item.attributes["type"].value in RESOURCES:
                        resource.update({item.attributes["type"].value: item.attributes["count"].value})
                    elif item.attributes["type"].value in ENTITY:
                        entity.update({item.attributes["type"].value: item.attributes["count"].value})
                    elif item.attributes["type"].value in PARTS:
                        parts.update({item.attributes["type"].value: item.attributes["count"].value})
                    elif item.attributes["type"].value in DETAIL_INFO:
                        detail_info.update({str(item.attributes["type"].value): item.attributes["count"].value})
                    elif item.attributes["type"].value in STATISTIC:
                        statistic.update({str(item.attributes["type"].value): item.attributes["count"].value})
                    elif item.attributes["type"].value in army_mask:
                        current_army.update({str(item.attributes["type"].value)[5:-11]:
                                            item.attributes["count"].value})

                result.update({"resource": resource,
                               "entity": entity,
                               "parts": parts,
                               "current_army": current_army,
                               "detail_info": detail_info,
                               "statistic": statistic})
                if uid:
                    for item in dom.getElementsByTagName("building"):
                        building_type = item.attributes["type"].value
                        if building_type in ["infantry_factory", "infantry_items_factory",
                                             "support_factory", "support_items_factory",
                                             "armor_factory", "armor_items_factory"]:
                            self.__setattr__("%s_%s" % (uid, building_type), item.attributes["id"].value)
        except Exception, err:
            self.logger.error("Error during response parsing: %s" % err)
            # print err
        finally:
            return result

    def get_participant_info(self, uid, auth, check_avail=True):
        """ Get user information from game """
        if check_avail and uid not in self.get_available():
            return False, "Sorry. Your UID isn't in available list"
        result = {"auth": auth, "uid": uid}
        try:
            data = '<get_friends_info uid="%s" auth_key="%s">' \
                   '<flags>0</flags>' \
                   '</get_friends_info>' % (uid, auth)
            response = self.send_request("%s/get_friends_info" % ENDPOINT, data)
            if "internal_error" in response:
                return False, "Wrong UID-AUTHKEY pair"
            else:
                friends = parseString(str(response)).getElementsByTagName("friends_info")[0].toxml()
                data = '<get_friends_status uid="%s" auth_key="%s">%s</get_friends_status>' % (uid, auth, friends)
                response = self.send_request("%s/get_friends_status" % ENDPOINT_DATA, data)
                friends_status = response
                data = '<get_game_info uid="%s" auth_key="%s"> <data> %s </data> </get_game_info>'\
                       % (uid, auth, friends_status)
                response = self.send_request("%s/get_game_info" % ENDPOINT, data)
                result.update(self.response_parse(uid, response))
                if uid != STAT_USER.get("uid"):
                    result.update({"username": self.get_user_name(uid)})
                result.update({"is_leader": self.is_clan_leader(uid, auth, result.get("sid"))})
                self.update_participant_params(uid, "AUTH", auth)
                return True, result
        except Exception, err:
            print err
            self.logger.error("Error during get information about user <%s>. %s" % (uid, err))
            return False, "Error during get information about user <%s>" % uid

    def get_user_information(self, uid):
        """ Get user information using Static User credentials """
        result = {"uid": uid}
        try:
            stat_uid, stat_auth = self.get_stat_user_info()
            info = self.get_participant_info(stat_uid, stat_auth)
            stat_sid = info[1]["sid"]
            data = '<get_user_info uid="%s" auth_key="%s" sid="%s"> <user>%s</user> </get_user_info>' \
                   % (stat_uid, stat_auth, stat_sid, uid)
            response = self.send_request("%s/get_user_info" % ENDPOINT, data)
            result.update(self.response_parse(response=response))
            result.update({"name": self.get_user_name(uid)})
        finally:
            return result

    def start_gather(self, uid, info):
        """
        {'username': '\xd0\x90\xd0\xbb\xd0\xb5\xd0\xba\xd1\x81\xd0\xb5\xd0\xb9 \xd0\x91\xd0\xbe\xd0\xb3\xd0\xbe\xd1\x81\xd0\xbb\xd0\xbe\xd0\xb2\xd1\x81\xd0\xba\xd0\xb8\xd0\xb9',
         'is_auth': True,
         'resource': {u'food': u'13500', u'fuel': u'1000', u'money': u'5000'},
         'uid': 'vk:2342994',
         'is_run': True,
         'start_time': 1430316488,
         'auth': '8bf09888459a49e3c9cee77ad304343e',
         'entity': {u'laser_aimer': u'803', u'tnt_charge': u'1393', u'rare_item': u'77', u'control_block': u'388', u'armor_composite': u'2599', u'armor_plate': u'2502', u'gun_receiver': u'1154', u'powder_charge': u'1263', u'kevlar_fiber': u'567'}, 'left_time': 7200,
         'parts': {u'thrower_armor': u'2', u'artillery_armor': u'14', u'jeep_gun': u'2', u'wave_emitter': u'3', u'sniper_armor': u'12', u'sniper_gun': u'54', u'artillery_shell': u'12', u'jeep_armor': u'2', u'detonator': u'1', u'tank_chassis': u'33', u'artillery_chassis': u'5', u'gunner_armor': u'4', u'gunner_gun': u'263', u'soldier_gun': u'262', u'thrower_gun': u'2'},
         'sid': u'fba37895e9f9decf5bf357cf32734ae7',
         'order': {'soldier': 1, 'thrower': 4, 'artillery': 8, 'gunner': 2, 'base_artillery': 7, 'jeep': 6, 'artillery_emp': 9, 'base_tank': 5, 'artillery_cassete': 0, 'sniper': 3}}
        """
        self.logger.info("Start ordering for user <%s>: " % uid)
        thread = Thread(name=uid, target=self.resource_unit_order, args=[uid, info, ])
        thread.start()
        sleep(1)
        self.thread_list.append(thread)

    def get_resources(self, uid, auth, sid):
        for resource in RESOURCES:
            response = self.send_request("%s/execute" % ENDPOINT, RESOURCE_TEMPLATE % (uid, auth, sid, resource))
            sleep(ADD_TIMEOUT)
            if "internal_error" in response:
                # self.logger.debug("Error during gather resources for user <%s>: %s" % (uid, response))
                raise Exception("Error during gather resources: %s" % response)

    def get_current_unit_order(self, uid):
        """ Return dict with current units ordering """
        order = {}
        for unit_type in ARMY:
            order.update({unit_type: getattr(self, "%s_%s" % (uid, unit_type), 0),
                          "%s_parts" % unit_type: getattr(self, "%s_%s_parts" % (uid, unit_type), False)})
        return order

    def order_units(self, uid, auth, sid, unit_type):
        # Information about current parts count
        parts = getattr(self, "%s_parts" % uid, {})

        # Get all previous orders if exist
        building_type = UNITS[unit_type]["building"]
        for building in ["%s_factory" % building_type, "%s_items_factory" % building_type]:
            get_order = '<collect_contract uid="%s" auth_key="%s" sid="%s">' \
                        '<slot>0</slot>' \
                        '<building>%s</building>' \
                        '</collect_contract>' % (uid, auth, sid, getattr(self, "%s_%s" % (uid, building)))
            response = ""
            i = 1
            while not "<internal_error>8a35a85ae4cd100c36a90fa421359ad3</internal_error>" in response and i < 5:
                response = self.send_request("%s/collect_contract" % ENDPOINT, get_order)
                if "Invalid sid" in response:
                    raise Exception("Invalid SID")
                if "_items_factory" in building:
                    for item in parseString(str(response)).getElementsByTagName("item_count_changed"):
                        if item.attributes["type"].value in PARTS:
                            parts.update({item.attributes["type"].value: item.attributes["count"].value})
                i += 1
                sleep(ADD_TIMEOUT)
        # Update information about parts after gather orders from buildings
        setattr(self, "%s_parts" % uid, parts)

        # Order unit
        response = self.send_request("%s/start_contract" % ENDPOINT,
                                     ORDER_TEMPLATE % (uid, auth, sid, "unit", unit_type,
                                                       getattr(self, "%s_%s_factory" % (uid, building_type))))
        if "Invalid sid" in response:
            raise Exception("Invalid SID")

        if "error" not in response:
            order_count = self.__getattribute__("%s_%s" % (uid, unit_type))
            self.__setattr__("%s_%s" % (uid, unit_type), int(order_count - int(UNITS[unit_type].get("count", 1))))
            for item in parseString(str(response)).getElementsByTagName("item_count_changed"):
                if item.attributes["type"].value in PARTS:
                    parts.update({item.attributes["type"].value: item.attributes["count"].value})
            # Update information about parts about gather after order unit
            setattr(self, "%s_parts" % uid, parts)

        # Order parts for unit if need
        require = UNITS[unit_type].get("requirements", [])
        # if require and self.__getattribute__("%s_%s_parts" % (uid, unit_type)):
        for item in require:
            if int(getattr(self, "%s_parts" % uid, {}).get(item, 0)) > 2:
                continue
            response = self.send_request("%s/start_contract" % ENDPOINT,
                                         ORDER_TEMPLATE % (uid, auth, sid, "item", item,
                                                           getattr(self, "%s_%s_items_factory" % (uid, building_type))))
            if "Invalid sid" in response:
                raise Exception("Invalid SID")

    def resource_unit_order(self, uid, info):
        self.__setattr__(uid, Event())
        for item in ARMY:
            self.__setattr__("%s_%s" % (uid, item), int(info["order"][item]))
            # self.__setattr__("%s_%s_parts" % (uid, item), bool(info["order"].get("%s_parts" % item)))
        self.__setattr__("%s_parts" % uid, info["parts"])
        self.__setattr__("%s_trade_time" % uid, 0)

        while not self.__getattribute__(uid).is_set():
            info.update({"parts": getattr(self, "%s_parts" % uid)})
            if self.order_lock:
                current = datetime.now()
                timeout = int(DAILY_MINUTE - current.minute) * 60
            else:
                try:
                    timeout = RESOURCE_TIMEOUT  # By default use resource gathering timeout (2 hour)
                    for item in ARMY:
                        order_count = self.__getattribute__("%s_%s" % (uid, item))
                        if order_count >= int(UNITS[item].get("count", 1)):

                            self.order_units(uid, info["auth"], info["sid"], item)
                            timeout = TIMEOUT  # If order units exist, then set timeout 1 minute
                        else:
                            self.__setattr__("%s_%s_parts" % (uid, item), False)
                    self.get_resources(uid, info["auth"], info["sid"])
                    # TODO add last trade time

                    if int(time()) - int(getattr(self, "%s_trade_time" % uid, 0)) > (4 * 60 * 60):  # More than 4 hours
                        self.buy_trade_products(uid, info["auth"], info["sid"])
                except Exception, err:
                    self.logger.debug("Error in main order function for user <%s>: %s" % (uid, err))
                    flag = False
                    tries = 1
                    while not flag:
                        flag, result = self.get_participant_info(uid, info["auth"])
                        if flag:
                            info.update(result)
                            order = {}
                            for item in ARMY:
                                order.update({item: self.__getattribute__("%s_%s" % (uid, item))})
                        else:
                            if tries < 5:
                                self.logger.debug("Try number: %s. %s" % (tries, result))
                                tries += 1
                                sleep(int(tries * 10))
                            else:
                                self.logger.debug("Cannot get information about user <%s> for a long time."
                                                  " Fall asleep for an 1 hour" % uid)
                                tries = 1
                                sleep(3600)
                    timeout = 0
            self.__setattr__("%s_expire" % uid, int(time()) + timeout)
            self.__getattribute__(uid).wait(timeout)

    def stop_gather(self, uid):
        self.logger.info("Stop ordering for user <%s>" % uid)
        self.__getattribute__(uid).set()
        for item in ARMY:
            self.__setattr__("%s_%s" % (uid, item), 0)
            self.__setattr__("%s_%s_parts" % (uid, item), False)
        sleep(1)

    def get_remaining_time(self, uid):
        """ Return time in seconds to next gathering """
        result = getattr(self, "%s_expire" % uid, int(time())) - int(time())
        if result < 0:
            result = 0
        h, m, s = humanize_time(result)
        # print "Wait time is %s:%s:%s" % (h, m, s)
        return "%02d:%02d:%02d" % (h, m, s)

    def get_stat_user_info(self):
        db = DB_API()
        uid = STAT_USER["uid"]
        try:
            res = db.get_data(table="PARTICIPANT", condition="UID='%s'" % uid)
            auth = res.get("AUTH", "")
            return uid, auth
        except Exception, err:
            self.logger.error("Error during update participant information:\n<%s>" % err)
        finally:
            db.connection.close()

    def get_top_clans(self, type_of="honor"):  # honor, rating, influence
        """ Get list of top clans depends in type: honor, rating or influence """
        result = []
        uid, auth = self.get_stat_user_info()
        if self.stat_sid is None:
            info = self.get_participant_info(uid, auth)
            self.stat_sid = info[1]["sid"]
        data = '<get_top_100_of_clans uid="%s" auth_key="%s" sid="%s"/>' % (uid, auth, self.stat_sid)
        response = self.send_request("%s/get_top_100_of_clans" % ENDPOINT, data)
        clans = parseString(str(parseString(str(response)).getElementsByTagName(type_of)[0].toxml()))
        for clan in clans.getElementsByTagName("clan"):
            clan_id = clan.attributes["id"].value
            data = '<get_clan_info uid="%s" auth_key="%s" sid="%s"><clan_id>%s</clan_id> </get_clan_info>' \
                   % (uid, auth, self.stat_sid, clan_id)
            response = self.send_request("%s/get_clan_info" % ENDPOINT, data)
            details = parseString(str(response))
            clan_name = details.getElementsByTagName("clan")[0].attributes["name"].value
            result.append({"clan_id": clan_id, "name": clan_name.decode('base64', 'strict')})
        return result

    def get_statistics(self):
        """ Get weekly clan statistic """
        result = []
        db = DB_API()
        try:
            res = db.get_data(table="STATISTICS", multiple=True, order="WEEK_CLAN_WIN DESC, WEEK_CLAN ASC, WEEK_RATING DESC")
            result = [{"uid": item.get("UID"),
                       "name": item.get("NAME"),
                       "week_clan_win": item.get("WEEK_CLAN_WIN"),
                       "week_clan": item.get("WEEK_CLAN"),
                       "week_rating": item.get("WEEK_RATING"),
                       "last_clan_win": item.get("LAST_CLAN_WIN"),
                       "last_clan": item.get("LAST_CLAN"),
                       "last_rating": item.get("LAST_RATING"),
                       "week_percentage": item.get("WEEK_PERCENTAGE"),
                       } for item in res]
        except Exception, err:
            self.logger.error("Error during get weekly clan statistic:\n<%s>" % err)
        finally:
            db.connection.close()
            return result

    def update_statistics(self):
        """ Update weekly clan statistic """
        saved_statistics = self.get_statistics()
        db = DB_API()
        try:
            for user in saved_statistics:
                uid = user.get("uid")
                current_statistic = self.get_user_information(uid)
                last_clan_win = int(current_statistic.get("statistic", {}).get("clan_pvp_tournament_win_item", 0))
                last_clan_play = int(current_statistic.get("statistic", {}).get("clan_pvp_tournament_play_item", 0))
                last_rating = int(current_statistic.get("detail_info", {}).get("rating", 0))
                week_clan_win = last_clan_win - int(user.get("last_clan_win"))
                week_clan_play = last_clan_play - int(user.get("last_clan"))
                week_rating = last_rating - int(user.get("last_rating"))
                # print user.get("name").encode('utf-8'), week_clan_win, week_clan_play, week_rating
                db.upsert_data(table="STATISTICS", data={"UID": uid,
                                                         "NAME": user.get("name").encode('utf-8'),
                                                         "LAST_CLAN_WIN": last_clan_win,
                                                         "LAST_CLAN": last_clan_play,
                                                         "LAST_RATING": last_rating,
                                                         "WEEK_CLAN_WIN": week_clan_win,
                                                         "WEEK_CLAN": week_clan_play,
                                                         "WEEK_RATING": week_rating,
                                                         "WEEK_PERCENTAGE": round(100 * float(week_clan_win) / week_clan_play , 2)})
        except Exception, err:
            print err
            self.logger.error("Error during update weekly clan statistic:\n<%s>" % err)
        finally:
            db.connection.close()

    def get_clan_participant(self, clan_id=FREEDOMS[0]):

        result = []
        uid, auth = self.get_stat_user_info()
        if self.stat_sid is None:
            info = self.get_participant_info(uid, auth)
            self.stat_sid = info[1]["sid"]
        data = '<get_clan_info uid="%s" auth_key="%s" sid="%s"><clan_id>%s</clan_id> </get_clan_info>' \
               % (uid, auth, self.stat_sid, clan_id)
        response = self.send_request("%s/get_clan_info" % ENDPOINT, data)
        dom = parseString(str(response))
        result.append({dom.getElementsByTagName("leader")[0].attributes["uid"].value:
                       int(dom.getElementsByTagName("leader")[0].attributes["rating"].value)})
        for participant in dom.getElementsByTagName("participant"):
            result.append({participant.attributes["uid"].value: int(participant.attributes["rating"].value)})
        return list(reversed(sorted(result, key=lambda part: part.values()[0])))

    def is_clan_leader(self, uid, auth, sid, clan_id=FREEDOMS[0]):
        data = '<get_clan_info uid="%s" auth_key="%s" sid="%s"><clan_id>%s</clan_id> </get_clan_info>' \
               % (uid, auth, sid, clan_id)
        response = self.send_request("%s/get_clan_info" % ENDPOINT, data)
        dom = parseString(str(response))
        leader_uid = dom.getElementsByTagName("leader")[0].attributes["uid"].value
        if str(leader_uid) == str(uid):
            return True

        return False

    def get_user_name(self, user_uid):
        try:
            db = DB_API()
            name = db.get_data("USERS", condition="UID='%s'" % user_uid).get("NAME", None)
        except:
            name = None
        finally:
            db.connection.close()
        if name is not None:
            return name
        else:
            uid, auth = self.get_stat_user_info()
            if self.stat_sid is None:
                info = self.get_participant_info(uid, auth)
                self.stat_sid = info[1]["sid"]
            data = '<get_user_profile uid="%s" auth_key="%s" sid="%s"> <uid>%s</uid> </get_user_profile>' \
                   % (uid, auth, self.stat_sid, user_uid)
            response = self.send_request("%s/get_user_profile" % ENDPOINT, data)

            dom = parseString(str(response))
            try:
                fname = dom.getElementsByTagName("first_name")[0].firstChild.nodeValue
                lname = dom.getElementsByTagName("last_name")[0].firstChild.nodeValue
                return " ".join([fname.decode('base64', 'strict'), lname.decode('base64', 'strict')])
            except Exception, err:
                return "Undefined Name"

    def update_users_clans(self, limit=100):
        """ Update information about clans and clan participants """
        db = DB_API()
        # db.create_tables()

        db.delete_data("USERS")
        db.delete_data("CLANS")
        # db.connection.commit()

        for clan in self.get_top_clans()[:limit]:
            db.upsert_data("CLANS", clan, commit=False)
            clan_id = clan.get("clan_id")
            for user in self.get_clan_participant(clan_id):
                db.upsert_data("USERS", {"uid": user.keys()[0],
                                         "name": self.get_user_name(user.keys()[0]),
                                         "clan_id": clan_id},
                               commit=False)
            db.connection.commit()
        db.connection.commit()
        db.connection.close()

    def update_participant(self, clans=FREEDOMS):
        """ Update information about clan participant """
        db = DB_API()
        try:
            current = []
            for clan_id in clans:
                current.extend([item.keys()[0] for item in self.get_clan_participant(clan_id)])  # Get clan participant from game


            saved = self.get_available("DYNAMIC")                                                # Get saved clan participant

            for item in list(set(saved) - set(current)):
                res = db.get_data(table="PARTICIPANT", condition="UID='%s' AND AUTH is not NULL" % item)
                if res.get("AUTH", "") != "":
                    db.upsert_data(table="ARCHIVE", data={"UID": item, "AUTH": res.get("AUTH", "")})
                try:
                    self.stop_gather(item)
                except:
                    pass

                db.delete_data(table="PARTICIPANT", condition="UID='%s'" % item)
                db.delete_data(table="STATISTICS", condition="UID='%s'" % item)

            for item in list(set(current) - set(saved)):
                self.add_participant(uid=item, ptype="DYNAMIC")
                # db.upsert_data(table="PARTICIPANT", data={"UID": item, "TYPE": "DYNAMIC"})

        except Exception, err:
            self.logger.error("Error during update clan participants:\n<%s>" % err)
        finally:
            db.connection.close()

    def add_participant(self, uid, auth=None, ptype="STATIC", daily="OFF"):
        """ Manual add clan participant """
        db = DB_API()
        try:
            db.upsert_data(table="PARTICIPANT", data={"UID": uid, "AUTH": auth, "TYPE": ptype, "DAILY_MERC": daily})
            info = self.get_user_information(uid)
            db.upsert_data(table="STATISTICS", data={"UID": uid,
                                                     "NAME": info.get("name"),
                                                     "LAST_RATING": int(info.get("detail_info", {}).get("rating", 0)),
                                                     "LAST_CLAN": int(info.get("statistic", {}).get("clan_pvp_tournament_play_item", 0)),
                                                     "LAST_CLAN_WIN": int(info.get("statistic", {}).get("clan_pvp_tournament_win_item", 0))})
        finally:
            db.connection.close()

    def get_available(self, part_type="all"):
        """ Return list of available users UIDs """
        result = []
        db = DB_API()
        try:
            condition = ""
            if part_type != "all":
                condition = "TYPE='%s'" % part_type
            res = db.get_data(table="PARTICIPANT", condition=condition, multiple=True)
            for item in res:
                result.append(item.get("UID"))
        finally:
            db.connection.close()
            return result

    def update_participant_params(self, uid, field, data):
        """  """
        db = DB_API()
        try:
            res = db.get_data(table="PARTICIPANT", condition="UID='%s'" % uid)
            res.update({field: data})
            db.upsert_data(table="PARTICIPANT", data=res)
        except Exception, err:
            self.logger.error("Error during update participant information:\n<%s>" % err)
        finally:
            db.connection.close()

    def get_trade_order(self, uid):
        """ Get current trade order for participant """
        result = {}
        db = DB_API()
        try:
            info = db.get_data(table="PARTICIPANT", condition="UID='%s'" % uid)
            order = info.get("TRADE_ORDER", '{}')
            result = loads(order)
            if not isinstance(result, dict):
                result = {}
        except Exception, err:
            self.logger.error("Error during get participant trade order:\n<%s>" % err)
        finally:
            db.connection.close()
            return result

    def buy_trade_products(self, uid, auth, sid):
        """ Buy products from trade house """
        try:
            order = self.get_trade_order(uid)
            products = []
            for entity, kinds in order.iteritems():
                for kind in kinds:
                    additional = ""
                    if str(kind) == "gold":
                        additional = "_real"
                    products.append(r"%s_pack_\d%s" % (str(entity), additional))

            combined = "(" + "$)|(".join(products) + "$)"

            data = '<get_user_info uid="%s" auth_key="%s" sid="%s"> <user>%s</user> </get_user_info>' % (uid, auth, sid, uid)
            response = self.send_request("%s/get_user_info" % ENDPOINT, data)
            if response is not None:
                if "Invalid sid" in response:
                    raise Exception("Invalid SID")
                dom = parseString(str(response))
                for item in dom.getElementsByTagName("item"):
                    if match(combined, item.attributes["type"].value):
                        for i in xrange(int(item.attributes["count"].value)):
                            data = '<execute uid="%s" auth_key="%s" sid="%s">' \
                                   '<arguments/>' \
                                   '<command>%s_buy_script</command>' \
                                   '</execute>' % (uid, auth, sid, item.attributes["type"].value)
                            result = self.send_request("%s/execute" % ENDPOINT, data)
                            if "Invalid sid" in result:
                                raise Exception("Invalid SID")
            setattr(self, "%s_trade_time" % uid, int(time()))
        except Exception, err:
            if "Invalid sid" in err:
                raise Exception("Invalid SID")
            else:
                self.logger.error("Error during buy products for user <%s>:\n<%s>" % (uid, err))

    def get_region_cities(self):
        """ Return dict where key = region, value = list of cities in current region """
        regions = {}
        cities = {}
        db = DB_API()
        try:
            res = db.get_data(table="CITY", multiple=True)
            for item in res:
                regions.update({item["REGION_ID"]: item["REGION"]})

                temp = cities.get(item["REGION_ID"], {})
                temp.update({item["ID"]: item["CITY_NAME"]})
                cities.update({item["REGION_ID"]: temp})
        except Exception, err:
            self.logger.error("Error during get region/city information: %s" % err)
        finally:
            return regions, cities

    def start_city_attack(self, uid, info):
        """
        """
        self.logger.info("Start city <%s> attack by user <%s>: " % (info["city_selected"], uid))
        auth = info.get("auth")
        sid = info.get("sid")
        region_id, city_id = info.get("selected_city", "_").split("_")

        thread = Thread(name=uid, target=self.city_attack, args=[uid, auth, sid, int(region_id), int(city_id), ])
        thread.start()
        sleep(1)
        self.thread_list.append(thread)

    def city_info_calldown(self, uid, auth, sid, city_id, region_id):
        """ Determine timeout to attack city """
        timeout = 0
        try:
            data = '<get_global_map uid="%s" auth_key="%s" sid="%s">' \
                   '<map>earth</map>' \
                   '</get_global_map>' % (uid, auth, sid)
            response = self.send_request("%s/get_global_map" % ENDPOINT, data)
            last_attack_time = 0
            details = parseString(str(response))
            for item in details.getElementsByTagName("city"):
                if item.attributes["type"].value == "region_%02d_city_%02d" % (region_id, city_id):
                    last_attack_time = int(item.attributes["last_attack_time"].value)
            timeout = int(24 * 60 * 60 - (int(time()) - last_attack_time))
        except Exception, err:
            self.logger.error("Error during get city attack calldown: %s" % err)
        finally:
            return timeout

    def city_attack(self, uid, auth, sid, region_id, city_id):
        """ Attack city """
        setattr(self, "%s_city" % uid, Event())

        # Get timeout to city
        timeout = (self.city_info_calldown(uid, auth, sid, city_id, region_id) - 30)
        getattr(self, "%s_city" % uid).wait(timeout)
        # sleep(timeout)

        data = '<global_map_attack uid="%s" auth_key="%s" sid="%s">' \
               '<city>region_%02d_city_%02d</city>' \
               '<map>earth</map>' \
               '<region>region_%02d</region>' \
               '</global_map_attack>' % (uid, auth, sid, region_id, city_id, region_id)
        counter = 0

        while not getattr(self, "%s_city" % uid).is_set():
            try:
                response = self.send_request("%s/global_map_attack" % ENDPOINT, data)
                if "Invalid sid" in response:
                    raise Exception("Invalid SID")
                elif "internal_error" not in response:
                    self.stop_city_attack(uid)
                counter += 1
                if counter % 150 == 0:
                    if self.city_info_calldown(uid, auth, sid, city_id, region_id) > 600:
                        self.stop_city_attack(uid)
                    else:
                        data = '<global_map_attack uid="%s" auth_key="%s" sid="%s">' \
                               '<city>region_%02d_city_%02d</city>' \
                               '<map>earth</map>' \
                               '<region>region_%02d</region>' \
                               '</global_map_attack>' % (uid, auth, sid, region_id, city_id, region_id)
                sleep(0.1)
            except Exception, err:
                self.logger.debug("Error in main order function for user <%s>: %s" % (uid, err))
                flag = False
                tries = 1
                while not flag:
                    flag, result = self.get_participant_info(uid, auth)
                    if flag:
                        sid = result.get("sid")
                    else:
                        if tries < 5:
                            self.logger.debug("Try number: %s. %s" % (tries, result))
                            tries += 1
                            sleep(int(tries * 10))
                        else:
                            self.logger.debug("Cannot get information about user <%s> for a long time."
                                              " Fall asleep for an 1 hour" % uid)
                            tries = 1
                            sleep(3600)

    def stop_city_attack(self, uid):
        """ Stop attack to city """
        getattr(self, "%s_city" % uid).set()
        sleep(1)

    def get_daily_params(self, uid):
        """ Get current mercenary for participant """
        merc, daily_schema, event_schema, group_plugin = None, None, None, None
        db = DB_API()
        try:
            info = db.get_data(table="PARTICIPANT", condition="UID='%s'" % uid)
            merc = info.get("DAILY_MERC", None)
            daily_schema = info.get("DAILY_SCHEMA", None)
            event_schema = info.get("EVENT_SCHEMA", None)
            group_plugin = info.get("GROUP_PLUGIN", None)
        except Exception, err:
            self.logger.error("Error during get participant params:\n<%s>" % err)
        finally:
            db.connection.close()
            return merc, daily_schema, event_schema, group_plugin

    def get_participants_present(self):
        db = DB_API()
        try:
            res = db.get_data(table="PARTICIPANT",
                              multiple=True,
                              condition="AUTH is not NULL and UPPER(DAILY_MERC) != 'OFF'")
            for user in res:
                uid = user["UID"]
                auth = user["AUTH"]
                merc = user["DAILY_MERC"]
                if merc == "random":
                    merc = choice(MERCS)
                self.get_game_daily(uid, auth, merc)
        except Exception, err:
            print "Error during get participant present: %s" % err
        finally:
            db.connection.close()

    def get_game_daily(self, uid, auth, merc, level=3):
        """ Get daily present (10 gold and mercenary) """
        print "===== Start Get Daily Game Present for user <%s> =====" % uid
        flag, info = self.get_participant_info(uid, auth)
        if not flag:
            print info
        else:
            sid = info.get("sid", "")
            update = '<update uid="%s" auth_key="%s" sid="%s"/>' % (uid, auth, sid)
            response = self.send_request("%s/update" % ENDPOINT, update)
            execute = '<execute uid="%s" auth_key="%s" sid="%s"><arguments/>' \
                      '<command>city_enter_script</command>' \
                      '</execute>' % (uid, auth, sid)
            response = self.send_request("%s/execute" % ENDPOINT, execute)
            DAILY = ['<execute uid="%s" auth_key="%s" sid="%s"> <arguments/>'
                     '<command>vip_tell_friends_script</command>'
                     '</execute>',

                     '<execute uid="%s" auth_key="%s" sid="%s">'
                     '<arguments> <count>1</count> </arguments>'
                     '<command>invite_count_script</command>'
                     '</execute>',

                     '<execute uid="%s" auth_key="%s" sid="%s">'
                     '<arguments/>'
                     '<command>vip_invites_complete_script</command>'
                     '</execute>',

                     '<execute uid="%s" auth_key="%s" sid="%s">'
                     '<command>vip_send_schemas_count_script</command>'
                     '<arguments> <count>10</count> </arguments>'
                     '</execute>',

                     '<execute uid="%s" auth_key="%s" sid="%s">'
                     '<arguments/>'
                     '<command>vip_send_schemas_complete_script</command>'
                     '</execute>']

            daily_order = '<execute uid="%s" auth_key="%s" sid="%s">' \
                          '<arguments/>' \
                          '<command>daily_quest_merc_us_%s_%s_executer_script</command>' \
                          '</execute>' % (uid, auth, sid, merc, level)
            response = self.send_request("%s/execute" % ENDPOINT, daily_order)

            for request in DAILY:
                response = self.send_request("%s/execute" % ENDPOINT, request % (uid, auth, sid))

            data1 = '<execute uid="%s" auth_key="%s" sid="%s">' \
                    '<command>daily_quest_merc_us_%s_%s_submit_script</command>' \
                    '<arguments/> </execute>' % (uid, auth, sid, merc, level)
            data2 = '<execute uid="%s" auth_key="%s" sid="%s">' \
                    '<command>daily_quest_merc_us_%s_%s_reward_quest_submit_script</command>' \
                    '<arguments/> </execute>' % (uid, auth, sid, merc, level)
            response = self.send_request("%s/execute" % ENDPOINT, data1)
            response = self.send_request("%s/execute" % ENDPOINT, data2)
            if "internal_error" in response:
                print response
            else:
                print "Success get %s" % merc

    def list_unique(self, incoming_list):
        output = []

        for item in incoming_list:
            if item not in output:
                output.append(item)
        return output

    def send_interactions(self):
        """ Send daily and event schemas for participants """
        db = DB_API()
        try:
            res = db.get_data(table="PARTICIPANT", multiple=True,
                              condition="DAILY_SCHEMA is not NULL or EVENT_SCHEMA is not NULL")

            senders = {}
            for net in NETS:
                add_recipient = [user["UID"] for user in db.get_data(table="ADD_RECIPIENTS",
                                                                     multiple=True,
                                                                     condition="UID like '%s%%'" % net)]

                locals()[net] = {"daily": add_recipient, "event": add_recipient}
                # locals()[net] = {"daily": add_recipient.get(net, []), "event": add_recipient.get(net, [])}

                db_sender = [{user["UID"]: user["AUTH"]}
                             for user in db.get_data(table="PARTICIPANT", multiple=True,
                                                     condition="AUTH is not NULL and UID like '%s%%'" % net)]

                archive_sender = [{user["UID"]: user["AUTH"]}
                                  for user in db.get_data(table="ARCHIVE", multiple=True,
                                                          condition="AUTH is not NULL and UID like '%s%%'" % net)]

                # file_sender = []
                # for item in getattr(additional_senders, net.upper()).split():
                #     if item.strip() == "":
                #         continue
                #     file_sender.append({(item.split(";")[0]).strip(): (item.split(";")[1]).strip()})

                senders.update({net: self.list_unique(db_sender + archive_sender)})

            for user in res:
                uid = user.get("UID")
                if uid.startswith("br"):
                    continue
                daily = user.get("DAILY_SCHEMA", None)
                if daily is not None:
                    temp = list(locals().get(uid[:2])["daily"])
                    temp.append(uid)
                    locals().get(uid[:2]).update({"daily": temp})

                event = user.get("EVENT_SCHEMA", None)
                if event is not None:
                    temp = list(locals().get(uid[:2])["event"])
                    temp.append(uid)
                    locals().get(uid[:2]).update({"event": temp})

            for net in NETS:
                if locals()[net].get("daily") or locals()[net].get("event"):
                    for sender_params in senders[net]:
                        sender_uid = sender_params.keys()[0]
                        sender_auth = sender_params.values()[0]

                        flag, info = self.get_participant_info(sender_uid, sender_auth, check_avail=False)
                        if not flag:
                            continue
                        try:
                            sid = info.get("sid")
                            for schema_type in ["daily", "event"]:
                                for recipient in locals()[net].get(schema_type):
                                    if sender_uid == recipient:
                                        continue
                                    # print "Send %s schema from %s to %s" % (schema_type, sender_uid, recipient)
                                    self.send_request("%s/interaction" % ENDPOINT,
                                                      INTERACTION[schema_type] % (sender_uid, sender_auth, sid, recipient))
                                    sleep(0.5)
                        except Exception, err:
                            print "Error during sending schemas from user <%s>: %s" % (sender_uid, err)
            print "Sending schemas finished"
        except Exception, err:
            print "Error during send interaction: %s" % err
        finally:
            db.connection.close()

    def get_group_plugin_present(self):
        """ Get daily present that publishing in official group and plugin """
        STEPS = {"GROUP":  {"start": 17, "step": 9},
                 "PLUGIN": {"start": 17, "step": 9}}
        # start 63, 17
        present = {}
        db = DB_API()
        try:
            res = db.get_data(table="PRESENT", multiple=True)
            for item in res:
                present_type = item["TYPE"]
                counter = int(item["COUNTER"])
                start_point = int(item["START_POINT"])
                first_step = int(item["FIRST_STEP"])

                present.update({present_type: int(start_point + counter * (first_step + counter - 1))})

                if counter == 7:
                    counter = 0
                    start_point += STEPS[present_type]["start"]
                    first_step += STEPS[present_type]["step"]
                else:
                    counter += 1

                db.upsert_data(table="PRESENT", data={"TYPE": present_type,
                                                      "COUNTER": counter,
                                                      "START_POINT": start_point,
                                                      "FIRST_STEP": first_step})
            res = db.get_data(table="PARTICIPANT",
                              multiple=True,
                              condition="AUTH is not NULL and GROUP_PLUGIN is not NULL")
            print "GROUP link: http://vk.com/war_crisis#gift_type=daily_gift&gift_subtype=%s" % present["GROUP"]
            print "PLUGIN link: http://vk.com/war_crisis#gift_type=daily_plugin_gift&gift_subtype=%s" % present["PLUGIN"]
            for user in res:
                self.get_present(user["UID"], user["AUTH"], present["GROUP"], present["PLUGIN"])
        except Exception, err:
            print "Error during get participant present: %s" % err
        finally:
            db.connection.close()

    def get_present(self, uid, auth, group=None, plugin=None):

        def present(present_id):
            try:
                response = self.send_request("%s/execute" % ENDPOINT,
                                             PRESENT_TEMPLATE % (uid, auth, sid, additional, present_id))

                dom = parseString(str(response))
                for item in dom.getElementsByTagName("item_count_changed"):
                    if item.attributes["type"].value == "daily_reward%s_item" % additional:
                        present_type = PRESENTS[int(item.attributes["count"].value) - 1]

                execute = '<execute uid="%s" auth_key="%s" sid="%s">' \
                          '<arguments/>' \
                          '<command>daily_reward%s_%s_submit_script</command>' \
                          '</execute>' % (uid, auth, sid, additional, present_type)
                response = self.send_request("%s/execute" % ENDPOINT, execute)
                if not "error" in response:
                    print "Success get %s %s" % (additional, present_type)
            except Exception, err:
                print "Error during get present <%s>: %s" % (additional, err)

        if group or plugin:
            print "===== Start Get Daily Present for user <%s> =====" % uid
            flag, info = self.get_participant_info(uid, auth)
            if not flag:
                print info
            else:
                sid = info.get("sid", "")

                if group:
                    additional = ""
                    present(group)

                if plugin:
                    additional = "_plugin"
                    present(plugin)


"""
INSERT INTO STATISTICS (UID, NAME, LAST_CLAN_WIN, LAST_CLAN, LAST_RATING, WEEK_CLAN_WIN, WEEK_CLAN, WEEK_RATING, WEEK_PERCENTAGE) VALUES
    ('vk:15453786', 'Ваня Патруц', 1023, 1671, 20818, 39, 62, 430, 62.90),
    ('vk:42083943', 'Тарас Жемелко', 639, 961, 30375, 24, 38, 979, 63.16),
    ('mr:672222039225022877', 'Константин Кабанов', 732, 1168, 18778, 43, 65, 541, 66.15),
    ('vk:215793727', 'Алексей Стуков', 957, 1538, 13230, 42, 59, 321, 71.19),
    ('br:39150', 'Олег Филипов', 346, 569, 14383, 18, 28, 646, 64.29),
    ('vk:65927701', 'Вадим Иванов', 563, 799, 15224, 19, 26, 350, 73.08),
    ('vk:3818838', 'Алексей Сибиряев', 390, 572, 12522, 5, 9, 560, 55.56),
    ('vk:1761241', 'Сергей Введенский', 642, 1017, 10423, 18, 27, 215, 66.67),
    ('vk:9630540', 'Ян Ярмолович', 443, 582, 7036, 20, 23, 228, 86.96),
    ('vk:226723848', 'Acc Gaming', 659, 985, 11440, 26, 41, 301, 63.41),
    ('od:81604620507', 'Сергей Харинский', 423, 718, 10829, 10, 16, 266, 62.50),
    ('od:519923501423', 'Евгений Мачехин', 388, 663, 9436, 13, 19, 267, 68.42),
    ('od:563216788409', 'Александр Васильев', 440, 759, 13074, 29, 58, 382, 50.00),
    ('mr:13725612745186471471', 'Евгений Федюшкин', 198, 303, 9138, 6, 10, 124, 60.00),
    ('od:560731711425', 'СЕРГЕЙ БОКОВОЙ', 534, 1200, 10038, 21, 38, 202, 55.26),
    ('od:573098935852', 'Алексей Соловьев', 397, 964, 6596, 16, 37, 224, 43.24),
    ('vk:8457405', 'Василий Воробьёв', 445, 660, 9243, 17, 24, 204, 70.83),
    ('vk:155076055', 'Madara In', 551, 859, 6207, 18, 24, 226, 75.00),
    ('vk:165361929', 'Станислав Саутин', 356, 569, 5080, 7, 14, 183, 50.00);
"""