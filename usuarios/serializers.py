from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password

from .models import (
    User,
    Role,
    CustomPermission,
    UserGroup,
    Notification,
    UserActivityLog
)


# ============================================================
#  ROLE SERIALIZER
# ============================================================

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = [
            'id',
            'code',
            'description',
            'hierarchy'
        ]


# ============================================================
#  PERMISOS EXTRA
# ============================================================

class CustomPermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomPermission
        fields = ['id', 'code', 'name', 'description']


# ============================================================
#  GRUPOS INSTITUCIONALES
# ============================================================

class UserGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserGroup
        fields = ['id', 'name', 'description']


# ============================================================
#  USER SERIALIZER (LECTURA)
# ============================================================

class UserSerializer(serializers.ModelSerializer):

    # Serialización anidada
    role = RoleSerializer(read_only=True)
    groups_institutional = UserGroupSerializer(many=True, read_only=True)
    extra_permissions = CustomPermissionSerializer(many=True, read_only=True)

    # Relación Apoderado -> Estudiantes y viceversa
    alumnos = serializers.SerializerMethodField()
    apoderados = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'rut',
            'phone',
            'address',
            'gender',
            'birth_date',
            'role',
            'groups_institutional',
            'extra_permissions',
            'alumnos',
            'apoderados',
            'profile_image',
            'enrollment_year',
            'active',
            'last_login',
            'last_login_ip',
            'created_at',
            'updated_at',
        ]

    def get_alumnos(self, obj):
        """Lista de alumnos asociados a un apoderado."""
        if obj.role and obj.role.code == "APODERADO":
            return [{"id": u.id, "name": f"{u.first_name} {u.last_name}"} for u in obj.alumnos.all()]
        return []

    def get_apoderados(self, obj):
        """Lista de apoderados asociados al alumno."""
        if obj.role and obj.role.code == "ALUMNO":
            return [{"id": u.id, "name": f"{u.first_name} {u.last_name}"} for u in obj.apoderados.all()]
        return []


# ============================================================
#  USER CREATE / UPDATE SERIALIZER
# ============================================================

class UserCreateSerializer(serializers.ModelSerializer):

    # Para crear o modificar la contraseña
    password = serializers.CharField(write_only=True, required=True)

    # Asignaciones directas
    role_id = serializers.IntegerField(write_only=True)
    group_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True
    )
    permission_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True
    )

    # Relación apoderado–alumno
    apoderado_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    alumno_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = User
        fields = [
            'username',
            'password',
            'first_name',
            'last_name',
            'email',
            'rut',
            'phone',
            'address',
            'gender',
            'birth_date',
            'role_id',
            'group_ids',
            'permission_ids',
            'apoderado_ids',
            'alumno_ids',
            'enrollment_year',
            'active',
        ]

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):

        # Extraer datos complejos
        group_ids = validated_data.pop('group_ids', [])
        permission_ids = validated_data.pop('permission_ids', [])
        apoderado_ids = validated_data.pop('apoderado_ids', [])
        alumno_ids = validated_data.pop('alumno_ids', [])

        role_id = validated_data.pop('role_id')

        # Crear usuario
        user = User(**validated_data)
        user.role_id = role_id
        user.set_password(validated_data['password'])
        user.save()

        # Asignar grupos
        if group_ids:
            groups = UserGroup.objects.filter(id__in=group_ids)
            user.groups_institutional.set(groups)

        # Asignar permisos extra
        if permission_ids:
            perms = CustomPermission.objects.filter(id__in=permission_ids)
            user.extra_permissions.set(perms)

        # Relación apoderado ↔ alumno
        if user.role.code == "APODERADO":
            students = User.objects.filter(id__in=alumno_ids)
            user.alumnos.set(students)

        if user.role.code == "ALUMNO":
            apoderados = User.objects.filter(id__in=apoderado_ids)
            user.apoderados.set(apoderados)

        return user

    def update(self, instance, validated_data):

        # Extraer relaciones
        group_ids = validated_data.pop('group_ids', [])
        permission_ids = validated_data.pop('permission_ids', [])
        apoderado_ids = validated_data.pop('apoderado_ids', [])
        alumno_ids = validated_data.pop('alumno_ids', [])

        role_id = validated_data.pop('role_id', None)

        # Actualizar campos simples
        for attr, value in validated_data.items():
            if attr == "password":
                instance.set_password(value)
            else:
                setattr(instance, attr, value)

        if role_id:
            instance.role_id = role_id

        instance.save()

        # Grupos
        if group_ids:
            instance.groups_institutional.set(UserGroup.objects.filter(id__in=group_ids))

        # Permisos
        if permission_ids:
            instance.extra_permissions.set(CustomPermission.objects.filter(id__in=permission_ids))

        # Relación apoderado–alumno
        if instance.role.code == "APODERADO":
            instance.alumnos.set(User.objects.filter(id__in=alumno_ids))

        if instance.role.code == "ALUMNO":
            instance.apoderados.set(User.objects.filter(id__in=apoderado_ids))

        return instance


# ============================================================
#  NOTIFICACIONES
# ============================================================

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'id',
            'title',
            'message',
            'level',
            'is_read',
            'created_at',
            'user',
        ]


# ============================================================
#  AUDITORÍA
# ============================================================

class ActivityLogSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.username')

    class Meta:
        model = UserActivityLog
        fields = [
            'id',
            'user',
            'action',
            'ip_address',
            'user_agent',
            'created_at'
        ]
