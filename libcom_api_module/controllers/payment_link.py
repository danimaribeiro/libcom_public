# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
from werkzeug.exceptions import abort
import requests
import json

class PaymentLink(http.Controller):

    @http.route('/api/charge_contributor', type='json', auth='user') 
    def create_payment_link(self, **rec):
        if request.jsonrequest:
            
            base_url = (self.env["ir.config_parameter"].sudo().get_param("web.base.url")
            link_values = {
                'amount': int(rec['monthly_donation'] * 100),
                "items": [{
                    "id": "subsrciption",
                    "title": "Libcom Subscription", #new_subscription.name #add here the invoice_origin,
                    "unit_price": rec['monthly_donation'],
                    "quantity": "1",
                    "tangible": False 
                }],
                'payment_config' : {
                    'boleto' : {
                        'enabled' : True,
                        'expires_in' : 20
                    },
                    'credit_card' : {
                        'enabled' : True,
                        'free_installments' : 4,
                        'interest_rate' : 25,
                        'max_installments' : 12
                    },
                    'default_payment_method' : 'boleto'
                },
                'max_orders' : 1,
                'expires_in' : 60,
                'postback_config' : {
                    'transactions' : '%s/api/pagarme/payment_link_postback' % base_url
                }
            }

            aquirer = request.env['payment.acquirer'].sudo().search([('provider', '=', 'pagarme')])
            query_params = {
                'api_key': aquirer.pagarme_api_key,
            }           
                
            headers = {
                'Content-Type': 'application/json',
            }
            url = 'https://api.pagar.me/1/payment_links'
            payment_link = requests.post(
            url, data=json.dumps(link_values), headers=headers, params=query_params
            )
            if not payment_link.ok:
                abort(400, str(payment_link.json()))

            return payment_link.json()['url']
            


