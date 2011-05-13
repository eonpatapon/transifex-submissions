"""
    Transifex submissions

    Initialize new VCS project

    @copyright: 2011 by Jean-Philippe Braun <jpbraun@mandriva.com>
    @license: GNU GPL, see COPYING for details.
"""

import sys
import logging
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from txsubmissions.models import VCSProject

log = logging.getLogger('txsubmissions')

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('-p', '--project', dest='project',
            help='Initialize a new VCS project'),
        make_option('-l', '--list', action='store_true', dest='list',
            help='List available projects'),
    )

    def handle(self, *args, **options):

        if options['list']:
            print "Available projects :"
            for project in VCSProject.objects.all():
                print "- %s" % project
            sys.exit()

        if options['project']:
            try:
                project = VCSProject.objects.get(tx_project__slug=options['project'])
            except VCSProject.DoesNotExist:
                print "Unknow project"
                sys.exit(1)
            else:
                project.checkout()
                project.update()
                project.init_tx_client()
                project.init_tx_client_resources()
                print "Done"
