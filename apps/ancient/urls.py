from django.conf.urls import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from views import Ancient_View

ancient = Ancient_View()

urlpatterns = patterns('ancient.views',
                       (r"^about/$", ancient.about),
                       (r"^$", ancient.main),
                       # (r"^info/$", crisis.info),
                       # (r"^(?P<username>\w+)/$", crisis.user_info),
                       # (r"^(?P<username>\w+)/auth_key/$", crisis.change_auth_key),
                       )

urlpatterns += staticfiles_urlpatterns()
