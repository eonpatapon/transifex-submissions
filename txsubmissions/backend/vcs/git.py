import os

from base import BaseVCS

class GitVCS(BaseVCS):

    def checkout(self):
        if os.path.exists(self.dest_dir):
            command = ["git", "pull", self.dest_dir]
        else:
            command = ["git", "clone", self.repo_url, self.dest_dir]
        super(GitVCS, self).checkout(command)

    def commit(self, file):
        commit = ["git", "commit", file, "-m", self.commit_msg ]
        push = ["git", "push"]
        super(GitVCS, self).commit(commit, push)
