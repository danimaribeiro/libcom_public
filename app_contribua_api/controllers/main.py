# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request

class LibcomController(http.Controller):
    
    @http.route('/web/session/authenticate', type='json', auth='none') #endopoint for authentication
    def authenticate(self, db, login, password, base_location=None):
        request.session.authenticate(db, login, password)
        return request.env['ir.http'].session_info([])
    

    @http.route('/api/get_contacts/', type='json', auth='user') #endopoint for getting a list of contacts
    def get_partners(self):
        contacts_rec = request.env['sale.subscription'].search([])
        contacts = []
        for rec in contacts_rec:
            vals = {
                'id': rec.id,
                'name': rec.name,
                'partner_id': rec.partner_id
            }
            contacts.append(vals)
        data = {'status': 200, 'message': 'Success', 'response': contacts}
        return data


    @http.route('/api/create_contribua/', type='json', auth='user') #endopoint for creating a contributor
    def create_contribua(self, **rec):
        if request.jsonrequest:
            
            # fetch partner data, create res.partner
            if rec['name']: #fordi dette er obligatorisk
                vals_res = {
                    'name' : rec['name'],
                    'email' : rec['email'],
                    #'l10n_br_cnpj_cpf' : rec['l10n_br_cnpj_cpf'] not installed Brazil on db4
                }
            
            #create contributor. Has to be changed to search for 
            new_contributor = request.env['res.partner'].sudo().create(vals_res)
            #new_contributor = request.env['res.partner'].sudo().search_find(vals_res[l10n_br_cnpj_cpf])
            
            #fetch subscription data
            vals_subscription = {
                'name': "subscription " + rec['name'],
                'partner_id' : new_contributor.id,
                'stage_id': 2
            }
            
            # #create subscription
            # new_subscription = request.env['sale.subscription'].sudo().create(vals_subscription)

            # #fech subscription line data,
            # vals_subscription_line = {
            #     'product_id': "6", 
            #     'analytic_account_id': new_subscription.id,
            #     'price_unit': rec['monthly_donation'],
            #     'uom_id': 1,
            # }
            # #subscription_line
            # new_subscription_line = request.env['sale.subscription.line'].sudo().create(vals_subscription_line)
            
            # #invoice
            # new_invoice = new_subscription.sudo().recurring_invoice()

            args = {'succes': True, 
            'message': 'Success', 
            'partner': new_contributor.id, 
            "subscription ID": new_subscription.id,
            # "subscription object": type(new_subscription),
            # "invoice": new_invoice
            }
        return args

            #create first recurring invoice. This methid doesnt return the invoice id, 
            #need to inherit the model sale.subscription and have the function return the invoice id.
            # new_invoice = request.env['account.subscription'].sudo().recurring_invoice([new_subscription.id])

            # request.env['account.subscription'].sudo().action_invoice_sent([new_invoice.id])

            #fetch data to return 
            #args = {'succes': True, 'message': 'Success', 'id': new_contributor.id} #do we need to return anything to contribua.libcom?
     #return args