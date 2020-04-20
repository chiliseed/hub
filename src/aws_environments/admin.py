from django.contrib import admin

from aws_environments.models import (
    Environment,
    Project,
    ExecutionLog,
    Resource, Service,
    BuildWorker,
)


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


class ServiceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "slug",
        "name",
        "subdomain",
        "project",
        "organization",
        "status",
        "is_deleted",
    )
    list_display_links = ("id", "project", "organization")
    list_filter = ("is_deleted", "last_status__status")
    readonly_fields = (
        "slug",
        "id",
    )

    def organization(self, obj):
        return obj.project.organization

    def status(self, obj):
        return obj.last_status.status


class ExecLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "slug",
        "action",
        "is_success",
        "created_at",
        "ended_at",
        "component",
        "component_id",
        "env",
    )
    list_filter = ("action", "is_success", "component")
    search_fields = (
        "id",
        "slug",
        "component_id",
    )
    readonly_fields = (
        "slug",
        "id",
    )

    def env(self, obj):
        component = obj.get_component_obj()
        if not component:
            return ""
        if obj.component == obj.Components.environment:
            return component.name
        elif obj.component == obj.Components.service:
            return component.project.environment.name
        elif obj.component == obj.Components.build_worker:
            return component.service.project.environment.name
        elif obj.component == obj.Components.deployment:
            return component.service.project.environment.name
        else:
            return component.environment.name


class BuildWorkerAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "slug",
        "organization",
        "service",
        "launched_at",
        "is_ready",
        "is_deleted",
    )
    list_filter = ("is_deleted",)
    search_fields = (
        "id",
        "slug",
    )
    readonly_fields = (
        "slug",
        "id",
    )

    def is_ready(self, obj):
        return obj.instance_id is not None


class ResourceAdmin(admin.ModelAdmin):
    list_display = ("id", "slug", "organization", "environment", "project", "identifier", "kind", "preset", "engine")
    list_filter = ("engine", "preset", "kind")
    search_fields = ("id", "slug", "identifier")
    readonly_fields = ("id", "slug")
    list_display_links = ("id", "project", "organization", "environment")


admin.site.register(Environment, EnvironmentAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(ExecutionLog, ExecLogAdmin)
admin.site.register(Service, ServiceAdmin)
admin.site.register(BuildWorker, BuildWorkerAdmin)
admin.site.register(Resource, ResourceAdmin)
