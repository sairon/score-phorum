from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.utils.translation import ugettext_lazy as _

from .forms import AdminUserChangeForm
from .models import Room, User


class AdminRoomChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField(
        help_text=_("Raw passwords are not stored, so there is no way to see this password.")
    )

    class Meta:
        model = Room
        fields = '__all__'

    def clean_password(self):
        return self.initial["password"]


class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'pinned', 'created')
    form = AdminRoomChangeForm


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
