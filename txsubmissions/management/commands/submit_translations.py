"""
    Transifex submissions

    Submit new translation to VCS script

    @copyright: 2011 by Jean-Philippe Braun <jpbraun@mandriva.com>
    @license: GNU GPL, see COPYING for details.
"""

import logging
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from txsubmissions.models import VCSSubmission, VCS_SUBMISSION_STATES, default_state, VALIDATION

log = logging.getLogger('txsubmissions')

class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--state', dest='state', default=default_state(),
            help='Submit in VCS all translations in the selected state (default: %s)' % default_state()
        ),
    )

    def handle(self, *args, **options):

        submissions = VCSSubmission.objects.filter(vcs_state=options['state']).order_by("-tx_added")

        if VALIDATION:
            # get also submissions that have 'new' status
            submissions = submissions | VCSSubmission.objects.filter(vcs_state=VCS_SUBMISSION_STATES[0][0])
            # get resources where all submissions are not validated
            not_validated = []
            for submission in submissions:
                if submission.vcs_state == VCS_SUBMISSION_STATES[0][0]:

                    not_validated.append(submission.vcs_resource)

        # order submissions
        # [project][language][resource][submissions]
        to_submit = {}
        for submission in submissions:
            project = submission.vcs_resource.vcs_project
            language = submission.tx_language
            resource = submission.vcs_resource

            if VALIDATION and not resource in not_validated:
                if not project in to_submit:
                    to_submit[project] = {}
                if not language in to_submit[project]:
                    to_submit[project][language] = {}
                if not resource in to_submit[project][language]:
                    to_submit[project][language][resource] = []
                to_submit[project][language][resource].append(submission)
            else:
                log.info("%s will not be submitted. Still submissions to validate." % resource)

        # submit ressources
        for project, details in to_submit.items():
            project.update()
            for language, resources in details.items():
                for resource, submissions in resources.items():
                    resource.pull(language)
                    resource.commit(language, submissions)
                    for submission in submissions:
                        log.debug("Set submission %s state as %s" % \
                            (submission, VCS_SUBMISSION_STATES[2][0]))
                        submission.vcs_state = VCS_SUBMISSION_STATES[2][0]
                        submission.save()
