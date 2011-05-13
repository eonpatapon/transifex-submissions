from django import forms

from txsubmissions.models import VCS_SUBMISSION_STATES

class SubmissionsForm(forms.Form):
    language = forms.ChoiceField()
    project = forms.ChoiceField()
    resource = forms.ChoiceField()
    translator = forms.ChoiceField()
    state = forms.ChoiceField(choices=VCS_SUBMISSION_STATES)

    def __init__(self, data, *fields_choices):
        super(SubmissionsForm, self).__init__(data)
        for field, choices in zip([ f for n, f in self.fields.items()], fields_choices):
            field.choices = choices
