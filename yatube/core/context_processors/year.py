import datetime


def year(request):
    """Добавляет переменную с текущим годом."""
    a = datetime.date.today()
    return {'year': a.year}
