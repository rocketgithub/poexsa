# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
import xmlrpc.client
import logging

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    franquicia_id = fields.Many2one('poexsa.franquicia','Francquicia')
    franquicia_so = fields.Char('Franquicia SO')

    def generar_so(self):
        for compra in self:
            if compra.order_line and compra.franquicia_id:
                url = compra.franquicia_id.url
                base_datos = compra.franquicia_id.base_datos
                usuario = compra.franquicia_id.usuario
                contrasenia = compra.franquicia_id.contrasenia
                existe_venta = compra.existe_venta(url, base_datos, usuario, contrasenia)
                if len(existe_venta) > 0:
                    raise ValidationError(_("Orden de compra actual ya fue registrada con anterioridad en la franquicia destino"))

                compra.crear_venta(url, base_datos, usuario, contrasenia)

                return True
        return True

    def obtener_productos(self, url, base_datos, usuario, contrasenia):
        productos = {}
        return productos

    def existe_venta(self, url, base_datos, usuario, contrasenia):
        ventas = []
        # modelo = xmlrpc.client.ServerProxy('%s/xmlrpc/2/common' % url)
        logging.warning(url)
        common = xmlrpc.client.ServerProxy('%s/xmlrpc/2/common' % url)
        version = common.version()
        # logging.warning(version)
        # modelo = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
        lista_ventas = modelo.execute_kw(base_datos, usuario, contrasenia, 'sale.order', 'search', [[['franquicia_po', '=', self.name]]], {'offset': 10, 'limit': 5})
        if len(lista_ventas):
            ventas = lista_ventas
        return ventas

    def crear_venta(self, url, base_datos, usuario, contrasenia):
        venta = False
        modelo = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
        lineas = []
        for linea in self.order_line:
            datos = {
                'product_id': productos[linea.product_id.default_code],
                'product_uom_qty': linea.product_qty,
                'name': linea.name,
            }
            lineas.append((0,0, datos))
        venta_id = modelo.execute_kw(base_datos, usuario, contrasenia, 'sale.order', 'create', [{'partner_id': 5, 'franquicia_po': self.name,'order_line': lineas}])
        if venta_id:
            venta = venta_id

        return venta
