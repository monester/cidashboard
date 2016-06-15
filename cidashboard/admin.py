from django.contrib import admin
from .models import CISystem


class CISystemAdmin(admin.ModelAdmin):
    pass


admin.site.register(CISystem, CISystemAdmin)
