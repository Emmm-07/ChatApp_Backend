from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MessageViewset
from . import views

router = DefaultRouter()
router.register('messages',MessageViewset)

urlpatterns = [
    path('api/', include(router.urls)),

    path('login',views.login),
    path('signup',views.signup),
    path('logout',views.logout),
]
    