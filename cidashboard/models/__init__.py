from django.db import models
from django.db.models.signals import post_save

from cidashboard.models.common import BaseModel
from cidashboard.models.models import *


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


class Product(BaseModel):
    """Product definition"""
    name = models.CharField(max_length=255)


class Result(BaseModel):
    """Results of Rule"""
    # job = models.ForeignKey(Job, related_name='results')
    # build_id = models.IntegerField(null=True)
    type = models.IntegerField()
    result = models.CharField(max_length=10, default='SKIPPED')

    def __eq__(self, other):
        """We should check is rule and result is equal. We should avoid same statuses with different ID"""
        if isinstance(other, self.__class__):
            return all(getattr(self, name) == getattr(other, name) for name in ['job', 'result'])
        return False

    @property
    def url(self):
        return '%s/view/%s/%s' % (self.job.ci_system.url, self.job.name, self.build_id)

    def __repr__(self):
        return "<JobResult: %s result %s>" % (self.url, self.result)


class CIStatus(BaseModel):
    """Status of CI Systems"""
    ci_system = models.ForeignKey(CISystem, related_name='statuses')
    _results = models.ManyToManyField(Result)
    status = models.CharField(max_length=255)

    jobs_results_list = []

    def results(self, **filters):
        """Current data from latest status"""
        result = set()
        for rule_type in ['job', 'view']:
            # variables = {}
            # for filter_name in filters:
            #     if filter_name.format(**variables)
            result.update([i for i in getattr(self, '{}s_results'.format(rule_type)).filter(**filters)])
        return result

    @classmethod
    def make_from_results(cls, ci_system, results=None):
        self = cls(ci_system=ci_system)
        if results:
            self.jobs_results_list = results
        else:
            for rule_type in ['job', 'view']:
                self.ci_system.jenkinses
        results_set = set(result.result for result in results)

        result = 'NONE'
        if 'FAILURE' in results_set:
            result = 'FAILURE'
        elif 'SUCCESS' in results_set:
            result = 'SUCCESS'

        self.status = result
        return self

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.ci_system == other.ci_system and self.status == other.status
        return False

    def __repr__(self):
        return "<CIStatus: %s: %s>" % (getattr(self.ci_system, 'url', ''), self.status)


class ProductStatus(BaseModel):
    """Status of Product"""
    product = models.ForeignKey(Product, related_name='statuses')
    results = models.ManyToManyField(Result)


# Signals
def post_save_status(sender, instance, **kwargs):
    for i in instance.jobs_results_list:
        instance.jobs_results.add(i)


post_save.connect(post_save_status, sender=CIStatus)
post_save.connect(post_save_status, sender=ProductStatus)
