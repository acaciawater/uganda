'''
Created on Aug 2, 2017

@author: theo
'''

from django.contrib import admin
from uganda.models import Sequence

@admin.register(Sequence)
class OrderAdmin(admin.ModelAdmin):
    model = Sequence
    list_display = ('location','order')
    search_fields = ('location__name',)
    