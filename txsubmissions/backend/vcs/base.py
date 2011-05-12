"""
    Transifex submissions

    VCS base backend

    @copyright: 2011 by Jean-Philippe Braun <jpbraun@mandriva.com>
    @license: GNU GPL, see COPYING for details.
"""

import os
from subprocess import check_output, CalledProcessError

class BaseVCS(object):

    def __init__(self, base_dir, project_dir, repo_url):
        self.base_dir = base_dir
        self.dest_dir = os.path.join(self.base_dir, project_dir)
        self.repo_url = repo_url
        self.commit_msg = "Transifex update"

    def checkout(self, *commands):
        print "Checkout project in %s" % (self.dest_dir)
        for cmd in commands:
            self.call(cmd)

    def commit(self, *commands):
        print "Commit file..."
        for cmd in commands:
            self.call(cmd, cwd=self.destdir)

    def call(self, command):
        print "Running : %s" % command
        try:
            print check_output(command)
        except CalledProcessError:
            raise VCSError

class VCSError(Exception):
    pass
