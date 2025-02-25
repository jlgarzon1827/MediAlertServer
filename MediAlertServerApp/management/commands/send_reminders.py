from django.core.management.base import BaseCommand
from MediAlertServerApp.services import ReminderNotificationService

class Command(BaseCommand):
    help = 'Envía recordatorios de medicamentos a los usuarios'

    def add_arguments(self, parser):
        parser.add_argument('--minutes', type=int, default=15, help='Minutos antes de la hora programada')

    def handle(self, *args, **options):
        minutes = options['minutes']
        stats = ReminderNotificationService.send_medication_reminders(minutes_before=minutes)
        
        self.stdout.write(self.style.SUCCESS(
            f"Recordatorios enviados: {stats['sent']} exitosos, {stats['failed']} fallidos, "
            f"{stats['no_device']} sin dispositivo (de {stats['total']} totales)"
        ))
