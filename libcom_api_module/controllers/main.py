# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
from werkzeug.exceptions import abort
import requests
import json

class LibcomController(http.Controller):
    

    #AUTHENTICATION
   
    @http.route('/web/session/authenticate', type='json', auth='none') #endopoint for authentication
    def authenticate(self, db, login, password, base_location=None):
        request.session.authenticate(db, login, password)
        return request.env['ir.http'].session_info([])

    
    
    
    
    #CREATE CONTRIBUTOR


    @http.route('/api/create_contribua', type='json', auth='user') 
    def create_contribua(self, **rec):
        if request.jsonrequest:

            
            
            
            #CREATE NEW CREDIT CARD
            
            if rec['payment_method'] == 'credit_card':
                vals_card = {
                    'card_number' : rec['card_number'],
                    'card_expiration_date' : rec['card_expiration_date'],
                    'card_holder_name' : rec['card_holder_name'],
                    'card_cvv' : rec['card_cvv'],
                }
                
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
                    abort(400, str(response.json()))
                
                credit_card = response.json()
                







            #CREATE / SELECT CONTRIBUTOR

            vals_res = {
                    'name' : rec['name'],
                    'email' : rec['email'],
                    'l10n_br_cnpj_cpf' : rec['l10n_br_cnpj_cpf']
                }
            
            

            # if CPF Exist in database, use existing res.partner:
            contributor = request.env['res.partner'].sudo().search([('l10n_br_cnpj_cpf', '=', vals_res['l10n_br_cnpj_cpf'])])
            
            
            #If payment_method = credit_card, save card_id

            if contributor and rec['payment_method'] == 'credit_card':
                contributor.id_customer_pagarme = credit_card['id']
            
            


            #else, create new contributor
            else:
                if rec['payment_method'] == 'credit_card':
                    vals_res['id_customer_pagarme'] = credit_card['id']
                contributor = request.env['res.partner'].sudo().create(vals_res)
        


            #fetch subscription data
            vals_subscription = {
                'name': "subscription " + rec['name'],
                'partner_id' : contributor.id,
                'stage_id': 2
            }
            
            #create subscription
            new_subscription = request.env['sale.subscription'].sudo().create(vals_subscription)

            product = request.env['product.product'].sudo().search([('default_code', '=', 'Subscription')])
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
            request.env['sale.subscription.line'].sudo().create(vals_subscription_line)
            
            #Fatura
            
            invoice_method = new_subscription.sudo().recurring_invoice()





            #CREATE CUSTOMER @ PAGARNE
            headers = {
                'Content-type': 'application/json',
            }
            
            aquirer = request.env['payment.acquirer'].sudo().search([('provider', '=', 'pagarme')])
            query_params = {
                'api_key': aquirer.pagarme_api_key,
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
                     'number': contributor.l10n_br_cnpj_cpf,
                }],
                

            }
            url = 'https://api.pagar.me/1/customers'
            result = None
            
            #
            # if contributor.id_customer_pagarme:
            #     vals = {
            #         'name': contributor.name,
            #         'email': contributor.email,
            #     }
            #     url = url + '/' + contributor.id_customer_pagarme
            #     response = requests.put(url, data=json.dumps(vals), params=query_params, headers=headers)
            #     if not response.ok:
            #         abort(400, str(response.json()['errors'][0]['message']+ "line 147"))
            #     response.raise_for_status()
                
            if not contributor.id_customer_pagarme:
                response = requests.post(url, data=json.dumps(contributor_vals), params=query_params, headers=headers)
                if not response.ok:
                    abort(400, str(response.json()))
                response.raise_for_status()
                result = response.json()
                #contributor.id_customer_pagarme = result['id']
            
            #self.env.cr.commit()

            # base_url = (
            #     self.env["ir.config_parameter"].sudo().get_param("web.base.url")
            # )
            

            #CREATE TRANSACTION - SECOND API CALL TO PAGARME
            
            trx_values = {
                'amount': int(rec['monthly_donation'] * 100),
                'payment_method': rec['payment_method'],
                #'postback_url': '%s/payment/process' % base_url,
                'async': False,
                'installments': 1,
                'soft_descriptor': '',
                #'reference_key': values.get('reference_key'),
                'customer': contributor_vals,
                'card_id': credit_card['id'] if rec['payment_method'] == 'credit_card' else None,
                'card_holder_name': contributor.name,
                
                #REMEMBER TO CHANGE THIS
                'billing': {
                    "name": contributor.name,
                    "address": {
                        "country": str(contributor.country_id.code).lower(),
                        "state": str(contributor.state_id.code).lower(),
                        "city": str(contributor.city_id).lower(),
                        "neighborhood": str(contributor.l10n_br_district),
                        "street": str(contributor.street),
                        "street_number": str(contributor.street),
                        "zipcode": str(contributor.l10n_br_number)
                    }  
                },
                
                #Talk with Mateus/Libcom about what to return to contributors
                "items": [
                        {
                        "id": "subsrciption",
                        "title": "Libcom Subscription", #new_subscription.name #add here the invoice_origin,
                        "unit_price": rec['monthly_donation'],
                        "quantity": "1",
                        "tangible": False 
                        }],
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
            url = 'https://api.pagar.me/1/transactions'
            response = requests.post(
                url, data=json.dumps(trx_values), headers=headers, params=query_params
            )
            if not response.ok:
                abort(400, str(response.json()))
            



            # AUTOMATIZE INVOICE #
            #if we the credit card is confirmed, we need to automatically register the payment on the invoice
            #if it is boleto, we just leave the invoice, and when we get a post back, 
            invoice = request.env['account.move'].sudo().search([('invoice_origin', '=', new_subscription.code)])
            

            #IF CREDIT CARD AND "PAID", CONFIRM INVOICE
            if rec['payment_method'] == 'credit_card':
                if response.json()['status'] == 'paid':
                    payment = invoice.action_invoice_register_payment()
                    
                    #request.env['account.payment'].browse('')

            

            # invoice.action_invoice_register_payment('amount'=)
            data = response.json()

            
            #return id on all objects created
            args = {'succes': True, 
            'message': 'Success', 
            'partner': contributor.id, 
            "subscription ID": new_subscription,
            "subscription object": type(new_subscription),
            "invoice": invoice.id,
            "info": response.json()
            }

        return args

            #create first recurring invoice. This methid doesnt return the invoice id, 
            #need to inherit the model sale.subscription and have the function return the invoice id.
            # new_invoice = request.env['account.subscription'].sudo().recurring_invoice([new_subscription.id])

            # request.env['account.subscription'].sudo().action_invoice_sent([new_invoice.id])

            #fetch data to return 
            #args = {'succes': True, 'message': 'Success', 'id': new_contributor.id} #do we need to return anything to contribua.libcom?
     #return args