import csv

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient

FILE_LIST = {
    Ingredient: "ingredients.csv",
}


class Command(BaseCommand):
    """
    Команда импорта csv файла по списку.
    """

    def handle(self, *args, **kwargs):
        for model, filename in FILE_LIST.items():
            with open(
                f"{settings.BASE_DIR}/data/{filename}", "r", encoding="utf-8"
            ) as file_csv:
                reader = csv.DictReader(file_csv, delimiter=",")
                try:
                    model.objects.bulk_create(model(**data) for data in reader)
                    print(
                        f"Файл {filename} для модели {model}" f"успешно импортирован."
                    )
                except Exception as error:
                    print(f"Невозможно импортировать файл {filename}. ", error)
        self.stdout.write(self.style.SUCCESS("Импорт файлов завершен"))
