from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    id_customer_pagarme = fields.Char()