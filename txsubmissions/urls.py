from django.conf.urls.defaults import *

urlpatterns = patterns('txsubmissions.views',
    url(r'^$', 'submissions', name="submissions"),
    url(r'^validate/(?P<pk>[\d]+)/$', 'validate', name="validate_submission"),
)

