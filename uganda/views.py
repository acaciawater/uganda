'''
Created on Jul 27, 2017

@author: theo
'''

from acacia.data.views import ProjectDetailView
from acacia.data.models import Project, ProjectLocatie
from django.shortcuts import get_object_or_404
from uganda.helpers import Latest
from django.views.generic import DetailView

class HomeView(ProjectDetailView):
    template_name = 'home.html'

    def get_object(self):
        return get_object_or_404(Project,pk=1)
        
class LatestInfoView(DetailView):
    model = ProjectLocatie
    template_name = 'latest.html'
    
    def get_context_data(self, **kwargs):
        context = super(LatestInfoView, self).get_context_data(**kwargs)
        loc = self.get_object()
        context['info'] = {unicode(m): Latest.info(m) for m in loc.meetlocatie_set.all()}
        return context
