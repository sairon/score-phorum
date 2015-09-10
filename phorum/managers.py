from mptt.querysets import TreeQuerySet


class PublicMessageQuerySet(TreeQuerySet):
    def last_message(self):
        return self.order_by('created').last()
