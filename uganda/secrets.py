# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '-cw3x)+ro%eks3651g%=8#n8n3wl)ylz&&m%uer^t#due8e-r5'
GOOGLE_MAPS_API_KEY = 'AIzaSyBZoEnkbR2kagMCHyT-CiuBzJOW3bkexBA'
OPENWEATHER_APIKEY = 'cbfee8a09865749b6a3a6781c1acfcca'
WUNDERGROUND_APIKEY = '68673dc753f817a4'

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'uganda',
    },
}

# DEFAULT_FROM_EMAIL = 'noreply@acaciadata.com'
# EMAIL_HOST='acaciadata.com'
# EMAIL_PORT=25
# EMAIL_HOST_USER='webmaster@acaciadata.com'
# EMAIL_HOST_PASSWORD='water123'
# EMAIL_USE_TLS = True

DEFAULT_FROM_EMAIL = 'noreply@acaciadata.com'
EMAIL_HOST='smtp.gmail.com'
EMAIL_PORT=587
EMAIL_HOST_USER='tkleinen@gmail.com'
EMAIL_HOST_PASSWORD='pw4Gmail'
EMAIL_USE_TLS = True
