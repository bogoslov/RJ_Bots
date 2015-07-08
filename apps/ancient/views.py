# Create your views here.
# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.template import RequestContext
from django.conf import settings
from utils import Utils
from time import time


class Ancient_View():
    def __init__(self):
        self.utils = Utils()

    def main(self, request):
        context = {}
        if request.method == "POST":
            if "run" in request.POST:
                try:
                    uid = request.POST.get("uid", None)
                    auth = request.POST.get("auth", None)
                    sid = self.utils.get_sid(uid, auth)
                    response = self.utils.send_request('<start_defence_session sid="%s"> <type>arena_rotation_m4</type> </start_defence_session>' % sid)
                    if "error" in response:
                        context = {"error": True, "message": "Some error happened :("}
                except Exception, err:
                    context = {"error": True, "message": "Some unexpected error happened :("}
        return render_to_response("ancient/user_select.html",
                                  context,
                                  context_instance=RequestContext(request))

    def about(self, request):
        context = {"authors": settings.ADMINS}
        return render_to_response("ancient/about.html",
                                  context,
                                  context_instance=RequestContext(request))
