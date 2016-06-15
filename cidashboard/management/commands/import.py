from django.core.management.base import BaseCommand, CommandError
from cidashboard.views import _import_cfg
import yaml


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('config', nargs=1, type=str)

    def handle(self, *args, **options):
        f = open(options['config'][0])
        config = yaml.load(f)
        _import_cfg(config)
