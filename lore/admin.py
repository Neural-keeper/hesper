from django.contrib import admin

from .models import CulturalConstellation, SkyCulture, Star

admin.site.register(SkyCulture)
admin.site.register(Star)
admin.site.register(CulturalConstellation)
