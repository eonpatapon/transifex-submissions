"""
    Transifex submissions

    Git backend

    @copyright: 2011 by Jean-Philippe Braun <jpbraun@mandriva.com>
    @license: GNU GPL, see COPYING for details.
"""

import os
from base import BaseVCS

class GitVCS(BaseVCS):

    def checkout(self):
        if not os.path.exists(self.dest_dir):
            cmd = ["git", "clone", self.repo_url, self.dest_dir]
            super(GitVCS, self).checkout(cmd)

    def update(self):
        cmd = ["git", "pull", self.dest_dir]
        super(GitVCS, self).update(cmd)

    def commit(self, file):
        cmd1 = ["git", "commit", file, "-m", self.commit_msg ]
        cmd2 = ["git", "push"]
        super(GitVCS, self).commit(cmd1, cmd2)
