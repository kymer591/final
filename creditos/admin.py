from django.contrib import admin
from .models import Prestamo, Amortizacion

class AmortizacionInline(admin.TabularInline):
    model = Amortizacion
    extra = 0
    readonly_fields = ['numero_cuota', 'fecha_pago', 'cuota', 'capital', 'interes', 'saldo', 'dias_mora', 'estado']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Prestamo)
class PrestamoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'ci', 'monto', 'tasa_interes_anual', 'plazo', 'fecha_inicio', 'cuota_mensual_display']
    list_filter = ['fecha_inicio', 'fecha_creacion']
    search_fields = ['nombre', 'ci']
    readonly_fields = ['tasa_mensual_display', 'cuota_mensual_display', 'fecha_creacion', 'fecha_actualizacion']
    
    fieldsets = (
        ('Información del Cliente', {
            'fields': ('nombre', 'ci')
        }),
        ('Información del Préstamo', {
            'fields': ('monto', 'tasa_interes_anual', 'tasa_mensual_display', 'fecha_inicio', 'plazo')
        }),
        ('Cálculos', {
            'fields': ('cuota_mensual_display',),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [AmortizacionInline]
    
    def tasa_mensual_display(self, obj):
        if obj.tasa_mensual is None:
            return "-"
        return f"{obj.tasa_mensual * 100:.4f}%"
    tasa_mensual_display.short_description = 'Tasa Mensual'
    
    def cuota_mensual_display(self, obj):
        if obj.cuota_mensual is None:
            return "-"
        return f"Bs. {obj.cuota_mensual:,.2f}"
    cuota_mensual_display.short_description = 'Cuota Mensual'

@admin.register(Amortizacion)
class AmortizacionAdmin(admin.ModelAdmin):
    list_display = ['prestamo', 'numero_cuota', 'fecha_pago', 'cuota', 'capital', 'interes', 'saldo', 'estado', 'pagado']
    list_filter = ['pagado', 'fecha_pago', 'prestamo']
    search_fields = ['prestamo__nombre', 'prestamo__ci']
    readonly_fields = ['dias_mora', 'estado']
    
    fieldsets = (
        ('Información General', {
            'fields': ('prestamo', 'numero_cuota', 'fecha_pago')
        }),
        ('Desglose de Cuota', {
            'fields': ('cuota', 'capital', 'interes', 'saldo')
        }),
        ('Estado de Pago', {
            'fields': ('pagado', 'fecha_pago_real', 'dias_mora', 'estado')
        }),
    )