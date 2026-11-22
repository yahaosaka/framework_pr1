from django.db import models


class Player(models.Model):
    name = models.CharField("Имя", max_length=200)
    email = models.EmailField(blank=True)

    class Meta:
        ordering = ["name", "pk"]

    def __str__(self):
        return self.name
