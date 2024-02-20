# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
import xmlrpc.client
import logging

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    franquicia_id = fields.Many2one('poexsa.franquicia','Francquicia')
    franquicia_so = fields.Char('Franquicia SO')

    def obtener_empresa(self, url, base_datos, usuario, contrasenia, nombre):
        empresa_id = False
        modelo = xmlrpc.client.ServerProxy('%s/xmlrpc/2/object' % url)
        empresa = modelo.execute_kw(base_datos, usuario, contrasenia, 'res.company', 'search', [[['name', '=', nombre]]])
        if empresa:
            empresa_id = empresa[0]
        return empresa_id

    def obtener_cliente(self, url, base_datos, usuario, contrasenia, nombre):
        cliente_id = False
        modelo = xmlrpc.client.ServerProxy('%s/xmlrpc/2/object' % url)
        cliente = modelo.execute_kw(base_datos, usuario, contrasenia, 'res.partner', 'search', [[['name', '=', nombre]]])
        if cliente:
            cliente_id = cliente[0]
        return cliente_id

    def generar_so(self):
        for compra in self:
            if compra.order_line and compra.franquicia_id:
                url = compra.franquicia_id.url
                base_datos = compra.franquicia_id.base_datos
                usuario = compra.franquicia_id.usuario
                contrasenia = compra.franquicia_id.contrasenia
                empresa = compra.franquicia_id.compania
                cliente = compra.franquicia_id.compania

                empresa = compra.obtener_empresa(url, base_datos, usuario, contrasenia, empresa)
                if empresa == False:
                    raise ValidationError(_("Compañia invalida"))

                cliente = compra.obtener_cliente(url, base_datos, usuario, contrasenia, cliente)
                if cliente == False:
                    raise ValidationError(_("Cliente invalida"))

                existe_venta = compra.existe_venta(url, base_datos, usuario, contrasenia, empresa)
                if len(existe_venta) > 0:
                    raise ValidationError(_("Orden de compra actual ya fue registrada con anterioridad en la franquicia destino"))

                venta_id = compra.crear_venta(url, base_datos, usuario, contrasenia, empresa, cliente)
                if venta_id == False:
                    raise ValidationError(_("No se pudo crear presupuesto"))

        return True

    def obtener_productos(self, url, base_datos, usuario, contrasenia):
        productos = {}
        modelo = xmlrpc.client.ServerProxy('%s/xmlrpc/2/object' % url)
        producto_ids = modelo.execute_kw(base_datos, usuario, contrasenia, 'product.product', 'search', [[['sale_ok', '=', True],['purchase_ok','=',True]]])
        lista_productos = modelo.execute_kw(base_datos, usuario, contrasenia, 'product.product', 'read', [producto_ids], {'fields': ['name', 'id', 'default_code']})

        if len(lista_productos) > 0:
            for producto in lista_productos:
                producto_default_code = producto['default_code']
                producto_id = producto['id']
                if producto_default_code not in productos:
                    productos[producto_default_code] = producto_id
        return productos

    def existe_venta(self, url, base_datos, usuario, contrasenia, empresa):
        ventas = []
        modelo = xmlrpc.client.ServerProxy('%s/xmlrpc/2/object' % url)
        lista_ventas = modelo.execute_kw(base_datos, usuario, contrasenia, 'sale.order', 'search', [[['franquicia_po', '=', self.name],['company_id', '=', empresa]]], {'offset': 10, 'limit': 5})

        if len(lista_ventas):
            ventas = lista_ventas
        return ventas

    def crear_venta(self, url, base_datos, usuario, contrasenia, empresa, cliente):
        venta = False
        modelo = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
        lineas = []
        productos = self.obtener_productos(url, base_datos, usuario, contrasenia)

        for linea in self.order_line:
            datos = {
                'product_id': productos[linea.product_id.default_code],
                'product_uom_qty': linea.product_qty,
                'name': linea.name,
            }
            lineas.append((0,0, datos))

        venta_id = modelo.execute_kw(base_datos, usuario, contrasenia, 'sale.order', 'create', [{'partner_id': cliente, 'franquicia_po': self.name,'order_line': lineas, 'company_id': empresa}])

        if venta_id:
            venta = venta_id
        return venta
