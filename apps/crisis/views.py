# Create your views here.
# -*- coding: utf-8 -*-

from json import dumps
from django.shortcuts import render_to_response
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.template import RequestContext
from django.conf import settings
from utils import Utils, MERCS, ENTITY, PARTS, ARMY, DETAIL_INFO

RUNNING_INFO = {}
TIMER = []


class Crisis_View():
    def __init__(self):
        self.utils = Utils()
        self.utils.watch_dog_runner()

    def is_exist(self, uid):
        if uid in RUNNING_INFO.keys():
            return True
        return False

    def login(self, request):
        """ Login """
        context = {}
        request.session['is_auth'] = False
        if request.method == "POST":
            if "connect" in request.POST:
                try:
                    uid = request.POST.get("uid", None)
                    auth = request.POST.get("auth", None)
                    if uid is not None:
                        uid = str(uid)
                    # uid = "vk:2342994"
                    # auth = "c0a426784e761547e57afcc6d2bbc367"
                    request.session['uid'] = uid
                    flag, data = self.utils.get_participant_info(uid, auth)
                    if flag:
                        request.session['is_auth'] = True
                        if uid.startswith("br"):
                            request.session['is_daily'] = False
                        else:
                            request.session['is_daily'] = True

                        request.session["is_leader"] = data.get("is_leader", False)

                        if uid not in RUNNING_INFO.keys():
                            data.update({"is_run": False, "is_attack": False})
                        else:
                            temp = RUNNING_INFO[uid]
                            temp.update(data)
                            data = temp

                        RUNNING_INFO.update({uid: data})
                        context.update(data)

                        return HttpResponseRedirect('order')
                    else:
                        context = {"error": True, "message": data}
                except Exception, err:
                    self.utils.logger.error(err.message)
                    if "Unable to create a new session key" in err.message:
                        context = {"error": True, "message": "Internal server Error. Please, contact administrator and try later..."}
                    else:
                        context = {"error": True, "message": "User select failed. Please, try again..."}

        return render_to_response("crisis/user_select.html",
                                  context,
                                  context_instance=RequestContext(request))

    def info(self, request):
        return HttpResponse("= %s =" % RUNNING_INFO)

    def order(self, request):
        """ Gather resources and order units """
        is_auth = request.session.get("is_auth", False)
        if not is_auth:
            return HttpResponseRedirect('/crisis')

        uid = request.session['uid']
        context = RUNNING_INFO.get(uid, {})
        context.update({"is_auth": is_auth,
                        "is_daily": request.session.get("is_daily", False),
                        "is_leader": request.session.get("is_leader", False),
                        "entity_list": ENTITY,
                        "parts_list": PARTS,
                        "detail_info_list": DETAIL_INFO})

        if "priority" not in context:
            priority = {}
            for item in ARMY:
                priority.update({item: 1})
            context.update({"priority": priority})

        if context.get("is_run", False):
            context.update({"left_time": self.utils.get_remaining_time(uid),
                            "order": self.utils.get_current_unit_order(uid)})
        """ Context Example
        context = {"username": self.utils.get_user_name(uid),
                   "is_run": False,
                   "is_auth": is_auth,
                   "resource": {"money": 100, "food": 200, "fuel": 300},
                   "entity":   {"armor_composite": 1, "armor_plate": 2, "control_block": 3,
                                "gun_receiver": 4, "kevlar_fiber": 5, "laser_aimer": 6,
                                "powder_charge": 7, "rare_item": 8, "tnt_charge": 9},
                   "parts":    {"artillery_armor": 1, "artillery_chassis": 2, "artillery_shell": 3, "detonator": 4,
                                "gunner_armor": 5, "gunner_gun": 6, "jeep_armor": 7, "jeep_gun": 8, "sniper_armor": 9,
                                "sniper_gun": 10, "soldier_gun": 11, "tank_chassis": 12, "thrower_armor": 13,
                                "thrower_gun": 14, "wave_emitter": 15},
                   'order':    {'soldier': 1, 'thrower': 4, 'artillery': 8, 'gunner': 2, 'base_artillery': 7, 'jeep': 6, 'artillery_emp': 9, 'base_tank': 5, 'artillery_cassete': 0, 'sniper': 3}
                  }
        """

        if request.method == "POST":
            if "start" in request.POST:
                order, priority = {}, {}
                data = dict(request.POST)

                for item in ARMY:
                    try:
                        count = int(data.get(item, [''])[0])
                    except:
                        count = 0
                    try:
                        prior = int(data.get("%s_priority" % item, [''])[0])
                    except:
                        prior = 1
                    order.update({item: count})
                    priority.update({item: prior})

                context.update({"is_run": True,
                                "order": order,
                                "priority": priority,
                                "left_time": self.utils.get_remaining_time(uid)})

                RUNNING_INFO.update({uid: context})
                self.utils.start_gather(uid, context)
            elif "stop" in request.POST:
                uid = request.session['uid']
                context = RUNNING_INFO.get(uid, {})
                context.update({"is_run": False, "left_time": "00:00:00"})
                RUNNING_INFO.update({uid: context})
                self.utils.stop_gather(uid)

        return render_to_response("crisis/order.html",
                                  context,
                                  context_instance=RequestContext(request))

    def daily(self, request):
        """ Set Daily Mercenary """
        is_auth = request.session.get("is_auth", False)
        is_daily = request.session.get("is_daily", False)
        if not is_auth or not is_daily:
            return HttpResponseRedirect('/crisis')
        uid = request.session.get("uid", None)

        params = self.utils.get_daily_params(uid)
        context = {"username": self.utils.get_user_name(uid),
                   "is_auth": is_auth,
                   "is_daily": is_daily,
                   "is_leader": request.session.get("is_leader", False),
                   "mercs": ["off"] + MERCS + ["random"],
                   "daily_merc": params[0],
                   "daily_schema": params[1],
                   "event_schema": params[2],
                   "group_plugin": params[3],
                   }

        if request.method == "POST":
            if "save" in request.POST:
                daily_merc = request.POST.get("daily_merc", None)
                self.utils.update_participant_params(uid, "DAILY_MERC", daily_merc)

                daily_schema = request.POST.get("daily_schema", None)
                self.utils.update_participant_params(uid, "DAILY_SCHEMA", daily_schema)

                event_schema = request.POST.get("event_schema", None)
                self.utils.update_participant_params(uid, "EVENT_SCHEMA", event_schema)

                group_plugin = request.POST.get("group_plugin", None)
                self.utils.update_participant_params(uid, "GROUP_PLUGIN", group_plugin)

                context.update({"daily_merc": daily_merc,
                                "daily_schema": daily_schema,
                                "event_schema": event_schema,
                                "group_plugin": group_plugin})
        return render_to_response("crisis/daily.html",
                                  context,
                                  context_instance=RequestContext(request))

    def trade(self, request):
        """ Buy entities at trade house  """
        is_auth = request.session.get("is_auth", False)
        is_daily = request.session.get("is_daily", False)
        if not is_auth or not is_daily:
            return HttpResponseRedirect('/crisis')
        uid = request.session.get("uid", None)

        entity_order = self.utils.get_trade_order(uid)
        context = {"username": self.utils.get_user_name(uid),
                   "is_auth": is_auth,
                   "is_daily": is_daily,
                   "is_leader": request.session.get("is_leader", False),
                   "slicer_list": [":4", "4:8", "8:"],
                   "entities": ["soldier_gun", "gunner_gun"] + ENTITY,
                   "entity_order": entity_order,
                   }

        if request.method == "POST":
            if "save" in request.POST:
                entity_order = {}
                for key, value in dict(request.POST).iteritems():
                    if "@money" in key or "@gold" in key:
                        entity, kind = key.split("@")

                        temp = list(entity_order.get(entity, []))
                        if kind not in temp:
                            temp.append(str(kind))

                        entity_order.update({entity: temp})

                context.update({"entity_order": entity_order})
                self.utils.update_participant_params(uid, "TRADE_ORDER", dumps(entity_order))
        return render_to_response("crisis/trade.html",
                                  context,
                                  context_instance=RequestContext(request))

    def city(self, request):
        """ Attack city """
        is_auth = request.session.get("is_auth", False)
        is_daily = request.session.get("is_daily", False)
        if not is_auth or not is_daily:
            return HttpResponseRedirect('/crisis')
        uid = request.session.get("uid", None)

        regions, cities = self.utils.get_region_cities()

        context = RUNNING_INFO.get(uid, {})
        context.update({"username": self.utils.get_user_name(uid),
                        "is_auth": is_auth,
                        "is_daily": is_daily,
                        "is_leader": request.session.get("is_leader", False),
                        "is_attack": context.get("is_attack", False),
                        "regions": regions,
                        "cities": cities
                        })
        if request.method == "POST":
            if "start" in request.POST:
                try:
                    context.update({"is_attack": True, "selected_city": request.POST.get("city")})
                    RUNNING_INFO.update({uid: context})
                    self.utils.start_city_attack(uid, context)
                except Exception, err:
                    self.utils.logger.error("Error during start city attack: %s" % err)
            elif "stop" in request.POST:
                try:
                    context.update({"is_attack": False})
                    self.utils.stop_city_attack(uid)
                except:
                    pass
        return render_to_response("crisis/city.html",
                                  context,
                                  context_instance=RequestContext(request))

    def statistics(self, request):
        """ Clan participants weekly statistics """
        context = {"uid": request.session.get("uid", None),
                   "is_auth": request.session.get("is_auth", False),
                   "is_daily": request.session.get("is_daily", False),
                   "is_leader": request.session.get("is_leader", False),
                   }

        context.update({"statistics": self.utils.get_statistics(),
                        "dates": self.utils.get_artefacts_dates()})
        return render_to_response("crisis/statistics.html",
                                  context,
                                  context_instance=RequestContext(request))

    def about(self, request):
        """ Information about developer """
        context = {"is_auth": request.session.get("is_auth", False),
                   "is_daily": request.session.get("is_daily", False),
                   "is_leader": request.session.get("is_leader", False),
                   "authors": settings.ADMINS}
        return render_to_response("crisis/about.html",
                                  context,
                                  context_instance=RequestContext(request))