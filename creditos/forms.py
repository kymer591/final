from django import forms
from .models import Prestamo, Amortizacion
from decimal import Decimal
import re
from datetime import date

class PrestamoForm(forms.ModelForm):
    class Meta:
        model = Prestamo
        fields = ['nombre', 'ci', 'monto', 'tasa_interes_anual', 'fecha_inicio', 'plazo']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre completo del cliente'
            }),
            'ci': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 12345678 LP'
            }),
            'monto': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Monto en bolivianos',
                'step': '0.01'
            }),
            'tasa_interes_anual': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 12.50',
                'step': '0.01'
            }),
            'fecha_inicio': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'plazo': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de meses'
            }),
        }
    
    def clean_nombre(self):
        """Validar que el nombre solo contenga letras y espacios"""
        nombre = self.cleaned_data.get('nombre')
        
        if not nombre:
            raise forms.ValidationError("El nombre es obligatorio.")
        
        # Eliminar espacios extras
        nombre = ' '.join(nombre.split())
        
        # Validar que solo contenga letras y espacios
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', nombre):
            raise forms.ValidationError("El nombre solo debe contener letras y espacios.")
        
        # Validar longitud mínima
        if len(nombre) < 3:
            raise forms.ValidationError("El nombre debe tener al menos 3 caracteres.")
        
        return nombre.upper()
    
    def clean_ci(self):
        """Validar formato de Cédula de Identidad"""
        ci = self.cleaned_data.get('ci')
        
        if not ci:
            raise forms.ValidationError("La cédula de identidad es obligatoria.")
        
        # Eliminar espacios extras
        ci = ci.strip().upper()
        
        # Validar formato (números y opcionalmente extensión: LP, SC, CB, etc.)
        if not re.match(r'^\d{5,10}(\s?[A-Z]{2})?$', ci):
            raise forms.ValidationError(
                "Formato de CI inválido. Use formato: 12345678 o 12345678 LP"
            )
        
        # Verificar que no exista otro préstamo con el mismo CI
        if self.instance.pk:
            # Estamos editando, excluir el registro actual
            existe = Prestamo.objects.filter(ci=ci).exclude(pk=self.instance.pk).exists()
        else:
            # Es nuevo registro
            existe = Prestamo.objects.filter(ci=ci).exists()
        
        if existe:
            raise forms.ValidationError(
                "Ya existe un préstamo registrado con esta cédula de identidad."
            )
        
        return ci
    
    def clean_monto(self):
        """Validar monto del préstamo"""
        monto = self.cleaned_data.get('monto')
        
        if monto is None:
            raise forms.ValidationError("El monto es obligatorio.")
        
        if monto < Decimal('100.00'):
            raise forms.ValidationError("El monto mínimo es de Bs. 100.00")
        
        if monto > Decimal('10000000.00'):
            raise forms.ValidationError("El monto máximo es de Bs. 10,000,000.00")
        
        return monto
    
    def clean_tasa_interes_anual(self):
        """Validar tasa de interés"""
        tasa = self.cleaned_data.get('tasa_interes_anual')
        
        if tasa is None:
            raise forms.ValidationError("La tasa de interés es obligatoria.")
        
        if tasa <= Decimal('0'):
            raise forms.ValidationError("La tasa de interés debe ser mayor a 0%")
        
        if tasa > Decimal('100.00'):
            raise forms.ValidationError("La tasa de interés no puede ser mayor a 100%")
        
        return tasa
    
    def clean_fecha_inicio(self):
        """Validar fecha de inicio"""
        fecha = self.cleaned_data.get('fecha_inicio')
        
        if not fecha:
            raise forms.ValidationError("La fecha de inicio es obligatoria.")
        
        # No permitir fechas muy antiguas (más de 1 año atrás)
        from datetime import timedelta
        fecha_minima = date.today() - timedelta(days=365)
        
        if fecha < fecha_minima:
            raise forms.ValidationError(
                "La fecha de inicio no puede ser mayor a 1 año en el pasado."
            )
        
        # No permitir fechas muy futuras (más de 1 año adelante)
        fecha_maxima = date.today() + timedelta(days=365)
        
        if fecha > fecha_maxima:
            raise forms.ValidationError(
                "La fecha de inicio no puede ser mayor a 1 año en el futuro."
            )
        
        return fecha
    
    def clean_plazo(self):
        """Validar plazo del préstamo"""
        plazo = self.cleaned_data.get('plazo')
        
        if plazo is None:
            raise forms.ValidationError("El plazo es obligatorio.")
        
        if plazo < 1:
            raise forms.ValidationError("El plazo mínimo es de 1 mes.")
        
        if plazo > 360:
            raise forms.ValidationError("El plazo máximo es de 360 meses (30 años).")
        
        return plazo
    
    def clean(self):
        """Validaciones generales que involucran múltiples campos"""
        cleaned_data = super().clean()
        monto = cleaned_data.get('monto')
        plazo = cleaned_data.get('plazo')
        tasa = cleaned_data.get('tasa_interes_anual')
        
        # Validar que la cuota mensual no sea excesiva
        if monto and plazo and tasa:
            # Calcular tasa mensual
            tasa_mensual = tasa / Decimal('12') / Decimal('100')
            
            # Calcular cuota mensual
            if tasa_mensual > 0:
                cuota = monto * (tasa_mensual * (1 + tasa_mensual)**plazo) / ((1 + tasa_mensual)**plazo - 1)
            else:
                cuota = monto / plazo
            
            # Validar que la cuota no sea menor a Bs. 10
            if cuota < Decimal('10.00'):
                raise forms.ValidationError(
                    "La combinación de monto, tasa y plazo resulta en una cuota muy baja (menor a Bs. 10). "
                    "Por favor ajuste los valores."
                )
        
        return cleaned_data


class AmortizacionForm(forms.ModelForm):
    class Meta:
        model = Amortizacion
        fields = ['pagado', 'fecha_pago_real']
        widgets = {
            'pagado': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'fecha_pago_real': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
    
    def clean(self):
        """Validar que si está marcado como pagado, tenga fecha de pago real"""
        cleaned_data = super().clean()
        pagado = cleaned_data.get('pagado')
        fecha_pago_real = cleaned_data.get('fecha_pago_real')
        
        if pagado and not fecha_pago_real:
            raise forms.ValidationError(
                "Si marca la cuota como pagada, debe ingresar la fecha de pago real."
            )
        
        if not pagado and fecha_pago_real:
            cleaned_data['fecha_pago_real'] = None
        
        # NUEVA VALIDACIÓN: Verificar que las cuotas anteriores estén pagadas
        if pagado and self.instance.numero_cuota > 1:
            # Buscar la cuota anterior
            cuota_anterior = Amortizacion.objects.filter(
                prestamo=self.instance.prestamo,
                numero_cuota=self.instance.numero_cuota - 1
            ).first()
            
            if cuota_anterior and not cuota_anterior.pagado:
                raise forms.ValidationError(
                    f"No puede marcar esta cuota como pagada. "
                    f"Primero debe pagar la cuota #{cuota_anterior.numero_cuota}."
                )
        
        # NUEVA VALIDACIÓN: No permitir despagar si hay cuotas posteriores pagadas
        if not pagado and self.instance.pk:
            # Verificar si ya estaba pagada anteriormente
            cuota_actual = Amortizacion.objects.get(pk=self.instance.pk)
            if cuota_actual.pagado:
                # Buscar si hay cuotas posteriores pagadas
                cuotas_posteriores_pagadas = Amortizacion.objects.filter(
                    prestamo=self.instance.prestamo,
                    numero_cuota__gt=self.instance.numero_cuota,
                    pagado=True
                ).exists()
                
                if cuotas_posteriores_pagadas:
                    raise forms.ValidationError(
                        "No puede desmarcar esta cuota como pagada porque hay cuotas "
                        "posteriores que ya están marcadas como pagadas. "
                        "Primero debe desmarcar las cuotas posteriores."
                    )
        
        return cleaned_data
    
    def clean_fecha_pago_real(self):
        """Validar fecha de pago real"""
        fecha = self.cleaned_data.get('fecha_pago_real')
        
        if fecha:
            # No permitir fechas futuras
            if fecha > date.today():
                raise forms.ValidationError(
                    "La fecha de pago real no puede ser futura."
                )
            
            # Validar que no sea anterior a la fecha de inicio del préstamo
            if self.instance.prestamo:
                if fecha < self.instance.prestamo.fecha_inicio:
                    raise forms.ValidationError(
                        "La fecha de pago no puede ser anterior a la fecha de inicio del préstamo."
                    )
                
                # NUEVA VALIDACIÓN: Verificar que no sea anterior a la fecha de pago de la cuota anterior
                if self.instance.numero_cuota > 1:
                    cuota_anterior = Amortizacion.objects.filter(
                        prestamo=self.instance.prestamo,
                        numero_cuota=self.instance.numero_cuota - 1,
                        pagado=True
                    ).first()
                    
                    if cuota_anterior and cuota_anterior.fecha_pago_real:
                        if fecha < cuota_anterior.fecha_pago_real:
                            raise forms.ValidationError(
                                f"La fecha de pago no puede ser anterior a la fecha de pago "
                                f"de la cuota anterior ({cuota_anterior.fecha_pago_real.strftime('%d/%m/%Y')})."
                            )
        
        return fecha