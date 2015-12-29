from django.db import models


class RoomQueryset(models.QuerySet):
    def pinned(self):
        return self.filter(pinned=True)

    def not_pinned(self):
        return self.filter(pinned=False)
