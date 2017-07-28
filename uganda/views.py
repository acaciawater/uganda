'''
Created on Jul 27, 2017

@author: theo
'''

from acacia.data.views import ProjectDetailView
from acacia.data.models import Project
from django.shortcuts import get_object_or_404
class HomeView(ProjectDetailView):
    template_name = 'home.html'

    def get_object(self):
        return get_object_or_404(Project,pk=1)
    