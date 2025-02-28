from django.contrib import admin
from .models import Cliente, Asistencia, Pago
from .forms import AsistenciaForm, PagoForm
from django.utils.timezone import now
import calendar
from datetime import date
import locale
from django.utils.timezone import now
import locale
from datetime import date
from django.utils import timezone
# Función para obtener el estado de pago de la cuota del mes
def obtener_pago_cliente(cliente):
    # Obtener el pago correspondiente al mes actual
    pago = Pago.objects.filter(cliente=cliente, fecha_pago__month=now().month, fecha_pago__year=now().year).first()
    if pago:
        return pago.importe  # O cualquier otro campo que desees mostrar, como el estado de pago
    return "No pagado"

# Función para obtener el estado de presencia del cliente hoy
def obtener_estado_presente(cliente):
    # Obtener la asistencia del cliente para la fecha actual
    asistencia = Asistencia.objects.filter(cliente=cliente, fecha=now().date()).first()
    if asistencia:
        return "Presente" if asistencia.presente else "Ausente"
    return "No registrado"

# Configuración del modelo Cliente
@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'apellido', 'obtener_pago', 'obtener_estado_presente', 'asistencia_mensual', 'edad', 'fecha_nacimiento', 'alergias', 'enfermedades','numero_celular')
    search_fields = ('nombre', 'apellido', 'celular')
    
    


    def obtener_pago(self, obj):
    # Configurar la localización para mostrar el mes en español
        try:
            locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')  # Asegúrate de que esta localización esté disponible
        except locale.Error:
            return "Localización no disponible"

    # Obtener el pago más reciente del cliente
        pago = Pago.objects.filter(cliente=obj).order_by('-fecha_pago').first()

        if pago:
        # Calcular el último día del mes de la fecha_inicio
            _, ultimo_dia = calendar.monthrange(pago.fecha_inicio.year, pago.fecha_inicio.month)
            fecha_fin_mes = date(pago.fecha_inicio.year, pago.fecha_inicio.month, ultimo_dia)

        # Formatear el rango de fechas
            rango_fechas = f"Desde {pago.fecha_inicio.strftime('%d de %B de %Y')} hasta {fecha_fin_mes.strftime('%d de %B de %Y')}"

        # Obtener el nombre del mes del pago más reciente
            mes_pagado = pago.fecha_pago.strftime('%B')

            return f"Pago del mes de {mes_pagado}: {pago.importe} ({rango_fechas})"
    
        return "No pagado"

    obtener_pago.short_description = 'Pago del Mes'




    # Función para obtener el estado de presencia del cliente hoy
    def obtener_estado_presente(self, obj):
        return obtener_estado_presente(obj)
    obtener_estado_presente.short_description = 'Presencia del Día'  # Título de la columna
    
    def asistencia_mensual(self, obj):
        # Obtener el nombre del mes actual
        month_name = calendar.month_name[now().month]
        # Contar los días presentes en el mes actual
        dias_presentes = Asistencia.objects.filter(cliente=obj, presente=True, fecha__month=now().month, fecha__year=now().year).count()
        return f"{month_name}: {dias_presentes} días presentes"
    asistencia_mensual.short_description = 'Asistencia del Mes'

# Configuración del modelo Asistencia
@admin.register(Asistencia)
class AsistenciaAdmin(admin.ModelAdmin):
    form = AsistenciaForm
    list_display = ('cliente', 'fecha', 'presente', 'asistencia_mensual')
    list_filter = ('fecha', 'presente')
    search_fields = ('cliente__nombre', 'cliente__apellido')

# Configuración del modelo Pago
@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    form = PagoForm
    list_display = ('cliente', 'fecha_inicio', 'fecha_fin', 'fecha_pago', 'importe')
    list_filter = ('fecha_pago',)
    search_fields = ('cliente__nombre', 'cliente__apellido')

    def save_model(self, request, obj, form, change):
        if not obj.fecha_fin:
            # Calcular el último día del mes de fecha_inicio si no está definido
            _, ultimo_dia = calendar.monthrange(obj.fecha_inicio.year, obj.fecha_inicio.month)
            obj.fecha_fin = date(obj.fecha_inicio.year, obj.fecha_inicio.month, ultimo_dia)
        super().save_model(request, obj, form, change)
        

from django.contrib import admin
from .models import Grupo, Subgrupo, Rutina

@admin.register(Grupo)
class GrupoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'get_clientes')  # Muestra los clientes en la tabla de admin
    filter_horizontal = ('clientes',)  # Facilita la selección de clientes en el admin

@admin.register(Subgrupo)
class SubgrupoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'grupo')

@admin.register(Rutina)
class RutinaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'grupo', 'subgrupo')
