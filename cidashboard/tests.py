from django.test import TestCase
from cidashboard.jenkins.models import get_value
from cidashboard.models import CISystem


class JenkinsApi(TestCase):
    def test_get_result(self):
        builds = [{
            "actions": [{
                "causes": [{
                    "shortDescription": "Started by timer"
                }]
            },
                {
                    "parameters": [{
                        "name": "REFSPEC",
                        "value": "master"
                    }]
                },
            ]
        }]
        self.assertEquals(
            get_value('actions.causes.shortDescription', builds),
            'Started by timer'
        )


class Test(TestCase):
    def main(self):
        self.assertTrue(True)

    # cis = CISystem.objects.create(url='http://test')
    # job = cis.jobs.create(name='job')
    # rr1 = JobResult(job=job, result='OK', build_id=1)
    # rr2 = JobResult(job=job, result='OK', build_id=2)
    # assert rr1 == rr2
    # rr3 =  JobResult(job=job, result='FAILED', build_id=3)
    # assert rr1 != rr3
