from django import forms
from django.core.exceptions import ValidationError

from .models import Comment, Post


class PostForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['group'].empty_label = '<--Группа не выбрана-->'

    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        help_texts = {
            'text': ('Текст нового поста'),
            'group': ('Группа, к которой будет относиться пост')
        }

    def clean_text(self):
        text = self.cleaned_data['text']
        if len(text) > 255:
            raise ValidationError('Длина превышает 255 символов')

        return text

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']