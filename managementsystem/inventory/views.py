from rest_framework import generics, permissions, status # type: ignore
from rest_framework.response import Response # type: ignore
from rest_framework.views import APIView # type: ignore
from rest_framework.decorators import api_view, permission_classes # type: ignore
from .models import Store, Category, Product, CustomUser, Staff
from .serializers import StoreSerializer, CategorySerializer, ProductSerializer, UserSerializer
from .permissions import IsAdmin, IsManager, IsStaff
from django.shortcuts import render  # type: ignore





def login_page(request):
    return render(request, 'inventory/login.html')


def dashboard_page(request):
    return render(request, 'inventory/dashboard.html')
# --- Store Views (Admin CRUD / Manager View only) ---

class StoreListCreateView(generics.ListCreateAPIView):
    queryset = Store.objects.all()
    serializer_class = StoreSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), IsAdmin()]

class StoreRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Store.objects.all()
    serializer_class = StoreSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), IsAdmin()]

# --- Category Views (Admin and Manager CRUD / Staff Read Only) ---

class CategoryListCreateView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), (IsAdmin | IsManager)()]

class CategoryRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), (IsAdmin | IsManager)()]

# --- Product Views (Admin, Manager, Staff CRUD) ---

class ProductListCreateView(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class ProductRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

# --- Manager Assignment Views (Admin only) ---

class ManagerView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def post(self, request, store_id):
        try:
            store = Store.objects.get(id=store_id)
            user = CustomUser.objects.get(id=request.data['user_id'])
        except (Store.DoesNotExist, CustomUser.DoesNotExist):
            return Response({"detail": "Store or User not found."}, status=status.HTTP_404_NOT_FOUND)

        if user.role != 'manager':
            return Response({"detail": "User must be a manager."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the store already has a manager
        if store.manager:
            return Response({"detail": "This store already has a manager."}, status=status.HTTP_400_BAD_REQUEST)

        store.manager = user
        store.save()
        return Response({"detail": "Manager assigned."}, status=status.HTTP_201_CREATED)

    def delete(self, request, store_id):
        try:
            store = Store.objects.get(id=store_id)
        except Store.DoesNotExist:
            return Response({"detail": "Store not found."}, status=status.HTTP_404_NOT_FOUND)

        if not store.manager:
            return Response({"detail": "No manager assigned."}, status=status.HTTP_400_BAD_REQUEST)

        store.manager = None
        store.save()
        return Response({"detail": "Manager removed."}, status=status.HTTP_204_NO_CONTENT)

    def get(self, request, store_id):
        try:
            store = Store.objects.get(id=store_id)
        except Store.DoesNotExist:
            return Response({"detail": "Store not found."}, status=status.HTTP_404_NOT_FOUND)

        if store.manager:
            return Response({"id": store.manager.id, "username": store.manager.username})
        return Response({"detail": "No manager assigned."})


# --- Staff Assignment Views (Admin only) ---

class StaffView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_store(self, store_id, request):
        try:
            store = Store.objects.get(id=store_id)
        except Store.DoesNotExist:
            return None, Response({"detail": "Store not found."}, status=status.HTTP_404_NOT_FOUND)

        # Only allow admin or the manager of the store
        if request.user.role != 'admin' and store.manager != request.user:
            return None, Response({"detail": "You do not have permission to access this store."}, status=status.HTTP_403_FORBIDDEN)

        return store, None

    def post(self, request, store_id):
        store, error = self.get_store(store_id, request)
        if error:
            return error

        user_id = request.data.get('user_id')
        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        if user.role != 'staff':
            return Response({"detail": "User must be staff."}, status=status.HTTP_400_BAD_REQUEST)

        store.staff.add(user)
        Staff.objects.get_or_create(user=user, defaults={"store": store})
        return Response({"detail": "Staff added."}, status=status.HTTP_201_CREATED)

    def delete(self, request, store_id):
        store, error = self.get_store(store_id, request)
        if error:
            return error

        user_id = request.data.get('user_id')
        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        if user not in store.staff.all():
            return Response({"detail": "User not staff of this store."}, status=status.HTTP_400_BAD_REQUEST)

        store.staff.remove(user)
        Staff.objects.filter(user=user, store=store).update(store=None)
        return Response({"detail": "Staff removed."}, status=status.HTTP_204_NO_CONTENT)

    def get(self, request, store_id):
        store, error = self.get_store(store_id, request)
        if error:
            return error

        staff = store.staff.values('id', 'username', 'email')
        return Response(staff)

    def patch(self, request, store_id):
        """
        Replace all staff with a new list.
        Payload: {"user_ids": [1, 2, 3]}
        """
        store, error = self.get_store(store_id, request)
        if error:
            return error

        user_ids = request.data.get('user_ids', [])
        if not isinstance(user_ids, list):
            return Response({"detail": "user_ids must be a list."}, status=status.HTTP_400_BAD_REQUEST)

        valid_staff = CustomUser.objects.filter(id__in=user_ids, role='staff')

        # Set new staff
        store.staff.set(valid_staff)

        # Sync Staff model
        for user in valid_staff:
            Staff.objects.get_or_create(user=user, defaults={"store": store})
            Staff.objects.filter(user=user).update(store=store)

        # Unassign users not in the list
        Staff.objects.filter(store=store).exclude(user__in=valid_staff).update(store=None)

        return Response({"detail": "Staff updated."}, status=status.HTTP_200_OK)

# --- User Management Views ---

class UserView(generics.ListCreateAPIView, generics.RetrieveUpdateDestroyAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.request.method in ['POST', 'PUT', 'PATCH', 'DELETE', 'GET']:
            return [permissions.IsAuthenticated(), IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        if self.request.user.role == 'manager':
            # Manager sees only users in their store
            store_id = self.kwargs.get('store_id')
            return Store.objects.get(id=store_id).staff.all()
        return CustomUser.objects.all()

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        serializer.save()

    def perform_destroy(self, instance):
        instance.delete()


# --- Authenticated current user ---

@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def me(request):
    user = request.user
    return Response({
        "id": user.id,
        "username": getattr(user, "username", ""),
        "email": getattr(user, "email", ""),
        "role": getattr(user, "role", None),
        "is_active": getattr(user, "is_active", False),
    })
