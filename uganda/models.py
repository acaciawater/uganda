'''
Created on Aug 2, 2017

@author: theo
'''
from django.db import models
from acacia.data.models import ProjectLocatie

class Sequence(models.Model):
    location = models.OneToOneField(ProjectLocatie)
    order = models.IntegerField(default=1)
    
    def __unicode__(self):
        return unicode(self.location)
    
    class Meta:
        ordering = ('order','location')
