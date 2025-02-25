from django.core.management.base import BaseCommand
from MediAlertServerApp.services import RecordatorioService

class Command(BaseCommand):
    help = 'Genera registros de toma para los próximos días'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=7, help='Número de días para generar registros')

    def handle(self, *args, **options):
        days = options['days']
        registros_creados = RecordatorioService.generate_upcoming_registros(days=days)
        self.stdout.write(self.style.SUCCESS(f'Se han creado {registros_creados} registros de toma'))
