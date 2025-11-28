from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password

from .models import (
    User,
    Role,
    CustomPermission,
    UserGroup,
    Notification,
    UserActivityLog,
    validar_rut
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

    # Relación Apoderado → Estudiantes y viceversa
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

    # ---------------------------------------------------------
    # MÉTODOS DE RELACIÓN
    # ---------------------------------------------------------

    def get_alumnos(self, obj):
        """Lista de alumnos asociados a un apoderado."""
        if obj.role and obj.role.code == "APODERADO":
            return [
                {
                    "id": u.id,
                    "name": f"{u.first_name} {u.last_name}",
                    "rut": u.rut,
                }
                for u in obj.alumnos.all()
            ]
        return []

    def get_apoderados(self, obj):
        """Lista de apoderados asociados al alumno."""
        if obj.role and obj.role.code == "ALUMNO":
            return [
                {
                    "id": u.id,
                    "name": f"{u.first_name} {u.last_name}",
                    "rut": u.rut,
                }
                for u in obj.apoderados.all()
            ]
        return []




# ============================================================
#  USER CREATE / UPDATE SERIALIZER
# ============================================================

class UserCreateSerializer(serializers.ModelSerializer):

    # Contraseña al crear usuario
    password = serializers.CharField(write_only=True, required=True)

    # IDs relacionales
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


    # =======================================================
    #  VALIDACIONES
    # =======================================================

    def validate_email(self, value):
        return value.lower().strip()

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate_role_id(self, value):
        if not Role.objects.filter(id=value).exists():
            raise serializers.ValidationError("El rol seleccionado no existe.")
        return value

    def validate(self, data):
        """
        Validaciones generales:
        - RUT según rol
        - Relaciones apoderado/alumno
        """
        role = Role.objects.filter(id=data.get('role_id')).first()

        rut = data.get('rut')
        
        # A) Validación de RUT según rol
        if role and role.code in ("ALUMNO", "APODERADO"):
            if not rut:
                raise serializers.ValidationError({"rut": "El RUT es obligatorio para alumnos y apoderados."})

            rut_norm = rut.replace(".", "").replace("-", "").upper().strip()
            if not validar_rut(rut_norm):
                raise serializers.ValidationError({"rut": "El RUT ingresado no es válido."})

        # B) No permitir asignación de sí mismo como apoderado o alumno
        if data.get("alumno_ids") and data.get("apoderado_ids"):
            raise serializers.ValidationError("Un usuario no puede ser alumno y apoderado simultáneamente.")

        return data




    # =======================================================
    #  CREATE
    # =======================================================

    def create(self, validated_data):

        # Extraer valores relacionales
        group_ids = validated_data.pop('group_ids', [])
        permission_ids = validated_data.pop('permission_ids', [])
        apoderado_ids = validated_data.pop('apoderado_ids', [])
        alumno_ids = validated_data.pop('alumno_ids', [])

        role_id = validated_data.pop('role_id')

        # Normalizar email
        if validated_data.get('email'):
            validated_data['email'] = validated_data['email'].lower().strip()

        # Crear usuario
        user = User(**validated_data)
        user.role_id = role_id
        user.set_password(validated_data['password'])
        user.save()

        # Asignar grupos institucionales
        if group_ids:
            user.groups_institutional.set(UserGroup.objects.filter(id__in=group_ids))

        # Permisos personalizados
        if permission_ids:
            user.extra_permissions.set(CustomPermission.objects.filter(id__in=permission_ids))

        # Relación apoderado → alumno
        if user.role.code == "APODERADO":
            students = User.objects.filter(id__in=alumno_ids)
            user.alumnos.set(students)

        if user.role.code == "ALUMNO":
            apoderados = User.objects.filter(id__in=apoderado_ids)
            user.apoderados.set(apoderados)

        return user




    # =======================================================
    #  UPDATE
    # =======================================================

    def update(self, instance, validated_data):

        # Extraer relaciones
        group_ids = validated_data.pop('group_ids', None)
        permission_ids = validated_data.pop('permission_ids', None)
        apoderado_ids = validated_data.pop('apoderado_ids', None)
        alumno_ids = validated_data.pop('alumno_ids', None)
        role_id = validated_data.pop('role_id', None)

        # Normalizacion email
        if validated_data.get('email'):
            validated_data['email'] = validated_data['email'].lower().strip()

        # Actualizar datos simples
        for attr, value in validated_data.items():
            if attr == "password":
                instance.set_password(value)
            else:
                setattr(instance, attr, value)

        if role_id:
            instance.role_id = role_id

        instance.save()

        # Grupos
        if group_ids is not None:
            instance.groups_institutional.set(UserGroup.objects.filter(id__in=group_ids))

        # Permisos extra
        if permission_ids is not None:
            instance.extra_permissions.set(CustomPermission.objects.filter(id__in=permission_ids))

        # Relaciones apoderado–alumno
        if instance.role.code == "APODERADO" and alumno_ids is not None:
            instance.alumnos.set(User.objects.filter(id__in=alumno_ids))

        if instance.role.code == "ALUMNO" and apoderado_ids is not None:
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
