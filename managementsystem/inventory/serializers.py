from rest_framework import serializers # type: ignore
from .models import Store, Category, Product, Manager, Staff, CustomUser
 # type: ignore

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'role', 'is_staff', 'is_active', 'password']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = CustomUser(**validated_data)
        if password:
            user.set_password(password)
        user.save()

        # Automatically create Manager or Staff
        if user.role == 'manager':
            from .models import Manager
            Manager.objects.create(user=user)
        elif user.role == 'staff':
            from .models import Staff
            Staff.objects.create(user=user)

        return user


class StoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = ['id', 'name', 'location', 'email', 'phone_number', 'manager', 'staff']

    def validate_manager(self, value):
        if value and value.role != 'manager':
            raise serializers.ValidationError("Selected user is not a manager.")
        return value

    def create(self, validated_data):
        staff_users = validated_data.pop('staff', [])
        store = super().create(validated_data)
        store.staff.set(staff_users)
        self._create_or_update_manager_record(store)
        self._create_or_update_staff_records(store, staff_users)
        return store

    def update(self, instance, validated_data):
        staff_users = validated_data.pop('staff', None)
        store = super().update(instance, validated_data)
        if staff_users is not None:
            store.staff.set(staff_users)
        self._create_or_update_manager_record(store)
        self._create_or_update_staff_records(store, store.staff.all())
        return store

    def _create_or_update_manager_record(self, store):
        from .models import Manager
        if store.manager:
            # Remove manager from other store
            Manager.objects.filter(user=store.manager).exclude(store=store).update(store=None)
            manager_obj, _ = Manager.objects.get_or_create(user=store.manager)
            manager_obj.store = store
            manager_obj.save()

    def _create_or_update_staff_records(self, store, staff_users):
        from .models import Staff
        for user in staff_users:
            if user.role != 'staff':
                continue  # skip if not a staff user
            staff_obj, _ = Staff.objects.get_or_create(user=user)
            staff_obj.store = store
            staff_obj.save()
        
        # Optionally remove users who are no longer in this store's staff
        Staff.objects.filter(store=store).exclude(user__in=staff_users).update(store=None)



class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'stock', 'store', 'category', 'created_at', 'created_by', 'updated_by']
        created_by = serializers.StringRelatedField(read_only=True)
        updated_by = serializers.StringRelatedField(read_only=True)


class ManagerSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Manager
        fields = ['id', 'user', 'store']

class StaffSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Staff
        fields = ['id', 'user', 'store']
