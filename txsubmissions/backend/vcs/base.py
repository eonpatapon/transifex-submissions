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
        print "Commit file"
        for cmd in commands:
            print cmd
            #self.call(cmd)

    def call(self, command):
        print "Running : %s" % command
        try:
            print check_output(command)
        except CalledProcessError:
            raise VCSError

class VCSError(Exception):
    pass
