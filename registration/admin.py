from django.contrib import admin

from registration.models import RegistrationProfile, MysqlCreds


class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'activation_key_expired')
    search_fields = ('user__username', 'user__first_name')


admin.site.register(RegistrationProfile, RegistrationAdmin)


class MysqlAdmin(admin.ModelAdmin):
    list_display = ('user', 'db_login',)
    search_fields = ('user__username', 'db_login')


admin.site.register(MysqlCreds, MysqlAdmin)
