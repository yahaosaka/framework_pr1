from django.db import models


class MatchQuerySet(models.QuerySet):
    def active(self):
        return self.filter(status=self.model.Status.ACTIVE)

    def scheduled(self):
        return self.filter(status=self.model.Status.SCHEDULED)

    def completed(self):
        return self.filter(status=self.model.Status.COMPLETED)

    def cancelled(self):
        return self.filter(status=self.model.Status.CANCELLED)

    def for_date(self, value):
        return self.filter(match_date=value)

    def blocking(self):
        return self.filter(status__in=[
            self.model.Status.ACTIVE, self.model.Status.SCHEDULED])

    def update(self, **kwargs):
        if "status" in kwargs and isinstance(kwargs["status"], str):
            kwargs["is_completed"] = (
                kwargs["status"] == self.model.Status.COMPLETED)
            kwargs["is_scheduled"] = (
                kwargs["status"] == self.model.Status.SCHEDULED)
        return super().update(**kwargs)
