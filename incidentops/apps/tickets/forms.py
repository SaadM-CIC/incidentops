from django import forms
from .models import Ticket, Category
from apps.accounts.models import CustomUser


class TicketCreateForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ('title', 'description', 'category', 'priority', 'attachment')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all()
        self.fields['category'].empty_label = "— Sélectionner une catégorie —"


class TicketEditForm(forms.ModelForm):
    """Formulaire limité pour l'utilisateur qui veut modifier sa demande."""
    class Meta:
        model = Ticket
        fields = ('title', 'description', 'attachment')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }


class TicketStatusForm(forms.Form):
    """Formulaire de changement de statut."""
    new_status = forms.ChoiceField(choices=[], label="Nouveau statut")
    comment = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
        label="Commentaire (optionnel)"
    )

    def __init__(self, *args, allowed_transitions=None, **kwargs):
        super().__init__(*args, **kwargs)
        if allowed_transitions:
            self.fields['new_status'].choices = [
                (s.value, s.label) for s in allowed_transitions
            ]


class TicketAssignForm(forms.ModelForm):
    """Formulaire d'affectation à un technicien (admin seulement)."""
    class Meta:
        model = Ticket
        fields = ('assigned_to',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_to'].queryset = CustomUser.objects.filter(
            role__in=['technicien', 'admin']
        )
        self.fields['assigned_to'].empty_label = "— Choisir un technicien —"
        self.fields['assigned_to'].label = "Technicien"
