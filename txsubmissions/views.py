"""
    Transifex submissions

    Views

    @copyright: 2011 by Jean-Philippe Braun <jpbraun@mandriva.com>
    @license: GNU GPL, see COPYING for details.
"""

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseBadRequest, HttpResponse
from django.contrib.auth.decorators import permission_required
from django.db.models import Q

from txsubmissions.models import VCSSubmission, TX_VALIDATION
from transifex.languages.models import LanguageManager

@permission_required('txsubmissions.can_view', login_url='/')
def submissions(request):

    submissions = VCSSubmission.objects.order_by("-tx_added")

    return render_to_response('submissions.html',
        {'submissions': submissions, 'validation': TX_VALIDATION},
        context_instance=RequestContext(request))

@permission_required('txsubmissions.change_vcssubmission', login_url='/')
def validate(request, pk):
    try:
        s = VCSSubmission.objects.get(pk=pk)
        s.vcs_state = "validated"
        s.save()
        return HttpResponse("OK")
    except Exception, err:
        return HttpResponseBadRequest(err)

