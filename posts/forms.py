from django.forms import ModelForm, Textarea
from .models import Post, Comment
from django import forms


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            "text": "Текст",
            "group": "Группа",
            'image': 'Изображение'
        }
        help_texts = {
            "text": "Введите здесь текст своего поста",
            "group": "Выберете группу к которой относится пост"
        }


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {"text": "Текст"}
        help_texts = {"text": "Введите здесь текст своего поста"}
