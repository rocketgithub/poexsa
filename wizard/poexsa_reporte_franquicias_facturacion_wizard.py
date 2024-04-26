
# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.tools import convert
from datetime import datetime
import xlsxwriter
import base64
import io
import locale
import logging
import xmlrpc.client
#CONsidedar campo reporte_ventas_franquicia, solo esos productos mostrar
class PoexsaReporteFranquiciasFactWizard(models.TransientModel):
    _name = 'poexsa.reporte_franquicias_fact_wizard'

    def _default_franquicias(self):
        franquicias = []
        franquicia_ids = self.env['poexsa.franquicia'].search([])
        if franquicia_ids:
            franquicias = franquicia_ids.ids
        return franquicias

    fecha_inicio = fields.Datetime('Fecha inicio', required=True)
    fecha_fin = fields.Datetime('Fecha fin', required = True)
    franquicia_ids = fields.Many2many('poexsa.franquicia',string='Franquicias', required=True, default=_default_franquicias)
    name = fields.Char('Nombre archivo', size=32)
    archivo = fields.Binary('Archivo', filters='.xls')

    def obtener_resumen_factura_ventas(self, franquicia_ids):
        total_facturas = {}
        franquicia_regalias = {}
        venta_ids = self.env['sale.order'].search([('franquicia','!=', False),('invoice_ids','!=',False)])
        for franquicia in franquicia_ids:
            franquicia_regalias[franquicia.compania] = franquicia.regalia

        if venta_ids:
            for venta in venta_ids:
                franquicia = venta.franquicia
                if franquicia not in total_facturas:
                    total_facturas[franquicia] = {'franquicia': franquicia, 'total_factura_sin_iva': 0, 'total_factura_con_iva': 0, 'regalia': 0}

                for factura in venta.invoice_ids:
                    total_facturas[franquicia]['total_factura_sin_iva'] += factura.amount_untaxed
                    total_facturas[franquicia]['total_factura_con_iva'] += factura.amount_total

        if len(total_facturas) > 0:
            for franquicia in total_facturas:
                regalia = (total_facturas[franquicia]['total_factura_sin_iva'] * franquicia_regalias[franquicia]) / 100
                total_facturas[franquicia]['regalia'] = regalia

        return total_facturas

    def abrir_reporte_lista(self):
        productos = self.obtener_productos()
        categorias = self.obtener_categorias()
        franquicias = {}
        for w in self:
            resumen_facturas_ventas = self.obtener_resumen_factura_ventas(w.franquicia_ids)
            for franquicia in w.franquicia_ids:
                franquicias[franquicia.compania] = franquicia.id

            if len(resumen_facturas_ventas):
                for franquicia in resumen_facturas_ventas:
                    franquicia_id = franquicias[franquicia]
                    total_factura_sin_iva = resumen_facturas_ventas[franquicia]['total_factura_sin_iva']
                    total_factura_con_iva = resumen_facturas_ventas[franquicia]['total_factura_con_iva']
                    regalia = resumen_facturas_ventas[franquicia]['regali']
                    info = {
                        'franquicia_id': franquicia_id,
                        'total_factura_sin_iva': total_factura_sin_iva,
                        'total_factura_con_iva': total_factura_con_iva,
                        'regalia': regalia
                    }
                    self.env['poexsa.reporte_franquicia_facturacion'].create(info)

        return {
            'name': _('Regalias'),
            'res_model': 'poexsa.reporte_franquicia_facturacion',
            'view_mode': 'tree',
            'view_ids': [self.env.ref('poexsa.view_poexa_reporte_franquicia_facturacion_tree').id],
            'type': 'ir.actions.act_window',
            'target': 'main',
            'context': "{'create': False}"
        }

    def print_report_excel(self):
        for w in self:
            f = io.BytesIO()
            libro = xlsxwriter.Workbook(f)
            hoja = libro.add_worksheet('Reporte franquicia facturacion')
            resumen_facturas_ventas = self.obtener_resumen_factura_ventas(w.franquicia_ids)

            hoja.write(0, 0, w.fecha_inicio)
            hoja.write(0, 1, "al")
            hoja.write(0, 2,w.fecha_fin)

            hoja.write(3, 0, 'Franquicia')
            hoja.write(3, 0, 'Total sin IVA')
            hoja.write(3, 0, 'Total con IVA')
            hoja.write(3, 0, 'Regalía')
            fila = 4
            if len(resumen_facturas_ventas) > 0:
                for franquicia in resumen_facturas_ventas:
                    total_factura_sin_iva = resumen_facturas_ventas[franquicia]['total_factura_sin_iva']
                    total_factura_con_iva = resumen_facturas_ventas[franquicia]['total_factura_con_iva']
                    regalia = resumen_facturas_ventas[franquicia]['regalia']
                    hoja.write(fila, 0, franquicia)
                    hoja.write(fila, 1, total_factura_sin_iva)
                    hoja.write(fila, 2, total_factura_con_iva)
                    hoja.write(fila, 3, total_factura_con_iva)
                    fila += 1

            libro.close()
            datos = base64.b64encode(f.getvalue())
            self.write({'archivo':datos, 'name':'reporte_franquicia_facturacion.xlsx'})

        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'poexsa.reporte_franquicias_facturacion_wizard',
            'res_id': self.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
