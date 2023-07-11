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
    categoria_ids = fields.Many2many('product.category',string='Categorías')
    name = fields.Char('Nombre archivo', size=32)
    archivo = fields.Binary('Archivo', filters='.xls')

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
            cuadre = []
            producto_ids = self.env['product.template'].search([('available_in_pos','=', True)])
            linea_venta_ids = self.env['pos.order.line'].search([('order_id.date_order','>=', w.fecha),('order_id.date_order','<=',w.fecha)])
            resumen_productos = {}
            ventas_dic = {}
            ingreso_dic = {}
            gastos = []
            inventario_productos = {}
            total_gastos = 0
            pago_ids = self.env['pos.payment'].search([('session_id', 'in', w.sesion_ids.ids)])
            total_pagos = {}
            conversion_dolar = 0
            if pago_ids:
                for pago in pago_ids:
                    if pago.payment_method_id.id not in total_pagos:
                        total_pagos[pago.payment_method_id.id] = {'nombre': pago.payment_method_id.name,'total': 0}

                    if pago.payment_method_id.journal_id:
                        if pago.payment_method_id.journal_id.currency_id and pago.payment_method_id.journal_id.currency_id.name == "USD":
                            conversion_dolar = pago.payment_method_id.journal_id.currency_id._get_conversion_rate(pago.payment_method_id.journal_id.currency_id, pago.company_id.currency_id, pago.company_id, pago.pos_order_id.date_order)
                            monto_quetzal = pago.payment_method_id.journal_id.currency_id._convert(pago.amount,pago.company_id.currency_id,pago.company_id,pago.pos_order_id.date_order)
                            total_pagos[pago.payment_method_id.id]['total'] += monto_quetzal
                        else:
                            total_pagos[pago.payment_method_id.id]['total'] += pago.amount

            for sesion in w.sesion_ids:
                if sesion.cash_register_id:
                    if sesion.cash_register_id.line_ids:
                        for linea in sesion.cash_register_id.line_ids:
                            if linea.amount < 0:
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

            if producto_ids and linea_venta_ids:
                for producto in producto_ids:
                    if producto.id not in resumen_productos:
                        inicial = 0
                        if producto.product_variant_id.id in inventario_productos:
                            inicial = inventario_productos[producto.product_variant_id.id]
                        resumen_productos[producto.id] = {'producto': producto.name,'inicial': inicial, 'ingreso':0, 'total':0, 'ventas': 0,'sobrante':0, 'efectivo_venta':0}

                    if producto.id in ventas_dic:
                        resumen_productos[producto.id]['ventas'] = ventas_dic[producto.id]['cantidad']
                        resumen_productos[producto.id]['efectivo_venta'] += ventas_dic[producto.id]['efectivo_venta']


                    if producto.id in ingreso_dic:
                        resumen_productos[producto.id]['ingreso'] = ingreso_dic[producto.id]

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
            for producto in resumen_productos:

                nombre = resumen_productos[producto]['producto']
                inicial = resumen_productos[producto]['inicial']
                ingreso = resumen_productos[producto]['ingreso']
                total = inicial + ingreso
                ventas = resumen_productos[producto]['ventas']
                sobrante = total - ventas
                efectivo_venta = resumen_productos[producto]['efectivo_venta']
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

                    fila +=1


            rango_total = "B"+str(fila)+":E"+str(fila)
            hoja.write(fila,3, "TOTAL")
            hoja.write(fila,4, total_gastos)

            fila += 2
            total_pagos_monto = 0
            if total_pagos:
                for pago in total_pagos:
                    forma_pago = total_pagos[pago]['nombre']
                    total_pago = total_pagos[pago]['total']
                    hoja.write(fila, 2, forma_pago)
                    if forma_pago == "DOLARES":
                        hoja.write(fila, 3, str(conversion_dolar))
                    hoja.write(fila, 4, total_pago)
                    total_pagos_monto += total_pago
                    fila += 1

            rango_resumen = "B"+str(fila)+":D"+str(fila)
            sobrante_faltante = total_efectivo - total_pagos_monto
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
