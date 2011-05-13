from django import forms

from txsubmissions.models import VCS_SUBMISSION_STATES

class SubmissionsForm(forms.Form):
    project = forms.ChoiceField()
    resource = forms.ChoiceField()
    translator = forms.ChoiceField()
    state = forms.ChoiceField(choices=VCS_SUBMISSION_STATES)
