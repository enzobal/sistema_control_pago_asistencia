from django.db import models
from django.contrib.auth.models import User
from datetime import date
import qrcode
from io import BytesIO
from django.core.files import File

# Create your models here.

class Cliente(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    numero_celular = models.CharField(max_length=15)
    edad = models.IntegerField(default=18)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    enfermedades = models.TextField(blank=True, null=True)
    alergias = models.TextField(blank=True, null=True)
    asistencia_mensual = models.PositiveIntegerField(default=0)
    imagen_perfil = models.ImageField(upload_to='perfil/', null=True, blank=True)
    qr_code = models.ImageField(upload_to='qr_codes/', null=True, blank=True)


    def save(self, *args, **kwargs):
        # Generar el QR con el ID único del cliente
        qr_data = f"{self.id}"  # O puedes usar datos adicionales
        qr_img = qrcode.make(qr_data)

        # Guardar el QR como archivo
        buffer = BytesIO()
        qr_img.save(buffer, format='PNG')
        file_name = f"qr_cliente_{self.id}.png"
        self.qr_code.save(file_name, File(buffer), save=False)

        super().save(*args, **kwargs)

    def membresia_vencida(self):
        """
        Retorna True si no hay pagos activos o la membresía está vencida, False si está activa.
        """
        ultimo_pago = Pago.objects.filter(cliente=self).order_by('-fecha_fin').first()
        if not ultimo_pago or (ultimo_pago.fecha_fin and ultimo_pago.fecha_fin < date.today()):
            return True
        return False
    
    @property
    def email(self):
        return self.user.email if self.user else None

    def __str__(self):
        return f"{self.nombre} {self.apellido}"



from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Cliente

@receiver(post_save, sender=User)
def create_or_update_cliente(sender, instance, created, **kwargs):
    if created:
        # Proporcionar un valor por defecto para 'edad'
        Cliente.objects.create(user=instance, edad=18)  # Reemplaza 18 con el valor que prefieras
    else:
        try:
            instance.cliente.save()
        except Cliente.DoesNotExist:
            Cliente.objects.create(user=instance, edad=18)  # Mismo valor por defecto aquí


from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from clientes.models import Cliente

class Command(BaseCommand):
    help = 'Crear clientes para usuarios existentes que no tengan uno.'

    def handle(self, *args, **kwargs):
        for user in User.objects.all():
            if not hasattr(user, 'cliente'):
                Cliente.objects.create(user=user)
                self.stdout.write(f"Cliente creado para {user.username}")





# asitencia diaria
class Asistencia(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    fecha = models.DateField()
    presente = models.BooleanField(default=False)
    asistencia_mensual = models.PositiveIntegerField(default=0)
    

    def __str__(self):
        return f"{self.cliente} - {self.fecha} - {'Presente' if self.presente else 'Ausente'}"
    

class Pago(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    importe = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_inicio = models.DateField(blank=True, null=True)
    fecha_pago = models.DateField(blank=True, null=True)
    fecha_fin = models.DateField(blank=True, null=True)  # Nuevo campo opcional para almacenar la fecha de fin

    def __str__(self):
        return f"Pago de {self.cliente} por {self.importe} el {self.fecha_pago} inicio {self.fecha_inicio} fin {self.fecha_fin}"

from django.db import models

class Nota(models.Model):
    contenido = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Nota creada el {self.fecha_creacion}"
