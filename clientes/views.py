
from .models import Cliente, Asistencia, Pago
from .forms import ClienteForm, AsistenciaForm, PagoForm
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from .forms import ClienteForm
from django.shortcuts import render, redirect, get_object_or_404


from django.contrib.auth.forms import UserCreationForm
from datetime import datetime

from .forms import RegistroUsuarioForm
from django.contrib import messages


def index(request):
    return render(request, 'index.html')

def registro_usuario(request):
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Registro exitoso. ¡Ahora puedes iniciar sesión!")
            return redirect('home')
    else:
        form = RegistroUsuarioForm()
    return render(request, 'clientes/registro_usuario.html', {'form': form})


# perfildel usuario


from django.shortcuts import redirect



@login_required
def perfil(request):
    try:
        cliente = Cliente.objects.get(user=request.user)
    except Cliente.DoesNotExist:
        return redirect('completar_perfil')  # Redirigir a una vista para completar el perfil
    
    return render(request, 'clientes/perfil.html', {'cliente': cliente})



# para editar el perfil
from django.shortcuts import render, redirect
from .forms import ClienteForm


@login_required
def editar_perfil(request, cliente_id=None):
    """
    Permite editar el perfil del cliente. 
    - Los usuarios solo pueden editar su propio perfil.
    - Los administradores pueden editar el perfil de cualquier cliente.
    """
    if cliente_id and request.user.is_staff:
        cliente = Cliente.objects.get(id=cliente_id)
    else:
        try:
            cliente = request.user.cliente
        except Cliente.DoesNotExist:
            cliente = Cliente(user=request.user)  # Crear un nuevo Cliente si no existe

    if request.method == 'POST':
        form = ClienteForm(request.POST, request.FILES, instance=cliente)
        if form.is_valid():
            form.save()
            return redirect('listar_clientes' if request.user.is_staff else 'perfil')
    else:
        form = ClienteForm(instance=cliente)

    return render(request, 'clientes/editar_perfil.html', {'form': form})


from django.shortcuts import get_object_or_404, redirect, render

from .forms import ClienteForm

@login_required
def editar_cliente(request, cliente_id=None):
    """
    Permite al administrador editar cualquier cliente.
    Los usuarios normales solo pueden editar su propio perfil.
    """
    # Determinar el cliente a editar
    if cliente_id and request.user.is_staff:  # Si es administrador y se pasa un cliente_id
        cliente = get_object_or_404(Cliente, id=cliente_id)
    elif not cliente_id:  # Si no hay cliente_id, es el propio usuario
        try:
            cliente = request.user.cliente
        except Cliente.DoesNotExist:
            return redirect('perfil')  # Redirigir si el cliente no existe
    else:  # Si no es administrador y trata de editar otro cliente
        return redirect('perfil')

    # Manejar formulario
    if request.method == 'POST':
        form = ClienteForm(request.POST, request.FILES, instance=cliente)
        if form.is_valid():
            form.save()
            return redirect('listar_clientes' if request.user.is_staff else 'perfil')
    else:
        form = ClienteForm(instance=cliente)

    return render(request, 'clientes/editar_cliente.html', {'form': form, 'cliente': cliente})





# cpmpletar el perfil si no lo tiene
from django.shortcuts import render, redirect
from .forms import ClienteForm  # Asumiendo que tienes un formulario para el modelo Cliente

@login_required
def completar_perfil(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save(commit=False)
            cliente.user = request.user
            cliente.save()
            return redirect('perfil')
    else:
        form = ClienteForm()
    
    return render(request, 'clientes/completar_perfil.html', {'form': form})


from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Cliente  # Asegúrate de importar tu modelo Cliente

@login_required
def home(request):
    cliente = None
    if hasattr(request.user, 'cliente'):  # Verifica si el usuario tiene un cliente asociado
        cliente = request.user.cliente

    return render(request, "clientes/home.html", {"cliente": cliente})

# def home(request):
#     cliente = None
#     if hasattr(request.user, 'cliente'): 
#         cliente = request.user.cliente

#     return render(request, "home.html", {"cliente": cliente})





@login_required
def listar_clientes(request):
    if request.user.is_staff:
        clientes = Cliente.objects.all()
    else:
        clientes = Cliente.objects.filter(user=request.user)

    # Calcular estado de membresía para cada cliente
    for cliente in clientes:
        cliente.membresia_vencida = cliente.membresia_vencida()

    return render(request, 'clientes/listar_clientes.html', {'clientes': clientes})


# clientes inactivos
from django.db.models import Subquery, Exists, OuterRef, Q
from datetime import timedelta
from django.utils.timezone import now

def listar_inactivos(request):
    hoy = now().date()
    hace_dos_meses = hoy - timedelta(days=60)
    hace_un_mes = hoy - timedelta(days=30)

    ultima_asistencia_subquery = Asistencia.objects.filter(
        cliente=OuterRef('pk')
    ).order_by('-fecha').values('fecha')[:1]

    clientes_con_ultima_asistencia = Cliente.objects.annotate(
        ultima_asistencia=Subquery(ultima_asistencia_subquery)
    )

    clientes_sin_pago = Cliente.objects.filter(
        ~Exists(Pago.objects.filter(cliente=OuterRef('pk'), fecha_pago__gte=hace_dos_meses))
    )

    clientes_sin_asistencia = clientes_con_ultima_asistencia.filter(
        Q(ultima_asistencia__isnull=True) | 
        Q(ultima_asistencia__lt=hace_un_mes)
    )

    clientes_inactivos = (clientes_sin_pago | clientes_sin_asistencia).distinct()

    # Preparando el motivo de inactividad para cada cliente con el tiempo sin pagar y sin asistir
    inactividad_por_pago = {}
    inactividad_por_asistencia = {}

    for cliente in clientes_sin_pago:
        ultima_pago = Pago.objects.filter(cliente=cliente).order_by('-fecha_pago').first()
        if ultima_pago:
            tiempo_sin_pagar = hoy - ultima_pago.fecha_pago
            inactividad_por_pago[cliente.id] = f'No pagó la cuota en {tiempo_sin_pagar.days} días'
        else:
            inactividad_por_pago[cliente.id] = 'No pagó la cuota en más de 60 días'

    for cliente in clientes_sin_asistencia:
        ultima_asistencia = Asistencia.objects.filter(cliente=cliente).order_by('-fecha').first()
        if ultima_asistencia:
            tiempo_sin_asistir = hoy - ultima_asistencia.fecha
            inactividad_por_asistencia[cliente.id] = f'No asistió al gimnasio en {tiempo_sin_asistir.days} días'
        else:
            inactividad_por_asistencia[cliente.id] = 'No asistió al gimnasio en más de 30 días'

    for cliente in clientes_inactivos:
        motivo = []
        if cliente.id in inactividad_por_pago:
            motivo.append(inactividad_por_pago[cliente.id])
        if cliente.id in inactividad_por_asistencia:
            motivo.append(inactividad_por_asistencia[cliente.id])

        # Añadir el motivo de inactividad al cliente
        cliente.motivo_inactividad = " y ".join(motivo) if len(motivo) > 1 else motivo[0]

    return render(request, 'clientes/inactivos.html', {
        'clientes_inactivos': clientes_inactivos
    })








@user_passes_test(lambda u: u.is_staff)
def crear_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('listar_clientes')
    else:
        form = ClienteForm()
    return render(request, 'clientes/crear_cliente.html', {'form': form})


from django.shortcuts import get_object_or_404

@login_required
def eliminar_cliente(request, cliente_id):
    """
    Permite al administrador eliminar un cliente.
    """
    if not request.user.is_staff:
        return redirect('home')

    cliente = get_object_or_404(Cliente, id=cliente_id)

    if request.method == 'POST':
        cliente.user.delete()  # Eliminar el usuario asociado
        cliente.delete()  # Eliminar el cliente
        return redirect('listar_clientes')

    return render(request, 'clientes/eliminar_cliente.html', {'cliente': cliente})


from django.db.models import Count
from datetime import date
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator  # Importamos Paginator
import logging
from .models import Asistencia
from clientes.models import Cliente

logger = logging.getLogger(__name__)

@login_required
def listar_asistencias(request):
    hoy = date.today()  # Fecha actual
    page_number = request.GET.get('page', 1)  # Número de página desde la URL

    if request.user.is_staff:
        asistencias = Asistencia.objects.all().order_by('-fecha')
        asistencia_hoy = None  # Los administradores no tienen asistencia propia
    else:
        try:
            cliente_actual = request.user.cliente
        except Cliente.DoesNotExist:
            logger.error(f"Cliente no encontrado para el usuario: {request.user.username}")
            return redirect('error_page')

        asistencias = Asistencia.objects.filter(cliente=cliente_actual).order_by('-fecha')
        asistencia_hoy = Asistencia.objects.filter(cliente=cliente_actual, fecha=hoy).first()

    # 🔹 Aplicar paginación (20 asistencias por página)
    paginator = Paginator(asistencias, 20)
    asistencias_paginadas = paginator.get_page(page_number)

    # 🔹 Agrupar asistencias por mes y día
    asistencias_por_mes = {}
    for asistencia in asistencias_paginadas:
        mes_anio = asistencia.fecha.strftime('%Y-%m')
        dia = asistencia.fecha.strftime('%d %B %Y')

        if mes_anio not in asistencias_por_mes:
            asistencias_por_mes[mes_anio] = {}

        if dia not in asistencias_por_mes[mes_anio]:
            asistencias_por_mes[mes_anio][dia] = []

        asistencias_por_mes[mes_anio][dia].append(asistencia)

    # 🔹 Resumen de asistencias mensuales
    if request.user.is_staff:
        asistencias_mensuales = Asistencia.objects.filter(presente=True).values(
            'cliente__nombre', 'cliente__apellido', 'fecha__month', 'fecha__year'
        ).annotate(total_asistencias=Count('id'))
    else:
        asistencias_mensuales = Asistencia.objects.filter(
            cliente=cliente_actual, presente=True
        ).values('cliente__nombre', 'cliente__apellido', 'fecha__month', 'fecha__year').annotate(total_asistencias=Count('id'))

    return render(request, 'clientes/listar_asistencias.html', {
        'asistencias_por_mes': asistencias_por_mes,
        'asistencias_mensuales': asistencias_mensuales,
        'asistencia_hoy': asistencia_hoy,
        'hoy': hoy,
        'asistencias_paginadas': asistencias_paginadas
    })




from django.shortcuts import render, redirect
from .forms import AsistenciaForm
from django.contrib.auth.decorators import login_required

@login_required
def crear_asistencia(request):
    if request.method == 'POST':
        form = AsistenciaForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('listar_asistencias')
    else:
        form = AsistenciaForm(user=request.user)
    return render(request, 'clientes/crear_asistencia.html', {'form': form})





from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from .models import Pago, Nota  # Nota debe estar correctamente definida

@login_required
def listar_pagos(request):
    # Obtenemos la consulta de búsqueda si existe
    query = request.GET.get('q')

    # Verificamos si el usuario es administrador
    if request.user.is_staff:  # Administradores ven todos los pagos
        if query:
            pagos = Pago.objects.filter(
                Q(fecha_pago__icontains=query) | 
                Q(cliente__nombre__icontains=query) |
                Q(cliente__apellido__icontains=query) |
                Q(importe__icontains=query)
            ).order_by('-fecha_pago')
        else:
            pagos = Pago.objects.order_by('-fecha_pago')
    else:  # Usuarios normales ven solo sus pagos
        if query:
            pagos = Pago.objects.filter(
                Q(fecha_pago__icontains=query) | 
                Q(importe__icontains=query),
                cliente__user=request.user  # Relación entre Cliente y User
            ).order_by('-fecha_pago')
        else:
            pagos = Pago.objects.filter(cliente__user=request.user).order_by('-fecha_pago')

    # Gestionamos las notas
    notas = Nota.objects.all()  # Verifica que el modelo Nota esté definido correctamente

    if request.method == "POST":
        if 'contenido' in request.POST:  # Agregar nueva nota
            contenido = request.POST['contenido']
            Nota.objects.create(contenido=contenido)
        elif 'nota_id' in request.POST:  # Eliminar una nota
            nota_id = request.POST['nota_id']
            Nota.objects.filter(id=nota_id).delete()

        return redirect('listar_pagos')

    return render(request, 'clientes/listar_pagos.html', {'pagos': pagos, 'notas': notas})



from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import get_object_or_404

# Verifica que el usuario sea administrador
def admin_required(user):
    return user.is_staff

@user_passes_test(admin_required)
def eliminar_pago(request, id):
    pago = get_object_or_404(Pago, id=id)
    pago.delete()
    return redirect('listar_pagos')


def crear_pago(request):
    if request.method == 'POST':
        form = PagoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('listar_pagos')
    else:
        form = PagoForm()
    return render(request, 'clientes/crear_pago.html', {'form': form})

from django.contrib.auth.decorators import login_required, user_passes_test

def is_admin(user):
    return user.is_staff

@login_required
def editar_asistencia(request, id):
    asistencia = Asistencia.objects.get(id=id)
    if request.user.is_staff or asistencia.cliente.user == request.user:
        form = AsistenciaForm(request.POST or None, instance=asistencia, user=request.user)
        if request.method == 'POST' and form.is_valid():
            form.save()
            return redirect('listar_asistencias')
    else:
        return redirect('error_page')  # Redirigir o mostrar un mensaje si el usuario no está autorizado
    return render(request, 'clientes/editar_asistencia.html', {'form': form})



from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def editar_pago(request, id):
    pago = get_object_or_404(Pago, id=id)

    if request.method == "POST":
        form = PagoForm(request.POST, instance=pago)
        if form.is_valid():
            form.save()
            messages.success(request, "Pago actualizado correctamente.")
            return redirect('listar_pagos')
    else:
        form = PagoForm(instance=pago)

    return render(request, 'clientes/editar_pago.html', {'form': form, 'pago': pago})





@receiver(post_save, sender=Asistencia)
def actualizar_asistencia_mensual(sender, instance, **kwargs):
    mes_actual = instance.fecha.month
    anio_actual = instance.fecha.year

    # Contar las asistencias del cliente en el mes actual
    total_asistencias = Asistencia.objects.filter(
        cliente=instance.cliente,
        presente=True,
        fecha__year=anio_actual,
        fecha__month=mes_actual
    ).count()

    # Actualizar todas las instancias del mes actual con el nuevo total
    Asistencia.objects.filter(
        cliente=instance.cliente,
        fecha__year=anio_actual,
        fecha__month=mes_actual
    ).update(asistencia_mensual=total_asistencias)

# vista para calculo de recaudacion anual y mensual
from django.shortcuts import render
from django.db.models import Sum
from .models import Pago
from django.contrib.auth.decorators import user_passes_test
import datetime

def is_admin(user):
    return user.is_staff

@user_passes_test(is_admin)
def recaudacion_view(request):
    import datetime
    hoy = datetime.date.today()
    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    mes_actual = meses[hoy.month - 1]
    año_actual = hoy.year

    # Obtener recaudación total para el mes y el año
    recaudacion_mes = Pago.objects.filter(fecha_pago__year=hoy.year, fecha_pago__month=hoy.month).aggregate(Sum('importe'))['importe__sum'] or 0
    recaudacion_anual = Pago.objects.filter(fecha_pago__year=hoy.year).aggregate(Sum('importe'))['importe__sum'] or 0

    # Obtener pagos por cliente para el mes
    pagos_mes = Pago.objects.filter(fecha_pago__year=hoy.year, fecha_pago__month=hoy.month).order_by('fecha_pago')

    # Obtener pagos por cliente para el año
    pagos_anual = Pago.objects.filter(fecha_pago__year=hoy.year).order_by('fecha_pago')

    # Obtener la recaudación y pagos detallados por cada mes del año
    recaudacion_por_mes = {}
    for i in range(1, 13):
        mes_nombre = meses[i - 1]
        pagos_mes_actual = Pago.objects.filter(fecha_pago__year=hoy.year, fecha_pago__month=i)

        # Calcular el total de ingresos para ese mes
        total_mes = pagos_mes_actual.aggregate(Sum('importe'))['importe__sum'] or 0

        # Guardar en el diccionario el total y los pagos detallados
        recaudacion_por_mes[mes_nombre] = {
            'total': total_mes,
            'pagos': pagos_mes_actual  # Lista de pagos del mes con cliente e importe
        }

    context = {
        'recaudacion_mes': recaudacion_mes,
        'recaudacion_anual': recaudacion_anual,
        'pagos_mes': pagos_mes,
        'pagos_anual': pagos_anual,
        'mes_actual': mes_actual,
        'año_actual': año_actual,
        'recaudacion_por_mes': recaudacion_por_mes,  # Se enviará a la plantilla
    }

    return render(request, 'clientes/recaudacion.html', context)

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@login_required
def eliminar_nota(request, nota_id):
    if request.user.is_staff:
        try:
            nota = Nota.objects.get(id=nota_id)
            nota.delete()
            return JsonResponse({'success': True})
        except Nota.DoesNotExist:
            return JsonResponse({'success': False})
    return JsonResponse({'success': False})

import qrcode
from io import BytesIO
import base64
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Cliente

# ✅ Generar QR para un cliente con datos formateados
def generar_qr(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)

    # 📌 Información que se guardará en el código QR
    qr_data = f"ID:{cliente.id}\nNombre:{cliente.nombre}\nApellido:{cliente.apellido}\nCelular:{cliente.numero_celular}"

    # ✅ Generar el QR con los datos formateados
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)

    # ✅ Crear imagen del QR
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    # ✅ Convertir a base64 para mostrar en la plantilla
    qr_code_url = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode('utf-8')}"

    return render(request, 'qr_cliente.html', {'cliente': cliente, 'qr_code_url': qr_code_url})

# ✅ Vista para escanear QR
def escanear_qr(request):
    return render(request, "escanear_qr.html")


from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse
import json
from django.utils.timezone import now
from .models import Cliente, Asistencia

@csrf_exempt

def registrar_asistencia_qr(request):
    try:
        # Cargar los datos JSON del cuerpo de la solicitud
        data = json.loads(request.body)
        cliente_id = data.get("cliente_id")

        if not cliente_id:
            return JsonResponse({"error": "No se recibió un ID de cliente válido"}, status=400)

        # Extraer solo el número si cliente_id es una URL
        if "http" in cliente_id:
            cliente_id = cliente_id.rstrip("/").split("/")[-1]

        cliente_id = int(cliente_id)  # Convertir a entero
        cliente = Cliente.objects.get(id=cliente_id)

        # Registrar asistencia
        asistencia, created = Asistencia.objects.get_or_create(
            cliente=cliente,
            fecha=now().date(),
            defaults={"presente": True}
        )

        if not created:
            asistencia.presente = True
            asistencia.save()

        return JsonResponse({"success": f"Asistencia registrada para {cliente.nombre}"})

    except Cliente.DoesNotExist:
        return JsonResponse({"error": "Cliente no encontrado"}, status=404)
    except ValueError:
        return JsonResponse({"error": "Formato de ID inválido"}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Error en el formato de datos"}, status=400)
    
    
# para datos estadisticos
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum
from datetime import date


# Verifica si el usuario es admin
def es_admin(user):
    return user.is_superuser

@login_required
@user_passes_test(es_admin)
def dashboard(request):
    total_clientes = Cliente.objects.count()
    presentes_hoy = Asistencia.objects.filter(fecha=date.today(), presente=True).count()
    ausentes_hoy = total_clientes - presentes_hoy
    total_recaudado = Pago.objects.aggregate(total=Sum('importe'))['total'] or 0

    # Cálculo del porcentaje de asistencia
    porcentaje_presentes = (presentes_hoy / total_clientes * 100) if total_clientes > 0 else 0

    context = {
        "total_clientes": total_clientes,
        "presentes_hoy": presentes_hoy,
        "ausentes_hoy": ausentes_hoy,
        "total_recaudado": total_recaudado,
        "porcentaje_presentes": round(porcentaje_presentes, 2)
    }

    return render(request, "dashboard.html", context)


from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import user_passes_test

@login_required
@user_passes_test(lambda u: u.is_staff)  # Solo administradores pueden eliminar
def eliminar_asistencia(request, asistencia_id):
    asistencia = get_object_or_404(Asistencia, id=asistencia_id)
    asistencia.delete()
    return redirect('listar_asistencias')  # Redirige a la lista de asistencias



# superadmin sebas, pirueee@gmail.com,sebas2025