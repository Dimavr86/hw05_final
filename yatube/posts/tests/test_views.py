import shutil
import time

from django import forms
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Follow, Group, Post, User

from .fix_data import TEMP_MEDIA_ROOT, small_gif

# Создаем временную папку для медиа-файлов;
# на момент теста медиа папка будет переопределена


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Создаём запись в БД для проверки доступности адреса group/test-slug/
        cls.group = Group.objects.create(
            title='Тестовая группа',
            description='Описание тестовой группы',
            slug='test-slug',
        )
        # создаём автора тестового поста
        cls.author = User.objects.create(username='Test_author')
        # создаём второго пользователя
        cls.commentator = User.objects.create(username='another_user')
        # создаём тестовый пост
        cls.test_img = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Текст поста для теста',
            group=cls.group,
            image=cls.test_img
        )
        cls.comment = Comment.objects.create(
            text='Тестовый комментарий для поста',
            author=cls.commentator,
            post=cls.post,
        )
        cls.pages_properties = {
            'index': {
                'view_func': reverse('posts:index'),
                'template': 'posts/index.html'
            },
            'group_list': {
                'view_func': reverse(
                    'posts:group_list', kwargs={'slug': cls.group.slug}
                ),
                'template': 'posts/group_list.html',
            },
            'profile': {
                'view_func': reverse(
                    'posts:profile', kwargs={'username': cls.author.username}
                ),
                'template': 'posts/profile.html'
            },
            'post_detail': {
                'view_func': reverse(
                    'posts:post_detail', kwargs={'post_id': cls.post.id}
                ),
                'template': 'posts/post_detail.html'
            },
            'post_edit': {
                'view_func': reverse(
                    'posts:post_edit', kwargs={'post_id': cls.post.id}
                ),
                'template': 'posts/create_post.html'
            },
            'create_post': {
                'view_func': reverse('posts:post_create'),
                'template': 'posts/create_post.html'
            },
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        # очищаем кэш от данных после других тестов
        cache.clear()
        # Создаем неавторизованный клиент
        self.guest = Client()
        # Создаем авторизованый клиент
        self.user = User.objects.create(username='NormalUser')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)

    def test_pages_uses_correct_template(self):
        """Проверка namespase:name и шаблонов"""
        for page, page_properties in self.pages_properties.items():
            with self.subTest(page=page):
                response = self.authorized_author.get(
                    page_properties['view_func']
                )
                template = page_properties['template']
                self.assertTemplateUsed(response, template)

    def check_post(self, context):
        """Вызываемая функция для проверки информации в посте."""
        with self.subTest(context=context):
            self.assertEqual(context.text, self.post.text)
            self.assertEqual(context.pub_date, self.post.pub_date)
            self.assertEqual(context.author, self.post.author)
            self.assertEqual(context.group.id, self.post.group.id)
            self.assertEqual(context.image, self.post.image)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом"""
        response = self.authorized_client.get(reverse('posts:index'))
        # Взяли первый элемент из списка и проверили, что его содержание
        # совпадает с ожидаемым
        self.check_post(response.context['page_obj'][0])

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        self.assertEqual(response.context['group'], self.group)
        self.check_post(response.context['page_obj'][0])

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': self.author.username})
        )
        self.assertEqual(response.context['author'], self.author)
        self.check_post(response.context['page_obj'][0])

    def test_detail_page_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id})
        )
        self.check_post(response.context['post'])
        # проверяем, что view-функция передаёт комментарии в контексте
        self.assertTrue(self.comment in response.context['comments'])

    def test_post_create_and_edit_pages_show_correct_context(self):
        """Проверяем корректность форм в контексте."""
        pages = [
            'create_post',
            'post_edit'
        ]
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.ImageField
        }
        for page in pages:
            with self.subTest(page=page):
                response = self.authorized_author.get(
                    self.pages_properties[page]['view_func']
                )
                for field, expected_type in form_fields.items():
                    with self.subTest(field=field):
                        self.assertIsInstance(
                            response.context.get('form').fields[field],
                            expected_type
                        )

    def test_check_cache_index_page(self):
        """Проверяем работу кэша на главной странице"""
        # делаем первый запрос к главной странице
        response_1 = self.authorized_client.get(reverse('posts:index'))
        # удаляем запись из тестовой базы
        Post.objects.get(id=self.post.id).delete()
        # для большей уверенности делаем небольшую паузу
        time.sleep(3)
        # делаем второй запрос к странице
        response_2 = self.authorized_client.get(reverse('posts:index'))
        # сравниваем, что содержимое осталось на странице
        self.assertEqual(response_1.content, response_2.content)
        # теперь принудительно очищаем кэш
        cache.clear()
        # снова делаем запрос к главной странице
        response_3 = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(response_1.content, response_3.content)


class PaginatorTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Test_author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            description='Описание тестовой группы',
            slug='test-slug',
        )
        # указываем сколько тестовых постов мы хотим создать
        cls.posts_qty = 13
        # создаём тестовые посты
        posts = [Post(
            text=f'Текст поста №{i}',
            author=cls.author,
            group=cls.group
        ) for i in range(cls.posts_qty)]
        Post.objects.bulk_create(posts)

        # указываем на каких страницах нужно тестировать пагинатор
        cls.pages_for_test = [
            'index',
            'group_list',
            'profile'
        ]

    def setUp(self):
        self.guest = Client()

    def test_pages_contain_correct_number_of_records(self):
        """Проверяем, что пагинатор выводит правильное
        количество постов на страницу"""
        # устанавливаем количество постов на 1 страницу
        posts_per_page = 10
        # количество оставшихся постов на 2-й странице пагинатора
        posts_remaining = self.posts_qty - posts_per_page
        pages_for_test = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.author.username})
        ]
        for view_func in pages_for_test:
            with self.subTest(view_func=view_func):
                response = self.guest.get(view_func)
                self.assertEqual(
                    len(response.context['page_obj']), posts_per_page
                )
                response = self.guest.get(view_func + '?page=2')
                self.assertEqual(
                    len(response.context['page_obj']), posts_remaining
                )


class FollowersTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Test_author')
        cls.follower = User.objects.create(username='Test_follower')
        cls.post = Post.objects.create(
            author=cls.author,
            text='Текст поста для теста',
        )
        cls.user_2 = User.objects.create(username='Another_user')

    def setUp(self):
        # очищаем кэш от данных после других тестов
        cache.clear()
        self.authorized_follower = Client()
        self.authorized_follower.force_login(self.follower)
        self.another_user = Client()
        self.another_user.force_login(self.user_2)

    def test_user_can_subscribe(self):
        """Авторизованный пользователь может
        подписываться и отписываться на/от других пользователей"""
        follow_count = Follow.objects.count()
        # создаём подписку
        self.authorized_follower.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.author.username}
        ))
        follow = Follow.objects.all().latest('id')
        # проверяем, что подписка создалась
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.assertEqual(follow.author_id, self.author.id)
        self.assertEqual(follow.user_id, self.follower.id)
        self.authorized_follower.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.author.username}
        ))
        self.assertEqual(Follow.objects.count(), 0)
        self.assertFalse(Follow.objects.filter(
            user=self.follower,
            author=self.author
        ).exists())

    def test_follow_index_page_correct(self):
        """Проверяем, Новая запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется в ленте тех, кто не подписан."""
        # создаём подписку
        Follow.objects.create(
            user=self.follower,
            author=self.author)
        response = self.authorized_follower.get(reverse(
            'posts:follow_index'
        ))
        # проверяем, что пост автора, на которого подписались есть на странице
        self.assertEqual(response.context['page_obj'][0], self.post)
        # делаем запрос страница для другого пользователя
        response_2 = self.another_user.get(reverse(
            'posts:follow_index'
        ))
        # проверяем, что у него нет постов от авторов,
        # на которых он не подписывался
        self.assertFalse(self.post in response_2.context['page_obj'])
