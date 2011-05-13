#!/usr/bin/env python
#-*- coding:utf-8 -*-

from subprocess import Popen, PIPE
import logging

log = logging.getLogger('txsubmissions')


def run(cmd, **kwargs):
        log.debug("Running : %s" % " ".join(cmd))
        p = Popen(cmd, stderr=PIPE, stdout=PIPE, **kwargs)
        p.wait()
        if not p.returncode == 0:
            raise RunError(p.communicate())


class RunError(Exception):

    def __init__(self, msg):
        if type(msg) in (type(tuple()), type(list())):
            self.msg = "\n".join(msg)
        elif type(msg) == type(str()):
            self.msg = msg
        else:
            self.msg = str(msg)

    def __str__(self):
        return "\n"+self.msg
