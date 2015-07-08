#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Purpose: 
Created: 25.12.2013
Author : Aleksey Bogoslovskyi
"""

import urllib2

from time import sleep
from re import match, compile
from datetime import datetime
from xml.dom.minidom import parseString


URL = "http://game-r01vk.rjgplay.com/command/"
PARSE = [ur".*in_login:(?P<LOGIN>\d+)-share:(?P<TYPE>.*)",
         ur".*share:(?P<TYPE>.*?)-in_login:(?P<LOGIN>\d+)"]



class Utils(object):
    def send_request(self, data):
        """ Send POST request """
        try:
            headers = {"Content-type": "application/x-www-form-urlencoded"}
            req = urllib2.Request(URL, data, headers)
            response = urllib2.urlopen(req)
            # <error>101</error>
            return response.read()
        except Exception, err:
            print "%s - Error during processing http request:\n<%s>" % (str(datetime.now()), err)
            # self.logger.warning("Error during processing http request:\n<%s>" % err)
            sleep(300)
            return None

    def get_sid(self, uid, auth_key):
        """ Get customer SID by uid and auth_key """
        try:
            data = "<auth><login>%s</login><auth_key>%s</auth_key></auth>" % (uid, auth_key)
            response = self.send_request(data)
            return response.split("sid")[1].strip(">").strip("</")
        except Exception, err:
            return None