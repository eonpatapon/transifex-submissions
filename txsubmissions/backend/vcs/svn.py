import os

from base import BaseVCS

class SvnVCS(BaseVCS):

    def checkout(self):
        if os.path.exists(self.dest_dir):
            command = ["svn", "up", self.dest_dir]
        else:
            command = ["svn", "co", self.repo_url, self.dest_dir]
        super(SvnVCS, self).checkout(command)

    def commit(self, file):
        command = ["svn", "ci", file, "-m", self.commit_msg ]
        super(SvnVCS, self).commit(command)
