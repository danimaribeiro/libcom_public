# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
from werkzeug.exceptions import abort
import requests
import json

class PagarmePaymentLinkPostback(http.Controller):

    @http.route('/api/pagarme/payment_link_postback', type='json', auth='none') #endopoint for authentication
    def pagarme_postback(self, **rec):
        if request.jsonrequest:
        

            
            # contributor = request.env['res.partner'].sudo().search([('l10n_br_cnpj_cpf', '=', rec['l10n_br_cnpj_cpf'])])
            # contributor.id_customer_pagarme = rec['card']['id']
            
            # #post something to Libcom
            # response = {
            #     'status': rec['status']
            # }
            # # 
            # # request.post(url+route, query_params, response)