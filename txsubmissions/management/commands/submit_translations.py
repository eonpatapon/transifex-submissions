"""
    Transifex submissions

    Submit new translation to VCS script

    @copyright: 2011 by Jean-Philippe Braun <jpbraun@mandriva.com>
    @license: GNU GPL, see COPYING for details.
"""

from django.core.management.base import BaseCommand, CommandError
from optparse import make_option

from txsubmissions.models import VCSSubmission, VCS_SUBMISSION_STATES, default_state

class Command(BaseCommand):
    args = '<state>'
    help = 'Submit in VCS all translations in the selected state (default: %s)' % \
        default_state()
    option_list = BaseCommand.option_list + (
        make_option('--state',
            action='store_true',
            dest='state',
            default=default_state(),
            help='Submit translations with the state'),
    )


    def handle(self, *args, **options):

        submissions = VCSSubmission.objects.filter(vcs_state=options['state']).order_by("-tx_added")

        to_submit = {}
        for submission in submissions:
            project = submission.vcs_resource.vcs_project
            language = submission.tx_language()
            resource = submission.vcs_resource

            if not project in to_submit:
                to_submit[project] = {}
            if not language in to_submit[project]:
                to_submit[project][language] = {}
            if not resource in to_submit[project][language]:
                to_submit[project][language][resource] = []
            to_submit[project][language][resource].append(submission)

        for project, details in to_submit.items():
            project.checkout()
            project.init_client()
            project.init_client_resources()
            for language, resources in details.items():
                for resource, submissions in resources.items():
                    resource.pull(language)
                    resource.commit(language, submissions)
                    for submission in submissions:
                        print "Set submission %s state as %s" % \
                            (submission, VCS_SUBMISSION_STATES[2][0])
                        submission.vcs_state = VCS_SUBMISSION_STATES[2][0]
                        submission.save()

