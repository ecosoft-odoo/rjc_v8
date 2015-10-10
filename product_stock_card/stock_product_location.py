#!/usr/bin/python
# -*- coding: utf-8 -*-
##############################################
#
# ChriCar Beteiligungs- und Beratungs- GmbH
# Copyright (C) ChriCar Beteiligungs- und Beratungs- GmbH
# all rights reserved
# created 2009-09-19 23:51:03+02
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs.
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company.
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/> or
# write to the Free Software Foundation, Inc.,
# 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
###############################################

from openerp import api, fields, models, _
from openerp.tools.sql import drop_view_if_exists

class stock_product_location(models.Model):
    _name = "stock.product.location"
    _description = "Product Stock By Location"
    _auto = False
    _table = "stock_product_location"

    location_id = fields.Many2one('stock.location', string='Location', select=True, required=True, readonly=True)
    product_id = fields.Many2one('product.product', string='Product', select=True, required=True, readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)
    #TODO: no such fields stock_real, stock_virtual now exits in location obj
#     qty_avaliable = fields.Float(related='location_id.stock_real', string="Quantity On Hand", readonly=True)
#     virtual_avaliable = fields.Float(related='location_id.stock_virtual', string="Forecasted Quantity", readonly=True)
    
    def init(self, cr):
        drop_view_if_exists(cr, 'stock_product_location')
        location_id = self.pool.get('ir.model.data').get_object_reference(cr, None, 'stock', 'stock_location_locations_virtual')[1]
        
        cr.execute("""create or replace view stock_product_location
                as
            SELECT ROW_NUMBER() OVER (ORDER BY location_id, product_id DESC) AS id, *
            FROM (
                SELECT
                 l.id AS location_id,product_id,
                 l.company_id
                FROM stock_location l,
                     stock_move i
                WHERE l.usage='internal'
                  AND i.location_dest_id = l.id
                  AND state != 'cancel'
                  AND i.company_id = l.company_id
                  AND l.active = True
                  And l.location_id <> %s
                UNION
                SELECT
                    l.id AS location_id ,product_id,
                l.company_id
                FROM stock_location l,
                     stock_move o
                WHERE l.usage='internal'
                  AND o.location_id = l.id
                  AND state != 'cancel'
                  AND o.company_id = l.company_id
                  AND l.active = True
                  And l.location_id <> %s
                  ) AS product_stock_location
                ORDER BY location_id, product_id DESC
                    ;""" % (str(location_id), str(location_id)))


class product_product(models.Model):
    _inherit = "product.product"
    
    stock_product_location_ids = fields.One2many('stock.product.location', 'product_id', string='Product by Stock', copy=False)

class stock_location(models.Model):
    _inherit = "stock.location"
    
    @api.model
    def _search_product_value(self, args, offset=0, limit=None, order=None, count=False):
        res_ids = self.search(args, offset, limit, order, count=count)
        loc_obj = self.browse(res_ids)
        res_ids = [x.id for x in loc_obj if x.stock_real != 0]
        return res_ids

    stock_product_location_ids = fields.One2many('stock.product.location', 'location_id', string='Product by Stock', copy=False)

