from django.core.management import BaseCommand
from recipes.models import Tag


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        data = [
            {'name': 'Завтрак', 'color': '#FFA07A', 'slug': 'breakfast'},
            {'name': 'Обед', 'color': '#90EE90', 'slug': 'lunch'},
            {'name': 'Ужин', 'color': '#87CEFA', 'slug': 'dinner'}]
        Tag.objects.bulk_create(Tag(**tag) for tag in data)
        self.stdout.write(self.style.SUCCESS('Все тэги загружены'))
