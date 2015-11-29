from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from django.utils.translation import ugettext_lazy as _

from .forms import AdminUserChangeForm
from .models import Room, User


class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'pinned', 'created')


class UserAdmin(DefaultUserAdmin):
    form = AdminUserChangeForm

    list_display = ('username', 'email', 'is_staff')
    search_fields = ('username', 'email')

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
    )

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('email', 'kredyti', 'level_override', 'motto', 'avatar')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )


admin.site.register(Room, RoomAdmin)
admin.site.register(User, UserAdmin)
