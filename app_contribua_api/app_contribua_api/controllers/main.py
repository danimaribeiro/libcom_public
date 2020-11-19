# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
from werkzeug.exceptions import abort
import requests
import json

class LibcomController(http.Controller):
    

    @http.route('/web/session/authenticate', type='json', auth='none') #endopoint for authentication
    def authenticate(self, db, login, password, base_location=None):
        request.session.authenticate(db, login, password)
        return request.env['ir.http'].session_info([])


    @http.route('/api/create_contribua/', type='json', auth='user') #endopoint for creating a contributor
    def create_contribua(self, **rec):
        if request.jsonrequest:

            #call Pagarme to create card_hash:
            
            #pega valores do rec, coloca no outro variavel
            vals_card = {
                'card_number' : rec['card_number'],
                'card_expiration_date' : rec['card_expiration_date'],
                'card_holder_name' : rec['card_holder_name'],
                'card_cvv' : rec['card_cvv'],
            }
            #pega a chave do api
            aquirer = request.env['payment.acquirer'].sudo().search([('provider', '=', 'pagarme')])
            if not aquirer:
                abort(404, 'Please add a pagarme API key in Odoo')
            
            query_params = {
            'api_key': aquirer.pagarme_api_key,
            }
            
            headers = {
            'Content-Type': 'application/json',
            }

            url = 'https://api.pagar.me/1/cards'
            
            response = requests.post(
            url, data=json.dumps(vals_card), headers=headers, params=query_params
            )

            if not response.ok:
                abort(400, str(response.json()['errors'][0]['message']))
            
            
            credit_card = response.json()
            
            #salvar valor no res partner
            credit_card['id']


            # fetch partner data to create/search res.partner 
            #if rec['name']: #set up conditions like this for all params
            vals_res = {
                    'name' : rec['name'],
                    'email' : rec['email'],
                    #'card_hash' : card_hash
                    'l10n_br_cnpj_cpf' : rec['l10n_br_cnpj_cpf']
                }
            # elif:
            #     abort(404, 'please provide partner name')

            # if CPF Exist in database, use existing res.partner:
            contributor = request.env['res.partner'].sudo().search(vals_res['l10n_br_cnpj_cpf'])
            if contributor:
                
                contributor.id_customer_pagarme = credit_card['id']
            
            
            #else, create new contributor
            else:
                vals_res['customer_pagarme'] = credit_card['id']
                contributor = request.env['res.partner'].sudo().create(vals_res)
        


            #fetch subscription data
            vals_subscription = {
                'name': "subscription " + rec['name'],
                'partner_id' : contributor.id,
                'stage_id': 2
            }
            
            #create subscription
            new_subscription = request.env['sale.subscription'].sudo().create(vals_subscription)

            product = request.env['product.produt'].sudo().search([('default_code', '=', 'Subscription')])
            if not product:
                abort(404, 'please create product "Subscription" in Odoo database')
            
            #fech subscription line data,
            vals_subscription_line = {
                'product_id': product.id,  
                'analytic_account_id': new_subscription.id,
                'price_unit': rec['monthly_donation'],
                'uom_id': 1,
            }
            #subscription_line
            new_subscription_line = request.env['sale.subscription.line'].sudo().create(vals_subscription_line)
            
            #Fatura
            new_invoice = new_subscription.sudo().recurring_invoice()

            #trx = call payment.transaction
            headers = {
                'Content-type': 'application/json',
            }
            query_params = {
                'api_key': self.pagarme_api_key,
            }
            contributor_vals = {
                'name': contributor.name,
                'email': contributor.email,
                'external_id': '00000' + str(contributor.id),
                'type': 'corporation' if contributor.is_company else 'individual',
                'country': contributor.country_id.code.lower(),
                'phone_numbers': [
                    '+5548999990000',
                ],
                'documents': [{
                    'type': 'cnpj' if contributor.is_company else 'cpf',
                    'number': re.sub('[^0-9]', '', contributor.l10n_br_cnpj_cpf or ''),
                }]
            }
            url = 'https://api.pagar.me/1/customers'
            result = None
            
            
            if contributor.id_customer_pagarme:
                vals = {
                    'name': contributor.name,
                    'email': contributor.email,
                }
                url = url + '/' + contributor.id_customer_pagarme
                response = requests.put(url, data=json.dumps(vals), params=query_params, headers=headers)
                response.raise_for_status()
                
            else:
                customer = pagarme.customer.create(contributor)
                #response = requests.post(url, data=json.dumps(), params=query_params, headers=headers)
                response.raise_for_status()
                result = response.json()
                contributor.id_customer_pagarme = result['id']
            
            self.env.cr.commit()

            base_url = (
                self.env["ir.config_parameter"].sudo().get_param("web.base.url")
            )
            
            values = {
                'amount': int(values.get('amount') * 100),
                'payment_method': 'boleto',
                'postback_url': '%s/payment/process' % base_url,
                'async': False,
                'installments': 1,
                'soft_descriptor': '',
                'reference_key': values.get('reference_key'),
                'customer': contributor_vals,
            }

            headers = {
                'Content-Type': 'application/json',
            }
            url = 'https://api.pagar.me/1/transactions'
            response = requests.post(
                url, data=json.dumps(values), headers=headers, params=query_params
            )

            data = response.json()

            
            #return id on all objects created
            args = {'succes': True, 
            'message': 'Success', 
            'partner': contributor.id, 
            "subscription ID": new_subscription.id,
            "subscription object": type(new_subscription),
            "invoice": new_invoice
            }

        return args

            #create first recurring invoice. This methid doesnt return the invoice id, 
            #need to inherit the model sale.subscription and have the function return the invoice id.
            # new_invoice = request.env['account.subscription'].sudo().recurring_invoice([new_subscription.id])

            # request.env['account.subscription'].sudo().action_invoice_sent([new_invoice.id])

            #fetch data to return 
            #args = {'succes': True, 'message': 'Success', 'id': new_contributor.id} #do we need to return anything to contribua.libcom?
     #return args