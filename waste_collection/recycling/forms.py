from django import forms
from .models import WasteCollection

# --------------------------------------------------------------------
# Form for creating and updating WasteCollection entries.
#
# Notes on the two behaviour changes requested:
#
# 1. waste_type is now a RadioSelect instead of a <select> dropdown.
#    The template renders each radio option as an image/icon card
#    (see collection_form.html) instead of Django's default bullets.
#
# 2. status is intentionally left OUT of Meta.fields. Residents should
#    never be able to set/change it - a new request always starts at
#    "Submitted for Collection" (enforced in the view). Only when an
#    admin edits an *existing* record do we add a status field back in,
#    via __init__ below, so they can move it forward through the
#    pending -> collected -> completed workflow.
# --------------------------------------------------------------------
class WasteCollectionForm(forms.ModelForm):
    class Meta:
        model = WasteCollection  # Link the form to the WasteCollection model

        # Fields from the model that will appear in the form.
        # 'status' is deliberately excluded - see class docstring above.
        fields = [
            'household_name',
            'address',
            'phone',
            'waste_type',
            'weight_kg',
            'collection_date',
            'notes',
        ]

        # Custom widgets for specific fields to improve user experience
        widgets = {
            # Multi-line text area for the address
            'address': forms.Textarea(attrs={'rows': 3}),

            # Multi-line text area for optional notes
            'notes': forms.Textarea(attrs={'rows': 3}),

            # HTML5 date picker for selecting the collection date
            'collection_date': forms.DateInput(attrs={'type': 'date'}),

            # Radio buttons so the template can render these as
            # clickable image cards instead of a plain dropdown.
            'waste_type': forms.RadioSelect,
        }

    def __init__(self, *args, is_admin=False, **kwargs):
        super().__init__(*args, **kwargs)

        # Django auto-adds a blank "---------" choice to fields with
        # `choices` whenever the model field has no default (even
        # though waste_type is required and blank=False) - strip it
        # out so the card grid only shows the real 6 waste types.
        self.fields['waste_type'].choices = WasteCollection.WASTE_TYPES
        self.fields['waste_type'].empty_label = None

        # Only staff/admins editing an *existing* request get a status
        # control. New requests (self.instance.pk is None) always start
        # as "submitted", set explicitly in the view's form_valid().
        if is_admin and self.instance and self.instance.pk:
            self.fields['status'] = forms.ChoiceField(
                choices=WasteCollection.STATUS_CHOICES,
                initial=self.instance.status,
                label='Status',
            )

    def save(self, commit=True):
        instance = super().save(commit=False)
        # If a status field was added (admin editing), apply it.
        if 'status' in self.cleaned_data:
            instance.status = self.cleaned_data['status']
        if commit:
            instance.save()
        return instance