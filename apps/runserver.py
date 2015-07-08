#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Purpose: Run CrisisBot on CherryPy WebServer
Created: 12.08.2014
Author: Aleksey Bogoslovskyi
"""
import os
import sys
import cherrypy
import django.core.handlers.wsgi as wsgi
from django.conf import settings

sys.path.append("/opt/RJ_Bots")


def main():
    """
    Start WebServer
    """
    daemon = cherrypy.process.plugins.Daemonizer(cherrypy.engine)
    daemon.subscribe()
    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
    app = wsgi.WSGIHandler()
    cherrypy.config.update(os.path.join("/opt/RJ_Bots/conf", 'bot.conf'))
    conf = {'/apps': {'tools.wsgiapp.on': True, 'tools.wsgiapp.app': app},
            '/static': {'tools.staticdir.on': True,
                        'tools.staticdir.dir': settings.STATIC_URL}}
    cherrypy.tree.graft(app, settings.SITE_HOME)
    cherrypy.engine.start()
    cherrypy.engine.block()

if __name__ == '__main__':
    main()
