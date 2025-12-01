from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from datetime import timedelta
from dateutil.relativedelta import relativedelta

class Prestamo(models.Model):
    nombre = models.CharField(max_length=200, verbose_name="Nombre del Cliente")
    ci = models.CharField(max_length=20, unique=True, verbose_name="Cédula de Identidad")
    monto = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('100.00'))],
        verbose_name="Monto del Préstamo"
    )
    tasa_interes_anual = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal('0.01')),
            MaxValueValidator(Decimal('100.00'))
        ],
        verbose_name="Tasa de Interés Anual (%)"
    )
    fecha_inicio = models.DateField(verbose_name="Fecha de Inicio")
    plazo = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(360)],
        verbose_name="Plazo en Meses"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Préstamo"
        verbose_name_plural = "Préstamos"
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.nombre} - CI: {self.ci} - Bs. {self.monto}"
    
    @property
    def tasa_mensual(self):
        """Calcula la tasa de interés mensual"""
        if self.tasa_interes_anual is None:
            return None
        return self.tasa_interes_anual / Decimal('12') / Decimal('100')
    
    @property
    def cuota_mensual(self):
        """Calcula la cuota mensual usando el método francés"""
        if not all([self.monto, self.tasa_interes_anual, self.plazo]):
            return None
        
        i = self.tasa_mensual
        n = self.plazo
        
        if i == 0:
            return self.monto / n
        
        cuota = self.monto * (i * (1 + i)**n) / ((1 + i)**n - 1)
        return cuota.quantize(Decimal('0.01'))
    
    def generar_amortizacion(self):
        """tabla de amortización"""
        self.amortizaciones.all().delete()
        
        saldo = self.monto
        cuota = self.cuota_mensual
        fecha_pago = self.fecha_inicio
        
        for numero_cuota in range(1, self.plazo + 1):
            fecha_pago = fecha_pago + relativedelta(months=1)
            interes = (saldo * self.tasa_mensual).quantize(Decimal('0.01'))
            
            if numero_cuota == self.plazo:
                capital = saldo
                cuota_ajustada = capital + interes
            else:
                capital = (cuota - interes).quantize(Decimal('0.01'))
                cuota_ajustada = cuota
            
            nuevo_saldo = (saldo - capital).quantize(Decimal('0.01'))
            if nuevo_saldo < 0:
                nuevo_saldo = Decimal('0.00')
            
            Amortizacion.objects.create(
                prestamo=self,
                numero_cuota=numero_cuota,
                fecha_pago=fecha_pago,
                cuota=cuota_ajustada,
                capital=capital,
                interes=interes,
                saldo=nuevo_saldo
            )
            
            saldo = nuevo_saldo
    
    def save(self, *args, **kwargs):
        """Override del método save para generar amortización automáticamente"""
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            self.generar_amortizacion()


class Amortizacion(models.Model):
    prestamo = models.ForeignKey(
        Prestamo, 
        on_delete=models.CASCADE, 
        related_name='amortizaciones',
        verbose_name="Préstamo"
    )
    numero_cuota = models.PositiveIntegerField(verbose_name="N° Cuota")
    fecha_pago = models.DateField(verbose_name="Fecha de Pago")
    cuota = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        verbose_name="Cuota"
    )
    capital = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        verbose_name="Capital (Amortización)"
    )
    interes = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        verbose_name="Interés"
    )
    saldo = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        verbose_name="Saldo Restante"
    )
    pagado = models.BooleanField(default=False, verbose_name="¿Pagado?")
    fecha_pago_real = models.DateField(
        null=True, 
        blank=True,
        verbose_name="Fecha de Pago Real"
    )
    
    class Meta:
        verbose_name = "Cuota de Amortización"
        verbose_name_plural = "Cuotas de Amortización"
        ordering = ['prestamo', 'numero_cuota']
        unique_together = ['prestamo', 'numero_cuota']
    
    def __str__(self):
        return f"Cuota {self.numero_cuota} - {self.prestamo.nombre}"
    
    @property
    def dias_mora(self):
        """Calcula los días de mora si la cuota no está pagada"""
        if self.pagado:
            return 0
        from datetime import date
        hoy = date.today()
        if hoy > self.fecha_pago:
            return (hoy - self.fecha_pago).days
        return 0
    
    @property
    def estado(self):
        """Retorna el estado de la cuota"""
        if self.pagado:
            return "PAGADA"
        elif self.dias_mora > 0:
            return f"MORA ({self.dias_mora} días)"
        else:
            return "PENDIENTE"