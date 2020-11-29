from odoo import http
from odoo.http import request
from werkzeug.exceptions import abort
import requests
import json


class PagarmePaymentLinkPostback(http.Controller):

    @http.route('/api/pagarme/payment_link_postback', method='post', type='http', auth='public', csrf=False)
    def pagarme_postback(self, **rec):

        print(rec)

        #if rec['current_status'] == 'paid': (awaiting business rule validation)
        #collect res.partner values from rec

        vals_res = {
            'name': rec['transaction[customer][name]'],
            'email': rec['transaction[customer][email]'],
            'l10n_br_cnpj_cpf': rec['transaction[customer][documents][0][number]'],
            'id_customer_pagarme': rec['transaction[card][id]'],
            'phone' : rec['transaction[customer][phone_numbers][0]'],
            'street' : rec['transaction[billing][address][street]'],
            'l10n_br_number' : rec['transaction[billing][address][street_number]'],
            'zip' : rec['transaction[billing][address][zipcode]'],
            'comment' : "Criado pela app Contribua " + rec['transaction[card][date_created]']
            #'state_id' : request.env['res.country.state'].sudo().search([('code', '=', rec['transaction[billing][address][state]'])]),
            #'l10n_br_district' : rec['transaction[billing][address][neighborhood]'], (Many2one, requires domain)

        }
        
        state = request.env['res.country.state'].sudo().search([('code', '=', rec['transaction[billing][address][state]'])])
        print(state)


        print(vals_res)
        # CONTRIBUTIR CREATION / Selection
        contributor = request.env['res.partner'].sudo().search(
            [('l10n_br_cnpj_cpf', '=', vals_res['l10n_br_cnpj_cpf'])])
        if not contributor:
            contributor = request.env['res.partner'].sudo().create(vals_res)


        #IF CC, STORE CARD ID
        contributor.id_customer_pagarme = rec['transaction[card][id]']
        
        print(contributor.id_customer_pagarme)

        # # SUBSCRIPTION CREATION
        vals_subscription = {
            'name': "subscription " + rec['transaction[customer][name]'],
            'partner_id': contributor.id,
            'stage_id': 2
        }
        subscription = request.env['sale.subscription'].sudo().create(vals_subscription)
        print(subscription)


        #Fetch product for donation
        product = request.env['product.product'].sudo().search([('default_code', '=', 'Subscription')])
        if not product:
            vals_product = {
                'name' : "Subscrição",
                'code' : "Subscription",
                'description' : 'ATTENCÃO: Criado automatico pela API, segurar que valores são corretos'
            }
            request.env['product.product'].sudo().create(vals_product)
            print('created new product')
        print(product.id)


        #fech subscription line data,
        vals_subscription_line = {
                'product_id': product.id,  
                'analytic_account_id': subscription.id,
                'price_unit': float(rec['transaction[amount]']) / 100,
                'uom_id': 1,
        }
        print(vals_subscription_line)
        
        #subscription_line
        request.env['sale.subscription.line'].sudo().create(vals_subscription_line)

        #Create first invoice
        subscription.sudo().recurring_invoice()
        invoice = request.env['account.move'].sudo().search([('invoice_origin', '=', subscription.code)])

        # boleto or cc? If CC, the first invoice is paid. Therefor, if cc and 'status' = paid, 
        # we will run the method for transaction, or set the status paid. 
