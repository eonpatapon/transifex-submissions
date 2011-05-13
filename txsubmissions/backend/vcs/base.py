"""
    Transifex submissions

    VCS base backend

    @copyright: 2011 by Jean-Philippe Braun <jpbraun@mandriva.com>
    @license: GNU GPL, see COPYING for details.
"""

import os
import logging

from txsubmissions.utils import RunError, run

log = logging.getLogger('txsubmissions')

class BaseVCS(object):

    def __init__(self, base_dir, project_dir, repo_url):
        self.base_dir = base_dir
        self.dest_dir = os.path.join(self.base_dir, project_dir)
        self.repo_url = repo_url
        self.commit_msg = "Transifex update"

    def checkout(self, *commands):
        log.info("Checkout project in %s" % (self.dest_dir))
        for cmd in commands:
            run(cmd)

    def update(self, *commands):
        log.info("Updating repo %s" % (self.dest_dir))
        for cmd in commands:
            run(cmd)

    def commit(self, *commands):
        log.info("Commit files")
        for cmd in commands:
            kwargs = {'cwd': self.dest_dir}
            try:
                run(cmd, **kwargs)
            except RunError, err:
                log.error(err)


class VCSError(Exception):
    pass
