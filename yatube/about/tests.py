from django.test import Client, TestCase


class StaticURLTests(TestCase):
    def setUp(self):
        # Устанавливаем данные для тестирования
        # Создаём экземпляр клиента. Он неавторизован.
        self.guest_client = Client()

    def test_about(self):
        """Проверяем доступность страницы "Об авторе" """
        response = self.guest_client.get('/about/author/')
        self.assertEqual(response.status_code, 200)

    def test_tech(self):
        """Проверяем доступность страницы "Технологии" """
        response = self.guest_client.get('/about/tech/')
        self.assertEqual(response.status_code, 200)
