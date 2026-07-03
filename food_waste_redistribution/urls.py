"""
URL configuration for food_waste_redistribution project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path('accounts/login/', RedirectView.as_view(pattern_name='accounts:login', permanent=True)),
    path('', include('accounts.urls', namespace='accounts')),
    path('donor/', include('donor.urls', namespace='donor')),
    path('adminpanel/', include('adminpanel.urls', namespace='adminpanel')),
    path('receiver/', include('receiver.urls', namespace='receiver')),
    path('chat/', include('chat.urls', namespace='chat')),
    path('driver/', include('driver.urls', namespace='driver')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/', include('allauth.urls')),
    path('how-it-works/', views.how_it_works, name='how_it_works'),
    path('faqs/', views.faqs, name='faqs'),
    path('about-us/', views.about_us, name='about_us'),
    path('contact-sales/', views.contact_sales, name='contact_sales'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('compliance/', views.compliance_center, name='compliance'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
