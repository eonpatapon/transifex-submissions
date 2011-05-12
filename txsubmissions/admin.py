from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from txsubmissions.models import VCSSubmission, VCSProject, VCSResource, VCSHistory

class VCSSubmissionAdmin(admin.ModelAdmin):
    list_display = ('tx_resource', 'tx_language', 'tx_added', 'vcs_state', 'vcs_last_action')


class VCSProjectResourceInline(admin.TabularInline):
    model = VCSResource
    verbose_name = _("Resource")


class VCSProjectAdmin(admin.ModelAdmin):
    list_display = ('tx_project', 'vcs_backend', 'vcs_url', 'vcs_checkout')
    inlines = (VCSProjectResourceInline,)


class VCSHistoryAdmin(admin.ModelAdmin):
    list_display = ('tx_resource', 'tx_language')

admin.site.register(VCSSubmission, VCSSubmissionAdmin)
admin.site.register(VCSProject, VCSProjectAdmin)
admin.site.register(VCSHistory, VCSHistoryAdmin)
