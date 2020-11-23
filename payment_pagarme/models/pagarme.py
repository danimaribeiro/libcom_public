import re
import json
import logging
import requests

from odoo import api, fields, models
from odoo.exceptions import UserError
from werkzeug import urls


_logger = logging.getLogger(__name__)


class PagarmeAcquirer(models.Model):
    _inherit = "payment.acquirer"

    provider = fields.Selection(selection_add=[("pagarme", "PagarMe")])
    pagarme_api_key = fields.Char("PagarMe API-key")

    def pagarme_form_generate_values(self, values):
        if not self.pagarme_api_key:
            raise UserError('Por favor configure a API Key')
        
        pagarme.authentication_key(self.pagarme_api_key)
        partner_id = values.get('partner_id')

        partner = self.env['res.partner'].browse(partner_id)
        headers = {
            'Content-type': 'application/json',
        }
        query_params = {
            'api_key': self.pagarme_api_key,
        }
        partner_vals = {
            'name': partner.name,
            'email': partner.email,
            'external_id': '00000' + str(partner.id),
            'type': 'corporation' if partner.is_company else 'individual',
            'country': partner.country_id.code.lower(),
            'phone_numbers': [
                '+5548999990000',
            ],
            'documents': [{
                'type': 'cnpj' if partner.is_company else 'cpf',
                'number': re.sub('[^0-9]', '', partner.l10n_br_cnpj_cpf or ''),
            }]
        }
        url = 'https://api.pagar.me/1/customers'
        result = None
        
        
        if partner.id_customer_pagarme:
            vals = {
                'name': partner.name,
                'email': partner.email,
            }
            url = url + '/' + partner.id_customer_pagarme
            response = requests.put(url, data=json.dumps(vals), params=query_params, headers=headers)
            response.raise_for_status()
            
        else:
            customer = pagarme.customer.create(partner_vals)
            #response = requests.post(url, data=json.dumps(partner_vals), params=query_params, headers=headers)
            response.raise_for_status()
            result = response.json()
            partner.id_customer_pagarme = result['id']
        
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
            'customer': partner_vals,
        }

        headers = {
            'Content-Type': 'application/json',
        }
        url = 'https://api.pagar.me/1/transactions'
        response = requests.post(
            url, data=json.dumps(values), headers=headers, params=query_params
        )

        data = response.json()

        return {
            "checkout_url": urls.url_join(
                base_url, "/pagarme/checkout/redirect"),
            "secure_url": data['boleto_url']
        }


class TransactionPicPay(models.Model):
    _inherit = "payment.transaction"

    pagarme_url = fields.Char(string="Fatura PicPay", size=300)

    @api.model
    def _pagarme_form_get_tx_from_data(self, data):
        acquirer_reference = data.get("data[id]")
        tx = self.search([("acquirer_reference", "=", acquirer_reference)])
        return tx[0]

    def _pagarme_form_validate(self, data):
        status = data.get("data[status]")

        if status in ('paid', 'partially_paid', 'authorized'):
            self._set_transaction_done()
            return True
        elif status == 'pending':
            self._set_transaction_pending()
            return True
        else:
            self._set_transaction_cancel()
            return False
