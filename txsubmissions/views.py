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
    """ Main view - Manage and view submissions """

    q = VCSSubmission.objects.order_by("-tx_added")

    # init form choices lists base on the submissions lists
    languages = [('all', _('All languages'))] + \
        list(Set([ (s.tx_language.code, s.tx_language) for s in q ]))
    projects = [('all', _('All projects'))] + \
        list(Set([ (s.tx_project.slug, s.tx_project) for s in q ]))
    resources = [('all', _('All resources'))] + \
        list(Set([ (s.tx_resource.slug, s.tx_resource) for s in q ]))
    translators = [('all', _('All translators'))] + \
        list(Set([ (s.tx_translator.username, s.tx_translator) for s in q ]))

    if not request.GET:
        # send some default values to the form
        data = {'language': 'all', 'project': 'all', 'resource': 'all',
            'translator': 'all', 'state': VCS_SUBMISSION_STATES[0][0]}
    else:
        # send GET values to the form
        data = request.GET

    form = SubmissionsForm(data, languages, projects, resources, translators, VCS_SUBMISSION_STATES)
    # validate form
    if form.is_valid():
        data = form.cleaned_data
        # filter the query
        if 'project' in data and data['project'] != 'all':
            q = q.filter(vcs_resource__vcs_project__tx_project__slug=data['project'])
        if 'resource' in data and data['resource'] != 'all':
            q = q.filter(vcs_resource__tx_resource__slug=data['resource'])
        if 'translator' in data and data['translator'] != 'all':
            q = q.filter(tx_translation__user__username=data['translator'])
        if 'language' in data and data['language'] != 'all':
            q = q.filter(tx_translation__language__code=data['language'])
        q = q.filter(vcs_state=data['state'])

    submissions = q

    return render_to_response('submissions.html',
        {'form': form,
         'submissions': submissions,
         'validation': VALIDATION},
        context_instance=RequestContext(request))

@permission_required('txsubmissions.change_vcssubmission', login_url='/')
def validate(request, pk):
    """ Ajax view that validates one submission """
    try:
        s = VCSSubmission.objects.get(pk=pk)
        s.vcs_state = VCS_SUBMISSION_STATES[1][0]
        s.save()
        return HttpResponse("OK")
    except Exception, err:
        return HttpResponseBadRequest(err)

