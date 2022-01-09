from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Comment, Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username='user')
        cls.commentator = User.objects.create(username='another_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестируем тестовый пост',
        )
        cls.comment = Comment.objects.create(
            text='Тестовый комментарий для поста',
            author=cls.commentator,
            post=cls.post,
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = PostModelTest.post
        group = PostModelTest.group
        comment = PostModelTest.comment
        expected_objects_name = {
            post: str(self.post)[:15],
            group: 'Тестовая группа',
            comment: str(self.comment)[:15]
        }
        for model, name in expected_objects_name.items():
            with self.subTest(model=model):
                self.assertEqual(
                    str(model), name,
                    f'В модели {model} некорректно работает метод __str__.'
                )

    def test_models_verbose_names(self):
        """Проверяем у моделей поле verbose_name"""
        post = PostModelTest.post
        group = PostModelTest.group
        comment = PostModelTest.comment
        expected_verbose_names = {
            post: {
                'text': 'Текст поста',
                'pub_date': 'Дата создания поста',
                'author': 'Автор поста',
                'group': 'Группа',
            },
            group: {
                'title': 'Название группы',
                'slug': 'URL группы',
                'description': 'Описание группы',
            },
            comment: {
                'post': 'Пост',
                'author': 'Автор',
                'text': 'Комментарий',
                'created': 'Создан'
            }
        }
        for model, verbose_names in expected_verbose_names.items():
            with self.subTest(model=model):
                for field, expected_text in verbose_names.items():
                    with self.subTest(field=field):
                        self.assertEqual(
                            model._meta.get_field(field).verbose_name,
                            expected_text,
                            f'В модели {model} некорректные verbose_name.'
                        )

    def test_help_text(self):
        """Проверяем у моделей поле help_text"""
        post = PostModelTest.post
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Выберите группу',
        }
        for field, expected in field_help_texts.items():
            with self.subTest(value=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected)
