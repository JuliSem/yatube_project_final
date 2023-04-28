import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from mixer.backend.django import mixer

from ..forms import PostForm
from ..models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = mixer.blend(User)
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.author = mixer.blend(User)
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.group = mixer.blend(Group)
        cls.post = mixer.blend(Post, author=cls.author, group=cls.group)
        cls.form = PostForm

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        """При отправке валидной формы со страницы создания поста
        создаётся новая запись в БД.
        """
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый пост 2',
            'group': self.group.id,
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse('posts:profile',
                              kwargs={'username': self.user.username}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый пост 2',
                group=self.group.id,
                image=f'posts/{uploaded}'
            ).exists())
        new_post = Post.objects.latest('id')
        self.assertEqual(new_post.text, form_data['text'])
        self.assertEqual(new_post.group.id, form_data['group'])
        self.assertEqual(new_post.image, f'posts/{uploaded}')

    def test_post_edit(self):
        """При отправке валидной формы со страницы редактирования поста
        происходит изменение поста с post.id в БД.
        """
        posts_count = Post.objects.count()
        form_data_edit = {
            'text': 'Отредактированный пост',
        }
        response = self.author_client.post(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data_edit,
            follow=True,
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))

        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(Post.objects.filter(
            text='Отредактированный пост',).exists())
        post_edit = Post.objects.latest('text')
        self.assertEqual(post_edit.text, form_data_edit['text'])
        self.assertEqual(post_edit.author, self.post.author)


class CommentFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = mixer.blend(User)
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = mixer.blend(Group)
        cls.post = mixer.blend(
            Post,
            author=cls.user,
            group=cls.group,
        )
        cls.comment = mixer.blend(Comment)

    def test_add_comment_post_detail(self):
        """Проверка создания комментария на странице поста."""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Текст второго комментария',
            'post_id': self.post.id,
            'author': self.user
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Comment.objects.count(), comments_count + 1,
                         'Комментарий не добавлен на страницу поста')
        self.assertTrue(
            Comment.objects.filter(
                text='Текст второго комментария',
                post_id=self.post.id,
                author=self.user
            ).exists(),
            'Данные комментария не совпадают')
        new_comment = Comment.objects.latest('text')
        self.assertEqual(new_comment.text, form_data['text'])
        self.assertEqual(new_comment.author, form_data['author'])
        self.assertEqual(new_comment.post_id, form_data['post_id'])
