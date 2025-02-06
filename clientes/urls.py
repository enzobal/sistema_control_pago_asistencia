from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('index', views.index, name='index'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),  # Redirige al home después de cerrar sesión
    path('registro/', views.registro_usuario, name='registro_usuario'),
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('perfil/', views.perfil, name='perfil'),
    path('editar_perfil/', views.editar_perfil, name='editar_perfil'),
    path('completar_perfil/', views.completar_perfil, name='completar_perfil'),
    path('', views.home, name='home'),
    path('clientes/', views.listar_clientes, name='listar_clientes'),
    path('clientes/nuevo/', views.crear_cliente, name='crear_cliente'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('eliminar_asistencia/<int:asistencia_id>/', views.eliminar_asistencia, name='eliminar_asistencia'),
    path('inactivos/', views.listar_inactivos, name='listar_inactivos'),
    
    path('asistencias/', views.listar_asistencias, name='listar_asistencias'),
    path('asistencias/nueva/', views.crear_asistencia, name='crear_asistencia'),
    path('asistencias/editar/<int:id>/', views.editar_asistencia, name='editar_asistencia'),
    path('pagos/', views.listar_pagos, name='listar_pagos'),
    path('pagos/nuevo/', views.crear_pago, name='crear_pago'),
    path('eliminar_pago/<int:id>/', views.eliminar_pago, name='eliminar_pago'),
    # path('pagos/editar/<int:id>/', views.editar_pago, name='editar_pago'),
    path('recaudacion/', views.recaudacion_view, name='recaudacion'),
    path('editar_pago/<int:id>/', views.editar_pago, name='editar_pago'),
    path('eliminar_nota/<int:nota_id>/', views.eliminar_nota, name='eliminar_nota'),
    path('editar/<int:cliente_id>/', views.editar_cliente, name='editar_cliente'),
    path('eliminar/<int:cliente_id>/', views.eliminar_cliente, name='eliminar_cliente'),
    path("escanear_qr/", views.escanear_qr, name="escanear_qr"),
    path('registrar_asistencia_qr/', views.registrar_asistencia_qr, name='registrar_asistencia_qr'),
    path('generar_qr/<int:cliente_id>/', views.generar_qr, name='generar_qr'),

]