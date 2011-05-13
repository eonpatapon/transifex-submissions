"""
    Transifex submissions

    SVN backend

    @copyright: 2011 by Jean-Philippe Braun <jpbraun@mandriva.com>
    @license: GNU GPL, see COPYING for details.
"""

import os
from base import BaseVCS

class SvnVCS(BaseVCS):

    def checkout(self):
        if not os.path.exists(self.dest_dir):
            cmd = ["svn", "co", self.repo_url, self.dest_dir]
            super(SvnVCS, self).checkout(cmd)

    def update(self):
        cmd = ["svn", "up", self.dest_dir]
        super(SvnVCS, self).update(cmd)

    def commit(self, file):
        commit = ["svn", "ci", file, "-m", self.commit_msg ]
        super(SvnVCS, self).commit(commit)
