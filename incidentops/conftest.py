import os
import django
from django.conf import settings

# Configurer Django avant l'exécution des tests
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()
