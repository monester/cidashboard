from django.db import models


class BaseModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class JobResult(BaseModel):
    """Results of Rule"""
    job = models.ForeignKey('cidashboard.Job', related_name='results')
    build_id = models.IntegerField(null=True)
    result = models.CharField(max_length=10, default='SKIPPED')

    def __eq__(self, other):
        """We should check is rule and result is equal. We should avoid same statuses with different ID
        """
        if isinstance(other, self.__class__):
            return all(getattr(self, name) == getattr(other, name) for name in ['job', 'result'])
        return False

    @property
    def url(self):
        return '%s/view/%s/%s' % (self.job.ci_system.url, self.job.name, self.build_id)

    def __repr__(self):
        return "<JobResult: %s result %s>" % (self.url, self.result)
