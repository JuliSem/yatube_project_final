from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        help_text = {
            'text': 'Введите текст поста',
            'group': 'Выберите нужную группу',
            'image': 'Загрузите своё изображение'
        }
        lable = {
            'text': 'Текст поста',
            'group': 'Группа поста',
            'image': 'Изображение'
        }

    def clean_subject(self):
        data = self.cleaned_data['text']
        if '' not in data():
            raise forms.ValidationError('Поле надо заполнить')
        return data


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        help_text = {
            'text': 'Введите текст комментария',
        }
