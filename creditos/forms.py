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
        
        nombre = ' '.join(nombre.split())
        
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', nombre):
            raise forms.ValidationError("El nombre solo debe contener letras y espacios.")
        
        if len(nombre) < 3:
            raise forms.ValidationError("El nombre debe tener al menos 3 caracteres.")
        
        return nombre.upper()
    
    def clean_ci(self):
        """Validar formato de Cédula de Identidad"""
        ci = self.cleaned_data.get('ci')
        
        if not ci:
            raise forms.ValidationError("La cédula de identidad es obligatoria.")
        
        ci = ci.strip().upper()
        
        if not re.match(r'^\d{5,10}(\s?[A-Z]{2})?$', ci):
            raise forms.ValidationError(
                "Formato de CI inválido. Use formato: 12345678 o 12345678 LP"
            )
        
        if self.instance.pk:
            existe = Prestamo.objects.filter(ci=ci).exclude(pk=self.instance.pk).exists()
        else:
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
        
        from datetime import timedelta
        fecha_minima = date.today() - timedelta(days=365)
        
        if fecha < fecha_minima:
            raise forms.ValidationError(
                "La fecha de inicio no puede ser mayor a 1 año en el pasado."
            )
        
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
        
        if monto and plazo and tasa:
            tasa_mensual = tasa / Decimal('12') / Decimal('100')
            
            if tasa_mensual > 0:
                cuota = monto * (tasa_mensual * (1 + tasa_mensual)**plazo) / ((1 + tasa_mensual)**plazo - 1)
            else:
                cuota = monto / plazo

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
        
        return cleaned_data
    
    def clean_fecha_pago_real(self):
        """Validar fecha de pago real"""
        fecha = self.cleaned_data.get('fecha_pago_real')
        
        if fecha:
            if fecha > date.today():
                raise forms.ValidationError(
                    "La fecha de pago real no puede ser futura."
                )
            
            if self.instance.prestamo:
                if fecha < self.instance.prestamo.fecha_inicio:
                    raise forms.ValidationError(
                        "La fecha de pago no puede ser anterior a la fecha de inicio del préstamo."
                    )
        
        return fecha