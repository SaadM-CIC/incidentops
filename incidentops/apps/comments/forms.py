from django import forms
from .models import Comment


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('content', 'is_internal')
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Ajouter un commentaire...'
            }),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Seuls techniciens et admins voient l'option "note interne"
        if user and user.role == 'user':
            self.fields.pop('is_internal')