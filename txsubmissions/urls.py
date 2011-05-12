"""
    Transifex submissions

    Urls

    @copyright: 2011 by Jean-Philippe Braun <jpbraun@mandriva.com>
    @license: GNU GPL, see COPYING for details.
"""

from django.conf.urls.defaults import *

urlpatterns = patterns('txsubmissions.views',
    url(r'^$', 'submissions', name="submissions"),
    url(r'^validate/(?P<pk>[\d]+)/$', 'validate', name="validate_submission"),
)

