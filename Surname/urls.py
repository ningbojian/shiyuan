from django.urls import path
from django.views.generic import RedirectView

from Surname.views import surnameAction

app_name = 'Surname'
urlpatterns = [
    path('', RedirectView.as_view(url='index'), name='surname'),
    path('index/' , surnameAction.as_view() , name = 'index'),
    path('announce/', surnameAction.announce, name='announce'),
    path('developer/', surnameAction.developer, name='developer'),
    path('information/', surnameAction.information, name='information'),
    path('introduction/', surnameAction.introduction, name='introduction'),
    path('science/', surnameAction.science, name='science'),
    path('search/', surnameAction.search, name='search')

]
