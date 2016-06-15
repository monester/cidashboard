from django.db import models

from cidashboard.models.common import BaseModel
from cidashboard.constants import JENKINS_STATUSES, TRIGGER_TYPE_CHOICES


class CISystem(BaseModel):
    """CI System definition"""
    name = models.CharField(max_length=255)

    def sources(self):
        """Now only jenkins can be a source"""
        return [i for i in self.jenkinses]

    # def add_source(self, source):
    #     if isinstance(source, Jenkins):
    #         self.jenkinses.add(source)
    #     else:
    #         raise Exception("Invalid source %s" % source)

    def __repr__(self):
        return "<CISystem: %s>" % self.url


class Jenkins(BaseModel):
    ci_system = models.ForeignKey('cidashboard.CISystem', related_name='jenkinses')
    url = models.CharField(max_length=255)
    login = models.CharField(max_length=255, null=True, blank=True)
    api_key = models.CharField(max_length=255, null=True, blank=True)

    @property
    def last_status(self):
        """Last status"""
        return self.statuses.last()

    def __repr__(self):
        return "<Jenkins: %s>" % self.url


class JobViewBase(BaseModel):
    jenkins = models.OneToOneField(Jenkins)
    change_ci_status = models.BooleanField(default=False)
    name = models.CharField(max_length=255)

    class Meta:
        abstract = True

    def __eq__(self, other):
        """We should check not for hash but for equalness of filters"""
        fields = [
            'ci_system',
            'change_ci_status',
            'name',
            'triggered_by',
            'gerrit_branch',
            'gerrit_refspec',
        ]
        if isinstance(other, self.__class__):
            return all(
                getattr(self, name) == getattr(other, name)
                for name in fields
                if hasattr(self, name)
            )
        return False

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, self.name)

    def get(self):
        pass


class Job(JobViewBase):
    """Job definition"""
    triggered_by = models.CharField(max_length=TRIGGER_TYPE_CHOICES_LEN, choices=list((v, v) for k, v in TRIGGER_TYPE_CHOICES), null=True)
    gerrit_branch = models.CharField(max_length=255, null=True)
    gerrit_refspec = models.CharField(max_length=255, null=True)


class View(JobViewBase):
    pass


class JobViewResultBase(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, choices=((k, v) for k, v in JENKINS_STATUSES.items()), null=True)

    class Meta:
        abstract = True


class JobResult(JobViewResultBase):
    job = models.ForeignKey(Job, related_name='results', null=True, on_delete=models.SET_NULL)
    build_id = models.IntegerField(null=True)


class ViewResult(JobViewResultBase):
    view = models.ForeignKey(View, related_name='results', null=True, on_delete=models.SET_NULL)


class CIStatus(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    jobs = models.ManyToManyField(JobResult)
    views = models.ManyToManyField(ViewResult)
    status = models.CharField(max_length=10, )
