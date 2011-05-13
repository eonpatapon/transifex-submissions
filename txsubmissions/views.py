"""
    Transifex submissions

    Views

    @copyright: 2011 by Jean-Philippe Braun <jpbraun@mandriva.com>
    @license: GNU GPL, see COPYING for details.
"""

from sets import Set

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseBadRequest, HttpResponse
from django.contrib.auth.decorators import permission_required
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from txsubmissions.models import VCSSubmission, VALIDATION, VCS_SUBMISSION_STATES
from txsubmissions.forms import SubmissionsForm
from transifex.languages.models import LanguageManager

@permission_required('txsubmissions.can_view', login_url='/')
def submissions(request):

    q = VCSSubmission.objects.order_by("-tx_added")

    projects = Set([ s.vcs_resource.vcs_project for s in q ])
    resources = Set([ s.vcs_resource for s in q ])
    translators = Set([ s.tx_translation.user for s in q ])

    if not request.GET:
        data = {'project': 'all', 'resource': 'all', 'translator': 'all', 'state': VCS_SUBMISSION_STATES[0][0]}
    else:
        data = request.GET
    form = SubmissionsForm(data)
    form.fields['project'].choices = [('all', _('All projects'))] + [ (p.tx_project.slug, p) for p in projects ]
    form.fields['resource'].choices = [('all', _('All resources'))] + [ (r.tx_resource.slug, r) for r in resources ]
    form.fields['translator'].choices = [('all', _('All translators'))] + [ (t, t) for t in translators ]
    if form.is_valid():
        data = form.cleaned_data
        if 'project' in data and data['project'] != 'all':
            q = q.filter(vcs_resource__vcs_project__tx_project__slug=data['project'])
        if 'resource' in data and data['resource'] != 'all':
            q = q.filter(vcs_resource__tx_resource__slug=data['resource'])
        if 'translator' in data and data['translator'] != 'all':
            q = q.filter(tx_translation__user__username=data['translator'])
        q = q.filter(vcs_state=data['state'])

    submissions = q

    return render_to_response('submissions.html',
        {'form': form,
         'submissions': submissions,
         'validation': VALIDATION},
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

