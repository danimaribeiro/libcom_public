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

        partner_id = values.get('partner_id')
        partner = self.env['res.partner'].browse(partner_id)

        base_url = (
            self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        )
        url_postback = 'http://82db30ceac2e.ngrok.io'
        values = {
            "api_key": self.pagarme_api_key,
            'amount': int(values.get('amount') * 100),
            "items": [
                {
                    "id": "1",
                    "title": "Pagamento Ref: %s" % values.get('reference'),
                    "unit_price": int(values.get('amount') * 100),
                    "quantity": 1,
                    "tangible": False
                },
            ],
            "payment_config": {
                "boleto": {
                    "enabled": True,
                    "expires_in": 2880
                },
                "credit_card": {
                    "enabled": True,
                    "free_installments": 4,
                    "interest_rate": 25,
                    "max_installments": 12
                },
                "default_payment_method": "boleto"
            },
            "postback_config": {
                "orders": '%s/pagarme/notification' % url_postback,
                "transactions": '%s/pagarme/notification' % url_postback
            },
            "customer_config":{  
                "customer":{  
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
                },
                "billing":{  
                    "name": partner.name,
                    "address":{  
                        "country": partner.country_id.code.lower(),
                        "state": partner.state_id.code,
                        "city": partner.city_id.name,
                        "neighborhood": partner.l10n_br_district,
                        "street": partner.street,
                        "street_number": partner.l10n_br_number,
                        "zipcode": re.sub('[^0-9]', '', partner.zip or '')
                    }
                },
            },
            "max_orders": 1,
            "expires_in": 2880
        }

        headers = {
            'Content-type': 'application/json',
        }
        url = "https://api.pagar.me/1/payment_links"
        response = requests.post(
            url, data=json.dumps(values), headers=headers
        )

        data = response.json()

        return {
            "checkout_url": urls.url_join(
                base_url, "/pagarme/checkout/redirect"),
            "secure_url": data['url']
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
