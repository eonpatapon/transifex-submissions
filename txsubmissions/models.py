import os, re
import codecs
from subprocess import check_output, CalledProcessError
from datetime import datetime

from django.conf import settings
from django.db import models
from django.db.models.signals import pre_save
from django.utils.translation import ugettext_lazy as _

from transifex.resources.models import Resource, SourceEntity, Translation
from transifex.languages.models import Language
from transifex.projects.models import Project

VCS_SUBMISSION_STATES = (
    ('new', 'new'),
    ('validated', 'validated'),
    ('commited', 'commited'),
    ('failed', 'failed')
)
VCS_BACKENDS = (
    ('Git', 'git'),
    ('Svn', 'svn')
)
VCS_CHECKOUT_DIR = "/home/eon/svn/soft/"

TX_USER = getattr(settings, 'SUBMISSIONS_TX_USER')
TX_PASS = getattr(settings, 'SUBMISSIONS_TX_PASS')
TX_HOST = getattr(settings, 'SUBMISSIONS_TX_HOST')
TX_VALIDATION = getattr(settings, 'SUBMISSIONS_TX_VALIDATION', False)
TX_ORGANIZATION = getattr(settings, 'SUBMISSIONS_TX_ORGANIZATION', '')
TX_HEADER_TPL = getattr(settings, 'SUBMISSIONS_TX_HEADER_TPL',
"""
#
# <project>
# <description>
# Copyright (C) <year> <organization>
# This file is distributed under the same license as the <project> package.
#
""")

class VCSProject(models.Model):
    """ Link a Transifex project to some VCS repo """
    tx_project = models.ForeignKey(Project, unique=True,
        help_text=_("Transifex project"),
        verbose_name=_("TX Project"))
    tx_source_language = models.ForeignKey(Language,
        help_text=_("The source language for this project"),
        verbose_name=_("TX Source language"))
    vcs_backend = models.CharField(max_length=10, choices=VCS_BACKENDS,
        help_text=_("Choose the VCS type"),
        verbose_name=_("VCS Backend"))
    vcs_url = models.CharField(max_length=255,
        help_text=_("RW checkout URL"),
        verbose_name=_("VCS URL"))
    vcs_checkout = models.CharField(max_length=255, default=VCS_CHECKOUT_DIR,
        help_text=_("Location of the project's checkout"),
        verbose_name=_("VCS Checkout"))
    vcs_header = models.TextField(default=TX_HEADER_TPL,
        blank=True, null=True,
        help_text=_("Header template for PO files"),
        verbose_name=_("VCS Header"))

    def __unicode__(self):
        return self.tx_project.name

    def destdir(self):
        """ Location of the project checkout """
        return os.path.join(self.vcs_checkout, self.tx_project.slug)

    def init_repo(self):
        """ Initialize the VCS backend """
        mod = __import__('txsubmissions.backend.vcs.%s' % \
            self.vcs_backend.lower(), globals(), locals(), ['%sVCS' % \
            self.vcs_backend])
        backend = getattr(mod, "%sVCS" % self.vcs_backend)
        self.repo = backend(self.vcs_checkout, self.tx_project.slug, self.vcs_url)

    def checkout(self):
        """ Checkout or update the project """
        if not getattr(self, 'repo', None):
            self.init_repo()
        self.repo.checkout()

    def commit(self, file):
        """ Commit file in the VCS """
        if not getattr(self, 'repo', None):
            self.init_repo()
        self.repo.commit(file)

    def init_client(self):
        """ Initialize Transifex client for VCS project """
        if not os.path.exists(os.path.join(self.destdir(), '.tx')):
            command = ['tx', 'init', '--host', TX_HOST, '--user', TX_USER,
                       '--pass', TX_PASS]
            print check_output(command, cwd=self.destdir())

    def init_client_resources(self):
        """ Initialize Transifex client resources """
        resources = VCSResource.objects.filter(vcs_project=self.pk)
        for resource in resources:
            command = ['tx', 'set', '--execute', '--auto-local', '-r',
                       '%s.%s' % (self.tx_project.slug, resource.tx_resource.slug),
                       '-s', self.tx_source_language.code,
                       '-f', resource.vcs_source_language_file,
                       u"%s" % resource.vcs_language_map ]
            print check_output(command, cwd=self.destdir())

    def get_header(self):
        """ Return a generated header for the project """
        header = self.vcs_header
        header = header.replace('<organization>', TX_ORGANIZATION)
        header = header.replace('<year>', datetime.now().strftime("%Y"))
        header = header.replace('<project>', self.tx_project.name)
        header = header.replace('<description>', self.tx_project.description)
        return header
    header = property(get_header)

    class Meta:
        verbose_name = _('VCS Project')


class VCSResource(models.Model):
    """ Map resources files to real files """
    tx_resource = models.ForeignKey(Resource, unique=True,
        verbose_name=_("TX Resource"))
    vcs_project = models.ForeignKey(VCSProject,
        verbose_name=_("VCS Project"))
    vcs_source_language_file = models.CharField(max_length=255,
        verbose_name=_("VCS Source language file"))
    vcs_language_map = models.CharField(max_length=255,
        verbose_name=_("VCS Language map"))

    def __unicode__(self):
        return u"%s" % self.tx_resource

    def pull(self, language):
        """ Pull resource file from Transifex in the selected language """
        command = ['tx', 'pull', '-f', '-r',
                   '%s.%s' % (self.vcs_project.tx_project.slug, self.tx_resource.slug),
                   '-l', language.code]
        print check_output(command, cwd=self.vcs_project.destdir())

    def commit(self, language):
        """ Commit the PO file in the VCS """
        # guess the file to commit
        language_file = self.vcs_language_map.replace('<lang>', language.code)
        language_file_path = os.path.join(self.vcs_project.destdir(), language_file)
        # get PO header
        header = self.vcs_project.header
        print header
        print unicode(header)
        # get translator history
        try:
            history = VCSHistory.objects.get(tx_resource=self.tx_resource, tx_language=language).vcs_history
        except VCSHistory.DoesNotExist:
            history = ""
        # read the po file contents and remove comments
        contents = u""
        for line in codecs.open(language_file_path, "r", "utf-8"):
            if not re.match("^#", line):
                contents = contents + line
        # add header and history
        contents = unicode(header) + "\n\n" + unicode(history) + "\n\n" + unicode(contents)
        # write the po file
        po_file = codecs.open(language_file_path, "w", "utf-8")
        po_file.write(contents)
        po_file.close()

        self.vcs_project.commit(language_file)

    class Meta:
        verbose_name = _('VCS Resource')


class VCSSubmission(models.Model):
    """ New translation to commit in VCS """
    tx_translation = models.ForeignKey(Translation,
        verbose_name=_("TX Translation"))
    tx_added = models.DateTimeField(auto_now=True, auto_now_add=True,
        verbose_name=_("Added"))
    old_string = models.TextField(null=True, blank=True,
        verbose_name=_("Old translation"))
    vcs_state = models.CharField(max_length=10, choices=VCS_SUBMISSION_STATES,
        default=VCS_SUBMISSION_STATES[0][0],
        verbose_name=_("VCS State"))
    vcs_last_action = models.DateTimeField(null=True, blank=True,
        verbose_name=_("VCS Action"))
    vcs_resource = models.ForeignKey(VCSResource,
        verbose_name=_("VCS Resource"))

    def tx_project(self):
        return self.tx_resource.project
    tx_project.short_description = _("TX Project")

    def tx_resource(self):
        return self.tx_translation.source_entity.resource
    tx_resource.short_description = _("TX Resource")

    def tx_language(self):
        return self.tx_translation.language
    tx_language.short_description = _("TX Language")

    def __unicode__(self):
        return u"%s (%s - %s)" % (self.vcs_resource, self.tx_translation, self.tx_added)

    class Meta:
        verbose_name = _('VCS Submission')
        permissions = (
            ("can_view", "Can see available submissions"),
        )


class VCSHistory(models.Model):
    """ Translator history """
    tx_resource = models.ForeignKey(Resource,
        verbose_name=_("TX Resource"))
    tx_language = models.ForeignKey(Language,
        verbose_name=_("TX Language"))
    vcs_history = models.TextField(verbose_name=_("VCS History"))

    def __unicode__(self):
        return u"History of %s for language %s" % (self.tx_resource, self.tx_language)

    class Meta:
        verbose_name=_("VCS History")
        verbose_name_plural=_("VCS History")


# Listen to new translations
def add_submission(sender, **kwargs):
    translation = kwargs['instance']
    try:
        # check if we need to queue this translation
        r = VCSResource.objects.get(tx_resource=translation.source_entity.resource)
        print "Adding new submission in queue."
        try:
            sub = VCSSubmission.objects.get(tx_translation=translation)
        except VCSSubmission.DoesNotExist:
            sub = VCSSubmission(tx_translation=translation, vcs_resource=r)
        # get the old string since model has not been saved yet
        sub.old_string = Translation.objects.get(pk=translation.pk).string
        sub.save()
    except VCSResource.DoesNotExist:
        # don't queue the translation
        pass
pre_save.connect(add_submission, sender=Translation)


def default_state():
    if TX_VALIDATION:
        return VCS_SUBMISSION_STATES[1][0]
    else:
        return VCS_SUBMISSION_STATES[0][0]
