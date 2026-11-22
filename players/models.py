from django.db import models


class Player(models.Model):
    name = models.CharField("Имя", max_length=200)
    email = models.EmailField("Электронная почта", blank=True)

    class Meta:
        verbose_name = "Игрок"
        verbose_name_plural = "Игроки"
        ordering = ["name", "pk"]

    def __str__(self):
        return self.name
