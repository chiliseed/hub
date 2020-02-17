from django.contrib import admin

from aws_environments.models import Environment, Project, ExecutionLog


class EnvironmentAdmin(admin.ModelAdmin):
    list_display = ("id", "slug", "name", "organization", "status")

    def status(self, obj):
        return obj.last_status.status


class ProjectAdmin(admin.ModelAdmin):
    list_display = ("id", "slug", "name", "organization", "env", "status")

    def status(self, obj):
        return obj.last_status.status

    def env(self, obj):
        return obj.environment.name


class ExecLogAdmin(admin.ModelAdmin):
    list_display = ("id", "slug", "action", "is_success", "created_at", "ended_at", "component", "component_id", "env")
    list_filter = ("action", "is_success", "component")
    search_fields = ("id", "slug", "component_id",)

    def env(self, obj):
        component = obj.get_component_obj()
        if not component:
            return ""
        if obj.component == obj.Components.environment:
            return component.name
        else:
            return component.environment.name


admin.site.register(Environment, EnvironmentAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(ExecutionLog, ExecLogAdmin)
