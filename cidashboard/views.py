from django.views.generic import TemplateView
from random import randint
from django.views.decorators.csrf import csrf_exempt

import yaml
from django.http import HttpResponse

from .models import CISystem


class Test(TemplateView):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super(Test, self).get_context_data(**kwargs)

        def j_list():
            return {
                'success': [('job %s' % i, bool(randint(0, 1))) for i in range(randint(3, 10))],
                'fail': [('job %s' % i, bool(randint(0, 1))) for i in range(randint(0, 10))],
            }

        context['cis'] = [
            {'name': 'Product CI'},
            {'name': 'Fuel CI'},
            {'name': 'Packaging CI'},
            {'name': 'MOS Infra CI'},
            {'name': 'Old Stable CI'},
            {'name': 'Patching CI'},
            {'name': 'Plugin CI'}
        ]
        for v in context['cis']:
            v['jobs'] = j_list()
        return context


def _import_cfg(config):
    for jenkins in config['sources']['jenkins']:
        ci_system, ci_created = CISystem.objects.get_or_create(url=jenkins['url'])
        for job_sets in jenkins.get('query', {}).get('jobs', {}):
            param_names = [
                'triggered_by',
                'gerrit_branch',
                'gerrit_refspec',
            ]
            job_config = {
                'change_ci_status': job_sets.get('affect_ci_system', False)
            }
            if 'filter' in job_sets:
                for param in [p for p in param_names if p in job_sets['filter']]:
                    job_config[param] = job_sets['filter'][param]

            if job_config.get('triggered_by') == 'Any':
                del job_config['triggered_by']

            for name in job_sets['names']:
                ci_system.jobs.get_or_create(name=name, **job_config)


@csrf_exempt
def import_cfg(request):
    config = yaml.load(request.FILES['file'].file)
    _import_cfg(config)
    return HttpResponse('Ok')
