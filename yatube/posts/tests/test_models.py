from django.test import TestCase
from mixer.backend.django import mixer

from ..models import Group, Post, User

COUNT_OF_SYMBOL = 15


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = mixer.blend(User)
        cls.post = mixer.blend(Post, author=cls.user)

    def test_models_have_correct_post_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = self.post
        expected_post_name = self.post.text[:COUNT_OF_SYMBOL]
        self.assertEqual(expected_post_name, str(post))


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = mixer.blend(Group)

    def test_models_have_correct_group_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        group = self.group
        expected_group_name = group.title
        self.assertEqual(expected_group_name, str(group))
