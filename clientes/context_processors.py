from .models import Cliente

def cliente_context(request):
    if request.user.is_authenticated:
        cliente = Cliente.objects.filter(user=request.user).first()
        return {'cliente': cliente}
    return {}

