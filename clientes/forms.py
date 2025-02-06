from django import forms
from .models import Cliente, Asistencia, Pago

from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth.models import User

class RegistroUsuarioForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text="Requerido. Introduce un correo válido.")

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nombre', 'apellido', 'numero_celular', 'edad', 'fecha_nacimiento', 'enfermedades', 'alergias', 'imagen_perfil']

class AsistenciaForm(forms.ModelForm):
    class Meta:
        model = Asistencia
        fields = ['cliente', 'fecha', 'presente']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
        }
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(AsistenciaForm, self).__init__(*args, **kwargs)
        if user and not user.is_staff:
            self.fields['cliente'].queryset = Cliente.objects.filter(user=user)

from django.core.exceptions import ValidationError

class PagoForm(forms.ModelForm):
    class Meta:
        model = Pago
        fields = ['cliente', 'importe', 'fecha_inicio','fecha_fin', 'fecha_pago']
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={'type': 'date'}),
            'fecha_fin': forms.DateInput(attrs={'type': 'date'}),
            'fecha_pago': forms.DateInput(attrs={'type': 'date'}),
        }


    def clean_importe(self):
        importe = self.cleaned_data.get('importe')
        if importe <= 0:
            raise ValidationError('El importe debe ser un valor positivo.')
        return importe

    def clean_fecha_pago(self):
        fecha_inicio = self.cleaned_data.get('fecha_inicio')
        fecha_pago = self.cleaned_data.get('fecha_pago')
        if fecha_pago < fecha_inicio:
            raise ValidationError('La fecha de pago no puede ser anterior a la fecha de inicio.')
        return fecha_pago
