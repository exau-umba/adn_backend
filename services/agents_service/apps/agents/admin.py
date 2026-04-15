from django.contrib import admin
from .models import Agent, AgentAvailability, AgentSkill


class AgentSkillInline(admin.TabularInline):
    model = AgentSkill
    extra = 1


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ("id", "full_name", "role", "service_category", "status", "score")
    list_filter = ("status", "service_category", "city")
    search_fields = ("first_name", "last_name", "phone")
    inlines = [AgentSkillInline]


@admin.register(AgentAvailability)
class AgentAvailabilityAdmin(admin.ModelAdmin):
    list_display = ("agent", "full_time", "part_time", "lodged", "non_lodged")
