import shutil
from http import HTTPStatus

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post, User
from .fix_data import TEMP_MEDIA_ROOT, small_gif


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Test_author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Описание тестовой группы',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest = Client()
        self.authorized_user = Client()
        self.authorized_user.force_login(self.author)

    def test_create_post(self):
        """Проверка создания записи авторизированным клиентом."""
        # Подсчитаем количество записей
        posts_count = Post.objects.count()
        test_img = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Текст поста',
            'group': self.group.id,
            'image': test_img,
        }
        # Отправляем POST-запрос
        response = self.authorized_user.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        # Проверяем статус ответа
        self.assertEqual(response.status_code, HTTPStatus.OK)
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), posts_count + 1)
        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response,
            reverse(
                'posts:profile', kwargs={'username': self.author.username})
        )
        post = Post.objects.filter(text=form_data['text'])
        print(post)
        self.assertTrue(
            Post.objects.filter(
                group=form_data['group'],
                text=form_data['text'],
                image='posts/small.gif',
            ).exists()
        )

    def test_authorized_user_edit_post(self):
        """Проверка редактирования записи авторизированным клиентом."""
        post = Post.objects.create(
            text='Текст поста',
            author=self.author,
            group=self.group,
        )
        # вставляем в форму измененные данные
        form_data = {
            'text': 'Отредактированный текст поста',
            'group': self.group.id,
        }
        response = self.authorized_user.post(
            reverse(
                'posts:post_edit', args=[post.id]), data=form_data, follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': post.id})
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        # Проверяем, что в созданном посте изменённая информация

    def test_create_post_with_empty_text(self):
        """Проверяем, что нельзя создать пост без текста."""
        posts_count = Post.objects.count()
        form_data = {
            'text': '',
            'group': ''
        }
        response = self.authorized_user.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertFormError(
            response,
            'form',
            'text',
            'Обязательное поле.'
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_guest_create_post(self):
        """Проверка создания записи неавторизованным пользователем."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст поста',
            'group': self.group.id,
        }
        response = self.guest.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        # Проверяем, что произошел редирект на страницу для авторизации
        redirect = reverse('login') + '?next=' + reverse('posts:post_create')
        self.assertRedirects(response, redirect)
        # Проверяем, что пост не создался
        self.assertEqual(Post.objects.count(), posts_count)
