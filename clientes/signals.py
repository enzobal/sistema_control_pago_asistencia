from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Asistencia, Cliente

@receiver(post_save, sender=Asistencia)
@receiver(post_delete, sender=Asistencia)
def update_asistencia_mensual(sender, instance, **kwargs):
    print("Señal activada")
    cliente = instance.cliente
    mes = instance.fecha.month
    anio = instance.fecha.year
    
    asistencia_mensual = Asistencia.objects.filter(
        cliente=cliente,
        presente=True,
        fecha__month=mes,
        fecha__year=anio
    ).count()

    print(f"Recalculando asistencia mensual: {asistencia_mensual} días para {cliente.nombre}")

    cliente.asistencia_mensual = asistencia_mensual
    cliente.save()

