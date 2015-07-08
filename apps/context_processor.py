#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Purpose: Allows to use users setting variables in templates
Created: 27.04.2014
Author: Aleksey Bogoslovskyi
"""
from django.conf import settings


def django_settings(request):
    return {"settings": settings}
