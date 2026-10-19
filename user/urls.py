from django.urls import path
from django.views.generic import RedirectView

from user.views import UsersAction, getToken

app_name = 'user'
urlpatterns = [
    path('create/', UsersAction.create, name='create'),
    path('vip/', UsersAction.changeVip, name='vip'),
    path('alter/', UsersAction.alter, name='alter'),
    path('getToken/', getToken, name='getToken'),
    path('comment/', UsersAction.comment, name='comment'),
    path('' , RedirectView.as_view(url='index')),
    path('index/' , UsersAction.as_view() , name = 'index'),
    path('log/' , UsersAction.log , name='log'),
    path('login/' , UsersAction.login , name='login'),
    path('register/' , UsersAction.register , name = 'register'),
    path('personal/' , UsersAction.personal , name = 'personal'),
    path('logout/' , UsersAction.logout , name = 'logout')
]
