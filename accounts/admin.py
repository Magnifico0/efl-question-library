from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from accounts.models import Organization,User
# Register your models here.

#firmaların giriş yapacağı kısım 
@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ["name","slug","created_at"] 
    prepopulated_fields = {"slug" : ("name",)}
    search_fields = ["name"]

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (("Rol ve Organizasyon",
                                            { "fields" : ("role", "organization")}),
    )
    list_display = ("username", "first_name", "last_name","role", "organization")
    list_filter = ["role",]
    search_fields = ["username","organization__name"] #__ to reach FK 
