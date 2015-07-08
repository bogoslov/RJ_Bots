from django.conf.urls import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from views import Crisis_View

crisis = Crisis_View()

urlpatterns = patterns('crisis.views',
                       (r"^order/$", crisis.order),
                       (r"^daily/$", crisis.daily),
                       (r"^trade/$", crisis.trade),
                       (r"^city/$", crisis.city),
                       (r"^statistics/$", crisis.statistics),
                       (r"^about/$", crisis.about),
                       (r"^$", crisis.login),
                       # (r"^info/$", crisis.info),
                       # (r"^(?P<username>\w+)/$", crisis.user_info),
                       # (r"^(?P<username>\w+)/auth_key/$", crisis.change_auth_key),
                       )

urlpatterns += staticfiles_urlpatterns()
