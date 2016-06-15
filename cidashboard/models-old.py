from collections import defaultdict
import requests

from django.db import models
from django.db.models.signals import post_save

from cidashboard import constants


class BaseModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class CISystem(BaseModel):
    """CI System definition"""
    name = models.CharField(max_length=255)

    def sources(self):
        """Now only jenkins can be a source"""
        return [i for i in self.jenkinses]

    def add_source(self, source):
        if isinstance(source, Jenkins):
            self.jenkinses.add(source)
        else:
            raise Exception("Invalid source %s" % source)

    def __repr__(self):
        return "<CISystem: %s>" % self.url


class Jenkins(BaseModel):
    ci_system = models.ForeignKey(CISystem, related_name='%(class)ses')
    url = models.CharField(max_length=255)
    login = models.CharField(max_length=255, null=True, blank=True)
    api_key = models.CharField(max_length=255, null=True, blank=True)

    _cache = defaultdict(lambda: dict())

    @classmethod
    def _get_cached(cls, base_url, resource):
        try:
            data = cls._cache[base_url][resource]
        except KeyError:
            cls._cache[base_url][resource] = data = requests.get(base_url + resource).json()
        return data

    @classmethod
    def clean_cache(cls):
        for i in cls._cache:
            del cls._cache[i]

    def get(self, resource):
        """Get JSON from Jenkins CI

        :param url: path to resource should start with '/'
        example: /api/json/
        '/api/json?tree=jobs[name,'
        'builds[id,result,timestamp,duration,actions[parameters[name,value],causes[shortDescription]]]],'
        'views[name,jobs[name,results]]'
        """
        base_url = self.url.rstrip('/')
        if not resource.startswith('/'):
            resource = '/' + resource
        return self._get_cached(base_url, resource)

    def get_job(self, job_name, depth=1):
        return self.get('/job/%s/api/json?depth=%s' % (job_name, depth))

    def get_view(self, view_name, depth=1):
        return self.get('/view/%s/api/json?depth=%s' % (view_name, depth))

    def latest_rule_results(self, **rules_filter):
        """Latest data from Jenkins
        :rtype: set
        """
        return set(i.results.last() for i in self.jobs.filter(**rules_filter) if i.results.count() > 0)

    @property
    def last_status(self):
        """Last status"""
        return self.statuses.last()

    def update_all(self):
        """TEMPORARY FUNCTION"""
        return [i.fetch_latest() for i in self.jobs.filter()]

    def __repr__(self):
        return "<Jenkins: %s>" % self.url


class JobViewBase(BaseModel):
    ci_system = models.ForeignKey(CISystem, related_name='%(class)ss')
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


class Job(JobViewBase):
    """Job definition"""
    triggered_by = models.CharField(choices=list((v, v) for k, v in constants.TRIGGER_TYPE_CHOICES),
                                    null=True, max_length=30)
    gerrit_branch = models.CharField(max_length=255, null=True)
    gerrit_refspec = models.CharField(max_length=255, null=True)

    @property
    def filters_count(self):
        reference_counter = 0
        if self.triggered_by:
            reference_counter += 1
        if self.gerrit_refspec:
            reference_counter += 1
        if self.gerrit_branch:
            reference_counter += 1
        return reference_counter

    # def filters(self):
    #     from collections import defaultdict
    #     filters = {'actions': defaultdict(lambda: dict())}
    #     if self.triggered_by != 'Any':
    #         filters['actions']['causes']['shortDescription'] = \
    #             lambda v: v.startswith(self.triggered_by)
    #     if self.gerrit_branch:
    #         filters['actions'][]
    #     return filters

    def fetch_latest(self):
        data = self.ci_system.get_job(self.name)
        for build in data['builds']:
            if build['building']:  # skip running
                continue
            params = {}
            for action in build['actions']:
                if self.triggered_by and 'causes' in action:
                    # check for triggered_by
                    for cause in action['causes']:
                        descr = cause.get('shortDescription', '')
                        if descr.startswith(self.triggered_by):
                            params['triggered_by'] = self.triggered_by
                            break  # break from causes loop
                if 'parameters' in action:
                    # check for gerrit_branch and gerrit_refspec
                    for parameter in action['parameters']:
                        # print parameter['name'], parameter['value']
                        if parameter['name'] == 'GERRIT_BRANCH' and self.gerrit_branch == parameter['value']:
                            params['gerrit_branch'] = parameter['value']
                        elif parameter['name'] == 'GERRIT_REFSPEC' and self.gerrit_refspec == parameter['value']:
                            params['gerrit_refspec'] = parameter['value']
            if len(params) == self.filters_count:
                # matched, shoud return if same result return exists or create new
                old = self.results.last()
                proposed = JobResult(job=self, build_id=int(build['id']), result=build['result'])
                if proposed == old:
                    return old
                proposed.save()
                return proposed
        return None


class View(JobViewBase):
    def fetch_latest(self):
        view = self.ci_system.get_view(self.name)
        failed = any(job['lastBuild'] == job['lastFailedBuild'] for job in view['jobs'])
        success = all(job['lastBuild'] == job['lastSuccessfulBuild'] for job in view['jobs'])

        result = 'UNKNOWN'
        if failed:
            result = 'FAILED'
        elif success:
            result = 'SUCCESS'

        old = self.results.last()
        proposed = ViewResult(job=self, result=result)
        if proposed == old:
            return old
        proposed.save()
        return proposed


class Product(BaseModel):
    """Product definition"""
    name = models.CharField(max_length=255)
    jobs = models.ManyToManyField(Job)
    views = models.ManyToManyField(View)


class JobResult(BaseModel):
    """Results of Rule"""
    job = models.ForeignKey(Job, related_name='results')
    build_id = models.IntegerField(null=True)
    result = models.CharField(max_length=10, default='SKIPPED')

    def __eq__(self, other):
        """We should check is rule and result is equal. We should avoid same statuses with different ID
        >>> cis = CISystem.objects.create(url='http://test')
        >>> job = cis.jobs.create(name='job')
        >>> rr1 = JobResult(job=job, result='OK', build_id=1)
        >>> rr2 = JobResult(job=job, result='OK', build_id=2)
        >>> rr1 == rr2
        True
        >>> rr3 =  JobResult(job=job, result='FAILED', build_id=3)
        >>> rr1 == rr3
        False
        """
        if isinstance(other, self.__class__):
            return all(getattr(self, name) == getattr(other, name) for name in ['job', 'result'])
        return False

    @property
    def url(self):
        return '%s/view/%s/%s' % (self.job.ci_system.url, self.job.name, self.build_id)

    def __repr__(self):
        return "<JobResult: %s result %s>" % (self.url, self.result)


class ViewResult(BaseModel):
    view = models.ForeignKey(View, related_name='results')
    result = models.CharField(max_length=10, default='SKIPPED')

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return all(getattr(self, name) == getattr(other, name) for name in ['view', 'result'])
        return False

    @property
    def url(self):
        return '%s/view/%s/%s' % (self.job.ci_system.url, self.job.name, self.build_id)

    def __repr__(self):
        return "<ViewResult: %s result %s>" % (self.url, self.result)


class CIStatus(BaseModel):
    """Status of CI Systems"""
    ci_system = models.ForeignKey(CISystem, related_name='statuses')
    jobs_results = models.ManyToManyField(JobResult)
    views_results = models.ManyToManyField(ViewResult)
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
    jobs_results = models.ManyToManyField(JobResult)


# Signals
def post_save_status(sender, instance, **kwargs):
    for i in instance.jobs_results_list:
        instance.jobs_results.add(i)


post_save.connect(post_save_status, sender=CIStatus)
post_save.connect(post_save_status, sender=ProductStatus)
