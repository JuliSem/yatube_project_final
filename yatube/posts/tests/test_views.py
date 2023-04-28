import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from mixer.backend.django import mixer
from yatube.settings import POSTS_NUMBER

from ..models import Follow, Group, Post, User

COUNT_OF_POSTS = 15
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.user = mixer.blend(User)
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = mixer.blend(Group)
        cls.post = mixer.blend(
            Post,
            author=cls.user,
            group=cls.group,
            image=cls.uploaded
        )

    def setUp(self):
        cache.clear()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_posts', kwargs={'slug': self.group.slug}):
                'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.user.username}):
                'posts/profile.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}):
                'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}):
                'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон главной страницы сформирован
        с правильным контекстом.
        """
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response.context['page_obj'][0], self.post)

    def test_cache_content_index_page(self):
        """Проверка хранения и отчистка кэша на главной странице."""
        response = self.authorized_client.get(reverse('posts:index'))
        posts = response.content
        Post.objects.create(
            text='Проверка кэша',
            author=self.user,
            group=self.group
        )
        old_response = self.authorized_client.get(reverse('posts:index'))
        old_posts = old_response.content
        self.assertEqual(old_posts, posts)
        cache.clear()
        new_response = self.authorized_client.get(reverse('posts:index'))
        new_posts = new_response.content
        self.assertNotEqual(old_posts, new_posts)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован
        с правильным контекстом.
        """
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        self.assertEqual(response.context['post'].text, self.post.text),
        self.assertEqual(response.context['post'].group, self.post.group)
        self.assertEqual(response.context['post'].author, self.post.author)
        self.assertEqual(response.context['post'].image, self.post.image)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован
        с правильным контекстом.
        """
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user.username}))
        first_obj = response.context['page_obj'][0]
        self.assertEqual(first_obj.author, self.post.author)
        self.assertEqual(first_obj.text, self.post.text)
        self.assertEqual(first_obj.group, self.post.group)
        self.assertEqual(first_obj.image, self.post.image)

    def test_group_posts_page_show_correct_context(self):
        """Шаблон group_posts сформирован
        с правильным контекстом.
        """
        response = self.authorized_client.get(
            reverse('posts:group_posts', kwargs={'slug': self.group.slug}))
        first_obj = response.context['group']
        self.assertEqual(first_obj.title, self.group.title)
        self.assertEqual(first_obj.slug, self.group.slug)
        self.assertEqual(first_obj.description, self.group.description)

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован
        с правильным контекстом.
        """
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_new_post_added_correctly(self):
        """При создании нового поста он появляется на:
        главной странице, странице группы и профиля автора"""
        new_post = Post.objects.create(
            text='Новый пост',
            author=self.user,
            group=self.group,
            image=self.uploaded
        )
        response_index = self.authorized_client.get(reverse('posts:index'))
        response_group_posts = self.authorized_client.get(
            reverse('posts:group_posts', kwargs={'slug': self.group.slug}))
        response_profile = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user.username}))
        index = response_index.context['page_obj']
        group_posts = response_group_posts.context['page_obj']
        profile = response_profile.context['page_obj']
        self.assertIn(new_post,
                      index,
                      'Новый пост не добавлен на главную страницу.')
        self.assertIn(new_post,
                      group_posts,
                      'Новый пост не добавлен на страницу группы.')
        self.assertIn(new_post,
                      profile,
                      'Новый пост не добавлен на страницу профиля.')

    def test_post_create_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован
        с правильным контекстом.
        """
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        self.assertTrue(response.context.get('is_edit'))


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = mixer.blend(User)
        cls.group = mixer.blend(Group)
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        paginator_objects = []
        for i in range(COUNT_OF_POSTS):
            paginator_objects.append(Post(text='Тестовый пост' + str(i),
                                          author=cls.user,
                                          group=cls.group))
        Post.objects.bulk_create(paginator_objects)

    def setUp(self):
        cache.clear()

    def test_correct_posts_of_page_guest_client(self):
        """Проверка количества постов на первой и второй страницах:
        index, group_posts, profile для неавторизованного клиента."""
        pages = (
            reverse('posts:index'),
            reverse('posts:group_posts', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username}))
        for page in pages:
            response_1 = self.client.get(page)
            response_2 = self.client.get(page + '?page=2')
            count_posts_1 = len(response_1.context['page_obj'])
            count_posts_2 = len(response_2.context['page_obj'])
            self.assertEqual(count_posts_1,
                             POSTS_NUMBER,
                             'Количество постов на первой странице'
                             'не соответствует ожидаемому.')
            self.assertEqual(count_posts_2,
                             COUNT_OF_POSTS - POSTS_NUMBER,
                             'Количество постов на второй странице'
                             'не соответствует ожидаемому.')

    def test_correct_posts_of_page_authorized_client(self):
        """Проверка колиества постов на первой и второй страницах:
        index, group_posts, profile для авторизованного клиента."""
        pages = (
            reverse('posts:index'),
            reverse('posts:group_posts', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username}))
        for page in pages:
            response_1 = self.authorized_client.get(page)
            response_2 = self.authorized_client.get(page + '?page=2')
            count_posts_1 = len(response_1.context['page_obj'])
            count_posts_2 = len(response_2.context['page_obj'])
            self.assertEqual(count_posts_1,
                             POSTS_NUMBER,
                             'Количество постов на первой странице'
                             'не соответствует ожидаемому.')
            self.assertEqual(count_posts_2,
                             COUNT_OF_POSTS - POSTS_NUMBER,
                             'Количество постов на второй странице'
                             'не соответствует ожидаемому.')


class FollowViewsTest(TestCase):
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

    def test_user_follow_author(self):
        """Авторизованный пользователь может подписаться
        на других пользователей."""
        follow_count = Follow.objects.count()
        self.authorized_client.get(reverse(
            'posts:profile_follow', kwargs={'username': self.author.username}
        ))
        self.assertTrue(
            Follow.objects.filter(
                user=self.user,
                author=self.author
            ).exists()
        )
        self.assertEqual(Follow.objects.count(), follow_count + 1,
                         'Пользователь не подписался на автора')

    def test_user_unfollow_author(self):
        """Авторизованный пользователь после подписки на автора
        так же может и отписаться от него."""
        Follow.objects.create(user=self.user, author=self.author)
        follow_count = Follow.objects.count()
        self.authorized_client.get(reverse(
            'posts:profile_unfollow', kwargs={'username': self.author.username}
        ))
        self.assertEqual(Follow.objects.count(), follow_count - 1)
        self.assertFalse(
            Follow.objects.filter(
                user=self.user,
                author=self.author
            ).exists()
        )

    def test_new_post_on_follow_index(self):
        """Новая запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется в ленте тех, кто не подписан."""
        Follow.objects.create(user=self.user, author=self.author)
        new_post_author = Post.objects.create(
            text='Новый пост автора',
            author=self.author,
            group=self.group
        )
        response_follow_index = self.authorized_client.get(
            reverse('posts:follow_index'))
        follow_index = response_follow_index.context['page_obj']
        self.assertIn(new_post_author,
                      follow_index,
                      'Новая запись пользователя не появилась в ленте тех, '
                      'кто на него подписан.')
        self.authorized_client.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.author.username}))
        new_response_follow_index = self.authorized_client.get(
            reverse('posts:follow_index'))
        new_follow_index = new_response_follow_index.context['page_obj']
        self.assertNotIn(new_post_author,
                         new_follow_index,
                         'Новая запись автора не пропала из ленты '
                         'пользователя после отписки от него.')
