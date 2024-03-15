
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

class PoexsaReporteFranquiciasWizard(models.TransientModel):
    _name = 'poexsa.reporte_franquicias_wizard'

    def _default_grupo_cuadre(self):
        grupo_cuadre = []
        grupo_cuadre_ids = self.env['poexsa.grupo_cuadre'].search([])
        if grupo_cuadre_ids:
            grupo_cuadre = grupo_cuadre_ids.ids
        return grupo_cuadre

    def _default_franquicias(self):
        franquicias = []
        franquicia_ids = self.env['poexsa.franquicia'].search([])
        if franquicia_ids:
            franquicias = franquicia_ids.ids
        return franquicias

    fecha_inicio = fields.Datetime('Fecha inicio', required=True)
    fecha_fin = fields.Datetime('Fecha fin', required = True)
    grupo_cuadre_ids = fields.Many2many('product.category',string='Categoría', required=True, default=_default_grupo_cuadre)
    franquicia_ids = fields.Many2many('poexsa.franquicia',string='Franquicias', required=True, default=_default_franquicias)
    name = fields.Char('Nombre archivo', size=32)
    archivo = fields.Binary('Archivo', filters='.xls')


    def obtener_categorias(self):
        categorias = {}
        productos = self.env['product.product'].search([('sale_ok','=',True),('purchase_ok','=', True),('categ_id','!=', False)])
        for producto in productos:
            categorias[producto.display_name] = producto.categ_id.name
        return categorias

    #retorna los productos agrupados por categorias
    def obtener_productos_categoria(self, franquicia_ids):
        productos_categorias = {}
        datos_franquicia = {}
        for franquicia in franquicia_ids:
            datos_franquicia[franquicia.name] = {'nombre': franquicia.name, 'cant_comprada': 0, 'cant_vendida': 0}

        productos = self.env['product.product'].search([('sale_ok','=',True),('categ_id','!=', False)])
        if productos:
            for producto in productos:
                if producto.categ_id.name not in productos_categorias:
                    productos_categorias[producto.categ_id.name] = {'productos': {}, 'categoria': producto.categ_id.name}

                if producto.display_name not in productos_categorias[producto.categ_id.name]['productos']:
                    productos_categorias[producto.categ_id.name]['productos'][producto.display_name] = datos_franquicia
                # productos_categorias[producto.categ_id.name]['productos'][producto.display_name] = {'cant_vendida': 0, 'cant_comprada': 0}

        return productos_categorias

    def obtener_cantidad_vendida(self, url, base_datos, usuario, contrasenia, fecha_inicio, fecha_fin, empresa):
        ventas = {}
        modelo = xmlrpc.client.ServerProxy('%s/xmlrpc/2/object' % url)
        linea_venta_ids = modelo.execute_kw(base_datos, usuario, contrasenia, 'pos.order.line', 'search', [[['qty', '>', 0],['create_date','>=', fecha_inicio],['create_date','<=', fecha_fin],['company_id','=',empresa]]])
        lista_ventas = modelo.execute_kw(base_datos, usuario, contrasenia, 'pos.order.line', 'read', [linea_venta_ids], {'fields': ['name', 'id', 'display_name','qty']})

        if len(lista_ventas) > 0:
            for linea_venta in lista_ventas:
                producto = linea_venta['display_name']
                cantidad = linea_venta['qty']
                if producto not in ventas:
                    ventas[producto] = 0
                ventas[producto] += cantidad
        return ventas

    def obtener_cantidad_comprada(self, url, base_datos, usuario, contrasenia, fecha_inicio, fecha_fin, empresa):
        compras = {}
        modelo = xmlrpc.client.ServerProxy('%s/xmlrpc/2/object' % url)
        linea_compra_ids = modelo.execute_kw(base_datos, usuario, contrasenia, 'purchase.order.line', 'search', [[['product_qty', '>', 0],['date_order','>=', fecha_inicio],['date_order','<=', fecha_fin],['company_id','=',empresa]]])
        lista_compras = modelo.execute_kw(base_datos, usuario, contrasenia, 'purchase.order.line', 'read', [linea_compra_ids], {'fields': ['name', 'id', 'display_name','product_qty']})

        if len(lista_compras) > 0:
            for linea_compra in lista_compras:
                producto = linea_compra['display_name']
                cantidad = linea_compra['product_qty']
                if producto not in compras:
                    compras[producto] = 0
                compras[producto] += cantidad
        return compras

    def credenciales_franquicia(self, franquicia):
        crendenciales = {}

    def obtener_resumen_productos(self, wizard):
        fecha_inicio = wizard.fecha_inicio
        fecha_fin = wizard.fecha_fin
        productos_categorias = self.obtener_productos_categoria(wizard.franquicia_ids)
        categorias = self.obtener_categorias()

        for franquicia in wizard.franquicia_ids:
            nombre = franquicia.name
            url = franquicia.url
            base_datos = franquicia.base_datos
            usuario = franquicia.usuario
            contrasenia = franquicia.contrasenia
            empresa = franquicia.compania
            ventas = self.obtener_cantidad_vendida(url, base_datos, usuario, contrasenia, fecha_inicio, fecha_fin, empresa)
            compras = self.obtener_cantidad_comprada(url, base_datos, usuario, contrasenia, fecha_inicio, fecha_fin, empresa)

            if len(ventas) > 0:
                for producto in ventas:
                    cantidad = ventas[producto]
                    if producto in categorias:
                        categoria_producto = categorias[producto]
                        for pc in productos_categorias:
                            if pc == categoria_producto:
                                for prod in productos_categorias[pc]['productos']:
                                    if producto == prod:
                                        productos_categorias[pc]['productos'][prod][nombre]['cant_vendida'] = cantidad


            if len(compras) > 0:
                for producto in compras:
                    cantidad = compras[producto]
                    if producto in categorias:
                        categoria_producto = categorias[producto]
                        for pc in productos_categorias:
                            if pc == categoria_producto:
                                for prod in productos_categorias[pc]['productos']:
                                    if producto == prod:
                                        productos_categorias[pc]['productos'][prod][nombre]['cant_vendida'] = cantidad

        return productos_categorias



    def print_report_excel(self):
        for w in self:
            dict = {}


            f = io.BytesIO()
            libro = xlsxwriter.Workbook(f)
            hoja = libro.add_worksheet('Reporte ventas compras')
            resumen_productos = self.obtener_resumen_productos(w)
            hoja.write(0, 0, w.fecha_inicio)
            hoja.write(0, 1, "al")
            hoja.write(0, 2,w.fecha_fin)

            fila = 4
            columna = 0
            for categoria in resumen_productos:
                hoja.write(fila, columna, categoria)
                fila += 1
                for producto in resumen_productos[categoria]['productos']:
                    hoja.write(fila, 1, producto)

                    columna_productos = 2
                    for franquicia in resumen_productos[categoria]['productos'][producto]:
                        #Agregamos el nombre de franquicias
                        columna_franquicia = 2
                        hoja.write(3, columna_franquicia, franquicia)
                        cant_vendida = resumen_productos[categoria]['productos'][producto][franquicia]['cant_vendida']
                        cant_comprada = resumen_productos[categoria]['productos'][producto][franquicia]['cant_comprada']
                        hoja.write(fila, columna_productos, cant_vendida)
                        columna_productos += 1
                        hoja.write(fila, columna_productos, cant_comprada)
                        columna_productos += 1
                        columna_franquicia + 2
                    fila += 1


            libro.close()
            datos = base64.b64encode(f.getvalue())
            self.write({'archivo':datos, 'name':'reporte_ventas_compras.xlsx'})

        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'poexsa.reporte_franquicias_wizard',
            'res_id': self.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
