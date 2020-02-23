"""Django admin ui."""
from django.contrib import admin

from organizations.models import Organization


class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("id", "slug")


admin.site.register(Organization, OrganizationAdmin)

