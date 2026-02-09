from django.views.generic import TemplateView

class EmotionsView(TemplateView):
    template_name = 'diario/emotions.html'
