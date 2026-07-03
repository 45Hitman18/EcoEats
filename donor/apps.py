from django.apps import AppConfig


class DonorConfig(AppConfig):
    name = 'donor'
    
    def ready(self):
        import donor.signals  # Import signals to register them
