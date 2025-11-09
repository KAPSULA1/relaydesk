"""
Settings Package
Automatically loads the correct settings based on DJANGO_ENV
"""
import os

ENV = os.getenv('DJANGO_ENV', 'dev')

if ENV == 'production':
    from .prod import *
elif ENV == 'dev':
    from .dev import *
else:
    from .dev import *
