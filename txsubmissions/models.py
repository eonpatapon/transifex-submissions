"""
    Transifex submissions

    The database models

    @copyright: 2011 by Jean-Philippe Braun <jpbraun@mandriva.com>
    @license: GNU GPL, see COPYING for details.
"""


import os, re
import codecs
from subprocess import check_output, CalledProcessError
from datetime import datetime
from sets import Set
import logging

from django.conf import settings
from django.db import models
from django.db.models.signals import pre_save
from django.utils.translation import ugettext_lazy as _

from transifex.resources.models import Resource, SourceEntity, Translation
from transifex.languages.models import Language
from transifex.projects.models import Project

from txsubmissions.utils import RunError, run

VCS_SUBMISSION_STATES = (
    ('new', _('New')),
    ('validated', _('Validated')),
    ('commited', _('Submited to VCS')),
    ('failed', _('Failed'))
)
VCS_BACKENDS = (
    ('git', 'Git'),
    ('svn', 'Svn')
)

VCS_CHECKOUT_DIR = getattr(settings, 'SUBMISSIONS_VCS_CHECKOUT_DIR')
TX_USER = getattr(settings, 'SUBMISSIONS_TX_USER')
TX_PASS = getattr(settings, 'SUBMISSIONS_TX_PASS')
TX_HOST = getattr(settings, 'SUBMISSIONS_TX_HOST')
VALIDATION = getattr(settings, 'SUBMISSIONS_VALIDATION', False)
ORGANIZATION = getattr(settings, 'SUBMISSIONS_ORGANIZATION', '')
HEADER_TPL = getattr(settings, 'SUBMISSIONS_HEADER_TPL',
"""
#
# <project>
# <description>
# Copyright (C) <year> <organization>
# This file is distributed under the same license as the <project> package.
#
""")

log = logging.getLogger('txsubmissions')

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
    vcs_checkout = models.CharField(max_length=255,
        default=VCS_CHECKOUT_DIR,
        help_text=_("The project will be checkout in this directory in its own directory."),
        verbose_name=_("VCS Checkout"))
    vcs_header = models.TextField(default=HEADER_TPL,
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
            self.vcs_backend.lower().capitalize()])
        backend = getattr(mod, "%sVCS" % self.vcs_backend.lower().capitalize())
        self.repo = backend(self.vcs_checkout, self.tx_project.slug, self.vcs_url)

    def checkout(self):
        """ Checkout localy the project """
        if not getattr(self, 'repo', None):
            self.init_repo()
        self.repo.checkout()

    def update(self):
        """ Update the local checkout """
        if not getattr(self, 'repo', None):
            self.init_repo()
        self.repo.update()

    def commit(self, file):
        """ Commit file in the VCS """
        if not getattr(self, 'repo', None):
            self.init_repo()
        self.repo.commit(file)

    def init_tx_client(self):
        """ Initialize Transifex client for VCS project """
        if not os.path.exists(os.path.join(self.destdir(), '.tx', 'config')):
            command = ['tx', 'init', '--host', TX_HOST, '--user', TX_USER,
                       '--pass', TX_PASS]
            run(command, **{'cwd': self.destdir()})

    def init_tx_client_resources(self):
        """ Initialize Transifex client resources """
        resources = VCSResource.objects.filter(vcs_project=self.pk)
        for resource in resources:
            command = ['tx', 'set', '--execute', '--auto-local', '-r',
                       '%s.%s' % (self.tx_project.slug, resource.tx_resource.slug),
                       '-s', self.tx_source_language.code,
                       '-f', resource.vcs_source_language_file,
                       u"%s" % resource.vcs_language_map ]
            run(command, **{'cwd': self.destdir()})

    def get_header(self):
        """ Return a generated header for the project """
        header = self.vcs_header
        header = header.replace('<organization>', ORGANIZATION)
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
        run(command, **{'cwd': self.vcs_project.destdir()})

    def commit(self, language, submissions):
        """ Commit the PO file in the VCS """
        # guess the file to commit
        language_file = self.vcs_language_map.replace('<lang>', language.code)
        language_file_path = os.path.join(self.vcs_project.destdir(), language_file)
        # get PO header
        header = self.vcs_project.header
        # try update translator history if there is any
        try:
            vcs_history = VCSHistory.objects.get(tx_resource=self.tx_resource, tx_language=language)
            vcs_history.update(Set([ s.tx_translation.user for s in submissions ]))
            history = vcs_history.vcs_history
        except VCSHistory.DoesNotExist:
            history = ""
        # read the po file contents and remove comments
        contents = u""
        for line in codecs.open(language_file_path, "r", "utf-8"):
            if not re.match("^#", line):
                contents = contents + line
        # add header and history
        contents = unicode(header) + "#\n" + unicode(history) + "\n\n" + unicode(contents)
        # write the po file
        po_file = codecs.open(language_file_path, "w", "utf-8")
        po_file.write(contents.replace("\r\n", "\n"))
        po_file.close()
        # commit the po file
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

    def get_tx_project(self):
        return self.tx_resource.project
    get_tx_project.short_description = _("TX Project")
    tx_project = property(get_tx_project)

    def get_tx_resource(self):
        return self.tx_translation.source_entity.resource
    get_tx_resource.short_description = _("TX Resource")
    tx_resource = property(get_tx_resource)

    def get_tx_language(self):
        return self.tx_translation.language
    get_tx_language.short_description = _("TX Language")
    tx_language = property(get_tx_language)

    def get_tx_translator(self):
        return self.tx_translation.user
    get_tx_translator.short_description = _("TX Translator")
    tx_translator = property(get_tx_translator)

    def vcs_state_name(self):
        for state, state_name in VCS_SUBMISSION_STATES:
            if self.vcs_state == state:
                return state_name

    def __unicode__(self):
        return u"%s (%s - %s)" % (self.vcs_resource, self.tx_translation, self.tx_added)

    class Meta:
        verbose_name = _('VCS Submission')
        permissions = (
            ("can_view", _("Can see available submissions")),
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

    def update(self, translators):
        """ Update the translator history """
        current_year = datetime.now().strftime("%Y")
        current_history = self.vcs_history.split("\n")
        for translator in translators:
            exists = False
            add_year = False
            # loop over a copy because we might add elements
            for index, line in enumerate(current_history[:]):
                # check if the translator is in the history
                if re.search(translator.email, line):
                    exists = True
                    # update the year list if needed
                    if not re.search(current_year, line):
                        current_history[index] += ", %s" % current_year
                    break
            # add a new translator
            if not exists:
                current_history.append("# %s %s <%s>, %s" % (translator.first_name,
                    translator.last_name, translator.email, current_year))
        # save the new history
        self.vcs_history = "\n".join(current_history)
        self.save()

    class Meta:
        verbose_name=_("VCS History")
        verbose_name_plural=_("VCS History")


# Listen to new translations
def add_submission(sender, **kwargs):
    """ Add new translations made on Transifex
        to the VCSSubmission model """
    translation = kwargs['instance']
    try:
        # check if we need to submit this translation
        r = VCSResource.objects.get(tx_resource=translation.source_entity.resource)
        try:
            sub = VCSSubmission.objects.get(tx_translation=translation)
        except VCSSubmission.DoesNotExist:
            sub = VCSSubmission(tx_translation=translation, vcs_resource=r)
        # get the old string since model has not been saved yet
        sub.old_string = Translation.objects.get(pk=translation.pk).string
        sub.save()
    except VCSResource.DoesNotExist:
        # we don't want to the translation
        pass
pre_save.connect(add_submission, sender=Translation)


def default_state():
    """ Returns the default state that should be used
        for submitting new translations """
    if VALIDATION:
        return VCS_SUBMISSION_STATES[1][0]
    else:
        return VCS_SUBMISSION_STATES[0][0]
