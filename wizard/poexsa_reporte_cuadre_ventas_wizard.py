# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.tools import convert
from datetime import datetime
import xlsxwriter
import base64
import io
import logging

class PoexsaReporteCuadreVentasWizard(models.TransientModel):
    _name = 'poexsa.reporte_cuadre_ventas_wizard'

    fecha = fields.Date('Fecha')
    sesion_ids = fields.Many2many('pos.session',string='Sesiones')
    grupo_cuadre_ids = fields.Many2many('poexsa.grupo_cuadre',string='Grupo de cuadre')
    name = fields.Char('Nombre archivo', size=32)
    archivo = fields.Binary('Archivo', filters='.xls')

    def generar_ajuste_inventario(self):
        resumen_productos_general = self.obtener_resumen_productos()
        if resumen_productos_general:
            resumen_productos = resumen_productos_general[0]
            for grupo in resumen_productos:
                if resumen_productos[grupo]['productos']:
                    for producto in resumen_productos[grupo]['productos']:
                        producto = resumen_productos[grupo]['productos'][producto]['product_product']
                        sobrante = resumen_productos[grupo]['productos'][producto]['sobrante']
                        logging.warning(producto)
                        movimiento_inventario_id = self.env['stock.move'].create({'product_id': producto, 'inventory_quantity': sobrante})
        return True

    def obtener_resumen_productos(self):
        for w in self:
            cuadre = []
            producto_ids = self.env['product.template'].search([('available_in_pos','=', True),('grupo_cuadre_id','in', w.grupo_cuadre_ids.ids)])
            linea_venta_ids = self.env['pos.order.line'].search([('order_id.date_order','>=', w.fecha),('order_id.date_order','<=',w.fecha)])
            resumen_productos = {}
            ventas_dic = {}
            ingreso_dic = {}
            gastos = []
            inventario_productos = {}
            total_gastos = 0
            depositos = []
            pago_ids = self.env['pos.payment'].search([('session_id', 'in', w.sesion_ids.ids)])
            total_pagos = {}
            conversion_dolar = 0
            total = 0
            if pago_ids:
                for pago in pago_ids:
                    if pago.payment_method_id.id not in total_pagos:
                        total_pagos[pago.payment_method_id.id] = {'nombre': pago.payment_method_id.name,'total': 0, 'tipo_cambio': 0}

                    if pago.payment_method_id.journal_id:
                        if pago.payment_method_id.journal_id.currency_id and pago.payment_method_id.journal_id.currency_id.name == "USD":
                            conversion_dolar = pago.payment_method_id.journal_id.currency_id._get_conversion_rate(pago.payment_method_id.journal_id.currency_id, pago.company_id.currency_id, pago.company_id, pago.pos_order_id.date_order)
                            monto_quetzal = pago.payment_method_id.journal_id.currency_id._convert(pago.amount,pago.company_id.currency_id,pago.company_id,pago.pos_order_id.date_order)
                            total_pagos[pago.payment_method_id.id]['total'] += monto_quetzal
                            total_pagos[pago.payment_method_id.id]['tipo_cambio'] = conversion_dolar
                        else:
                            total_pagos[pago.payment_method_id.id]['total'] += pago.amount

            for sesion in w.sesion_ids:
                if sesion.cash_register_id:
                    if sesion.cash_register_id.line_ids:
                        for linea in sesion.cash_register_id.line_ids:
                            if linea.amount < 0:
                                if ("Deposito" or "DEPOSITO" or "Depósito" or "DEPÓSITO") in linea.payment_ref:
                                    depositos.append({'descripcion': linea.payment_ref,'importe': linea.amount * -1})
                                else:
                                    gastos.append({'descripcion': linea.payment_ref,'importe': linea.amount * -1})
                                    total_gastos += (linea.amount * -1)

            ingreso_ids = self.env['poexsa.ingreso_producto'].search([('fecha','>=', w.fecha),('fecha','<=', w.fecha)])
            for ingreso in ingreso_ids:
                if ingreso.default_pos_id.id == w.sesion_ids[0].config_id.id:
                    if ingreso.producto_id.id not in ingreso_dic:
                        ingreso_dic[ingreso.producto_id.id] = 0
                    ingreso_dic[ingreso.producto_id.id] += ingreso.cantidad

            if linea_venta_ids:
                ubicacion = w.sesion_ids[0].config_id.picking_type_id.default_location_src_id.id
                for producto in self.env['product.product'].with_context({'location': ubicacion, 'to_date': self.fecha.strftime("%Y-%m-%d %H:%M:%S"), 'lang':'es_GT'}).search([('type', '=', 'product'), '|', ('active', '=', True), ('active', '=', False)]):
                    if producto.id not in inventario_productos:
                        inventario_productos[producto.id] = producto.qty_available

                for venta in linea_venta_ids:
                    if venta.product_id.id not in ventas_dic:
                        ventas_dic[venta.product_id.product_tmpl_id.id] = {'cantidad':0, 'efectivo_venta': 0 }
                    ventas_dic[venta.product_id.product_tmpl_id.id]['cantidad'] += venta.qty
                    ventas_dic[venta.product_id.product_tmpl_id.id]['efectivo_venta'] += venta.price_subtotal_incl


            resumen_productos = {}
            for producto in producto_ids:
                producto_grupo_cuadre_id = producto.grupo_cuadre_id.id
                if producto_grupo_cuadre_id not in resumen_productos:
                    resumen_productos[producto_grupo_cuadre_id] = {'nombre_grupo': producto.grupo_cuadre_id.name, 'productos': {},'inicial': 0, 'ingreso':0, 'total':0, 'ventas': 0,'sobrante':0, 'efectivo_venta':0 }

                if producto.id not in resumen_productos[producto_grupo_cuadre_id]['productos']:
                    inicial = 0
                    if producto.product_variant_id.id in inventario_productos:
                        inicial = inventario_productos[producto.product_variant_id.id]
                    resumen_productos[producto_grupo_cuadre_id]['productos'][producto.id] = {'product_product': producto.product_variant_id.id,'producto': producto.name,'inicial': inicial, 'ingreso':0, 'total':0, 'ventas': 0,'sobrante':0, 'efectivo_venta':0}
                    resumen_productos[producto_grupo_cuadre_id]['inicial'] += inicial

                if producto.id in ventas_dic:
                    resumen_productos[producto_grupo_cuadre_id]['productos'][producto.id]['ventas'] = ventas_dic[producto.id]['cantidad']
                    resumen_productos[producto_grupo_cuadre_id]['productos'][producto.id]['efectivo_venta'] += ventas_dic[producto.id]['efectivo_venta']
                    resumen_productos[producto_grupo_cuadre_id]['ventas'] += ventas_dic[producto.id]['cantidad']
                    resumen_productos[producto_grupo_cuadre_id]['efectivo_venta'] += ventas_dic[producto.id]['efectivo_venta']

                if producto.id in ingreso_dic:
                    resumen_productos[producto_grupo_cuadre_id]['productos'][producto.id]['ingreso'] = ingreso_dic[producto.id]
                    resumen_productos[producto_grupo_cuadre_id]['ingreso'] += ingreso_dic[producto.id]

        return [resumen_productos,gastos, depositos, total_pagos]

    def print_report_excel(self):
        for w in self:
            dict = {}


            f = io.BytesIO()
            libro = xlsxwriter.Workbook(f)
            hoja = libro.add_worksheet('Reporte cuadre de ventas')
            formato_fecha = libro.add_format({'num_format': 'dd/mm/yy'})

            hoja.set_column("B:H", 12)
            # hoja.set_row(3, 30)
            # hoja.set_row(6, 30)
            # hoja.set_row(7, 30)

            formato_unir_celdas_encabezado = libro.add_format(
                {
                    "bold": 1,
                    "border": 1,
                    "align": "center",
                    "valign": "vcenter",
                    "fg_color": "orange",
                }
            )
            formato_unir_celdas_fecha = libro.add_format(
                {
                    "bold": 1,
                    "border": 1,
                    "align": "center",
                    "valign": "vcenter",
                    "fg_color": "yellow",
                }
            )
            formato_columna = libro.add_format(
                {
                    "bold": 1,
                    "border": 1,
                    "align": "center",
                    "valign": "vcenter",
                }
            )

            formato_gastos_encabezado = libro.add_format(
                {
                    "bold": 1,
                    "border": 1,
                    "align": "center",
                    "valign": "vcenter",
                }
            )
            formato_gastos_total = libro.add_format(
                {
                    "bold": 1,
                    "border": 1,
                    "align": "center",
                    "valign": "vcenter",
                }
            )
            formato_resumen = libro.add_format(
                {
                    "border": 1,
                    "align": "center",
                    "valign": "vcenter",
                }
            )
            formato_total = libro.add_format(
                {
                    "bold": 1,
                    "align": "center",
                    "valign": "vcenter",
                }
            )

            cuadre = []
            resumen_productos = {}
            ventas_dic = {}
            ingreso_dic = {}
            gastos = []
            inventario_productos = {}
            total_gastos = 0
            depositos = []
            total_pagos = {}
            conversion_dolar = 0
            total = 0
            gran_total = 0
            resumen_productos_general = self.obtener_resumen_productos()
            resumen_productos = resumen_productos_general[0]
            gastos = resumen_productos_general[1]
            depositos = resumen_productos_general[2]
            total_pagos = resumen_productos_general[3]

            fila = 5
            fecha = datetime.strptime(str(w.fecha), "%Y-%m-%d").strftime("%A, %B %d, %Y")
            hoja.merge_range("B3:H3", w.sesion_ids[0].config_id.name,formato_unir_celdas_encabezado)
            hoja.merge_range("D5:E5", "FECHA:")
            hoja.merge_range("F5:H5", str(fecha),formato_unir_celdas_fecha)
            hoja.write(5, 1, "PRODUCTO", formato_columna)
            hoja.write(5, 2, "INICIAL", formato_columna)
            hoja.write(5, 3, "INGRESO", formato_columna)
            hoja.write(5, 4, "TOTAL", formato_columna)
            hoja.write(5, 5, "VENTAS", formato_columna)
            hoja.write(5, 6, "SOBRANTE", formato_columna)
            hoja.write(5, 7, "EFECTIVO DE VENTA", formato_columna)

            total_efectivo = 0
            fila += 1
            for grupo in resumen_productos:
                nombre = resumen_productos[grupo]['nombre_grupo']
                inicial = resumen_productos[grupo]['inicial']
                ingreso = resumen_productos[grupo]['ingreso']
                total = inicial + ingreso
                ventas = resumen_productos[grupo]['ventas']
                sobrante = total - ventas
                efectivo_venta = resumen_productos[grupo]['efectivo_venta']
                hoja.write(fila, 1, nombre, formato_resumen)
                hoja.write(fila, 2, inicial, formato_resumen)
                hoja.write(fila, 3, ingreso, formato_resumen)
                hoja.write(fila, 4, total, formato_resumen)
                hoja.write(fila, 5, ventas, formato_resumen)
                hoja.write(fila, 6, sobrante, formato_resumen)
                hoja.write(fila, 7, efectivo_venta, formato_resumen)
                total_efectivo += efectivo_venta
                fila += 1

            rango = "G"+str(fila)+":G"+str(fila)
            hoja.write(fila,6, "TOTAL", formato_gastos_total)
            hoja.write(fila,7, total_efectivo, formato_gastos_total)
            fila += 3
            # hoja.write(4, 6, 'Fecha')
            # hoja.write(4, 6, str(w.fecha))
            rango_gastos = "B"+str(fila)+":E"+str(fila)
            hoja.merge_range(rango_gastos, "GASTOS", formato_gastos_encabezado)

            if len(gastos) > 0:
                for gasto in gastos:
                    rango_gastos_d = "B"+str(fila)+":D"+str(fila)
                    hoja.write(fila,2, gasto['descripcion'])
                    hoja.write(fila, 4,gasto['importe'])
                    total_gastos += gasto['importe']
                    fila +=1


            rango_total = "B"+str(fila)+":E"+str(fila)
            hoja.write(fila,2, "TOTAL", formato_total)
            hoja.write(fila,4, total_gastos)

            fila += 2
            total_pagos_monto = 0
            if len(depositos) > 0:
                for deposito in depositos:
                    logging.warning(deposito)
                    hoja.write(fila, 2, deposito['descripcion'])
                    hoja.write(fila, 4, deposito['importe'])
                    gran_total += deposito['importe']* -1
                    fila += 1
            if total_pagos:
                for pago in total_pagos:
                    forma_pago = total_pagos[pago]['nombre']
                    total_pago = total_pagos[pago]['total']
                    hoja.write(fila, 2, forma_pago)
                    if forma_pago == "DOLARES":
                        hoja.write(fila, 3, total_pagos[pago]['tipo_cambio'])
                    hoja.write(fila, 4, total_pago)
                    total_pagos_monto += total_pago
                    total += total_pago
                    fila += 1

            gran_total += total_pagos_monto - total_gastos
            rango_resumen = "B"+str(fila)+":D"+str(fila)
            hoja.write(fila, 2, "TOTAL", formato_total)
            hoja.write(fila, 4, gran_total)
            fila += 1
            sobrante_faltante = total -total_efectivo
            hoja.write(fila, 2, "SOBRANTE/FALTANTE")
            hoja.write(fila, 4, sobrante_faltante)
            #hoja.merge_range(rango_resumen, "SOBRANTE/FALTANTE", formato_gastos_total)

            libro.close()
            datos = base64.b64encode(f.getvalue())
            self.write({'archivo':datos, 'name':'reporte_cuadre_ventas.xlsx'})

        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'poexsa.reporte_cuadre_ventas_wizard',
            'res_id': self.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
