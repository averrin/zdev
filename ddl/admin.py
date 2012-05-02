from django.contrib import admin

from ddl.models import ObjectTypes


class OTypesAdmin(admin.ModelAdmin):
    list_display = ('title', 'sql',)


admin.site.register(ObjectTypes, OTypesAdmin)
