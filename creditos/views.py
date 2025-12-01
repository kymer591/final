from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from .models import Prestamo, Amortizacion
from .forms import PrestamoForm, AmortizacionForm

def home(request):
    """Vista principal del sistema"""
    return render(request, 'creditos/home.html')

def prestamo_lista(request):
    """Lista todos los préstamos con búsqueda"""
    query = request.GET.get('q', '')
    
    if query:
        prestamos = Prestamo.objects.filter(
            Q(nombre__icontains=query) | 
            Q(ci__icontains=query)
        )
    else:
        prestamos = Prestamo.objects.all()
    
    context = {
        'prestamos': prestamos,
        'query': query
    }
    return render(request, 'creditos/prestamo_lista.html', context)

def prestamo_crear(request):
    """Crea un nuevo préstamo"""
    if request.method == 'POST':
        form = PrestamoForm(request.POST)
        if form.is_valid():
            prestamo = form.save()
            messages.success(
                request, 
                f'Préstamo creado exitosamente para {prestamo.nombre}. '
                f'Se generaron {prestamo.plazo} cuotas de amortización.'
            )
            return redirect('prestamo_detalle', pk=prestamo.pk)
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario.')
    else:
        form = PrestamoForm()
    
    context = {
        'form': form,
        'titulo': 'Crear Nuevo Préstamo'
    }
    return render(request, 'creditos/prestamo_form.html', context)

def prestamo_editar(request, pk):
    """Edita un préstamo existente"""
    prestamo = get_object_or_404(Prestamo, pk=pk)
    
    if request.method == 'POST':
        form = PrestamoForm(request.POST, instance=prestamo)
        if form.is_valid():
            prestamo = form.save()
            # Regenerar la tabla de amortización
            prestamo.generar_amortizacion()
            messages.success(
                request, 
                f'Préstamo actualizado exitosamente. '
                f'Se regeneró la tabla de amortización con {prestamo.plazo} cuotas.'
            )
            return redirect('prestamo_detalle', pk=prestamo.pk)
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario.')
    else:
        form = PrestamoForm(instance=prestamo)
    
    context = {
        'form': form,
        'prestamo': prestamo,
        'titulo': f'Editar Préstamo - {prestamo.nombre}'
    }
    return render(request, 'creditos/prestamo_form.html', context)

def prestamo_detalle(request, pk):
    """Muestra el detalle del préstamo y su tabla de amortización"""
    prestamo = get_object_or_404(Prestamo, pk=pk)
    amortizaciones = prestamo.amortizaciones.all()
    
    # Calcular totales
    total_cuotas = sum(a.cuota for a in amortizaciones)
    total_capital = sum(a.capital for a in amortizaciones)
    total_interes = sum(a.interes for a in amortizaciones)
    
    # Calcular estado de pagos
    cuotas_pagadas = amortizaciones.filter(pagado=True).count()
    cuotas_pendientes = amortizaciones.filter(pagado=False).count()
    
    context = {
        'prestamo': prestamo,
        'amortizaciones': amortizaciones,
        'total_cuotas': total_cuotas,
        'total_capital': total_capital,
        'total_interes': total_interes,
        'cuotas_pagadas': cuotas_pagadas,
        'cuotas_pendientes': cuotas_pendientes,
    }
    return render(request, 'creditos/prestamo_detalle.html', context)

def prestamo_eliminar(request, pk):
    """Elimina un préstamo"""
    prestamo = get_object_or_404(Prestamo, pk=pk)
    
    if request.method == 'POST':
        nombre = prestamo.nombre
        prestamo.delete()
        messages.success(request, f'Préstamo de {nombre} eliminado exitosamente.')
        return redirect('prestamo_lista')
    
    context = {
        'prestamo': prestamo
    }
    return render(request, 'creditos/prestamo_confirmar_eliminar.html', context)

def amortizacion_actualizar(request, pk):
    """Actualiza el estado de una cuota de amortización"""
    amortizacion = get_object_or_404(Amortizacion, pk=pk)
    
    # Verificar si hay cuotas anteriores sin pagar
    cuota_anterior_pendiente = None
    if amortizacion.numero_cuota > 1:
        cuota_anterior_pendiente = Amortizacion.objects.filter(
            prestamo=amortizacion.prestamo,
            numero_cuota__lt=amortizacion.numero_cuota,
            pagado=False
        ).first()
    
    if request.method == 'POST':
        form = AmortizacionForm(request.POST, instance=amortizacion)
        if form.is_valid():
            form.save()
            messages.success(
                request, 
                f'Cuota #{amortizacion.numero_cuota} actualizada exitosamente.'
            )
            return redirect('prestamo_detalle', pk=amortizacion.prestamo.pk)
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario.')
    else:
        form = AmortizacionForm(instance=amortizacion)
    
    context = {
        'form': form,
        'amortizacion': amortizacion,
        'prestamo': amortizacion.prestamo,
        'cuota_anterior_pendiente': cuota_anterior_pendiente,
    }
    return render(request, 'creditos/amortizacion_form.html', context)