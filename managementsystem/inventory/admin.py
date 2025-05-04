from django.contrib import admin
from django.core.exceptions import ValidationError
from .models import CustomUser, Store, Manager, Staff, Product, Category
from django.contrib.auth.admin import UserAdmin


# Customizing the User Admin
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('id', 'username', 'email', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password', 'role')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'role', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )
    search_fields = ('username', 'email')
    ordering = ('username',)

    def save_model(self, request, obj, form, change):
        is_new = obj._state.adding  # Corrected line
        super().save_model(request, obj, form, change)

        if is_new:
            if obj.role == 'manager':
                Manager.objects.get_or_create(user=obj)
            elif obj.role == 'staff':
                Staff.objects.get_or_create(user=obj)



# Admins for other models
@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    """Admin panel customization for Store model."""
    list_display = ("id" ,"name", "location", "phone_number", "email", "manager", "created_at")
    list_filter = ("location", "manager")
    search_fields = ("name", "location", "manager__username")
    ordering = ("name",)

    def save_model(self, request, obj, form, change):
        """Override save_model to ensure manager role validation and store assignment."""
        # Ensure only users with the role 'manager' can be assigned as store manager
        if obj.manager:
            if obj.manager.role != 'manager':
                raise ValidationError("Only users with the 'manager' role can be assigned as a store manager.")

            # Ensure the user is not already a manager for another store
            if Manager.objects.filter(user=obj.manager).exclude(store=obj).exists():
                raise ValidationError(f"{obj.manager.username} is already assigned as a manager in another store.")

        # Save the store first
        super().save_model(request, obj, form, change)

        # Ensure manager entry in the Manager table is created (if manager exists)
        if obj.manager:
            # Check if a manager already exists for this store
            manager, created = Manager.objects.get_or_create(user=obj.manager, store=obj)
            if not created:
                # If manager already exists, update the store assignment if needed
                manager.store = obj
                manager.save()


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'stock', 'store', 'category', 'created_at', 'created_by', 'updated_by')
    list_filter = ('store', 'category')
    search_fields = ('name',)


@admin.register(Manager)
class ManagerAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'store')
    search_fields = ('user__username', 'store__name')


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'store')
    search_fields = ('user__username', 'store__name')


# Register CustomUser separately with its custom admin
admin.site.register(CustomUser, CustomUserAdmin)
