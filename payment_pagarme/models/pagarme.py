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
    pagarme_seller_token = fields.Char("PagarMe Seller Token")

    def pagarme_form_generate_values(self, values):
        print(values)

    # def picpay_form_generate_values(self, values): #pay page creation"
    #     """ Function to generate HTML POST @ PagarMe """
    #     base_url = (
    #         self.env["ir.config_parameter"].sudo().get_param("web.base.url") #this safe place to hold the API-key
    #     ) #we are using the base URL including the API-key, query param
    #     partner = self.env['res.partner'].browse(values.get('partner_id'))
    #     pagarme_vals = {
    #         'referenceId': values.get('reference_key'),
    #         'callbackUrl': '%stransactions/transaction_id/refund' %  ,
    #         #'returnUrl': '%s/payment/process' % base_url,
    #         'value': values.get('amount'),
    #         'buyer': {
    #             'firstName': values.get('partner_first_name'),
    #             'lastName': values.get('partner_last_name'),
    #             'document': partner.l10n_br_cnpj_cpf,
    #             'email': values.get('billing_partner_email'),
    #             'phone': values.get('billing_partner_phone'),
    #         }
    #     }
    #     headers = {
    #         'Content-Type': 'application/json',
    #         'x-picpay-token': self.picpay_token,
    #     }
    #     url = 'https://api.pagar.me/1/transactions' #https://docs.pagar.me/reference#criar-transacao
    #     response = requests.post(
    #         url, data=json.dumps(pic_vals), headers=headers
    #     )

    #     data = response.json()

    #     if not response.ok: #denne virker - betyder bare, at der kommer en besked, hvis der ikke er et respons 
    #         raise UserError(data.get("message"))

    #     acquirer_reference = data.get("acquirer_id") #https://docs.pagar.me/reference#objeto-transaction
    #     payment_transaction_id = self.env['payment.transaction'].search(
    #         [("reference", "=", values['reference'])])

    #     payment_transaction_id.write({
    #         "acquirer_reference": acquirer_reference,
    #         "pagarme_url": data['postback_url'], #postback_url from the documentation
    #     })
    #     #product of the function is a dict with 
    #     return {
    #         "checkout_url": urls.url_join(
    #             base_url, "/picpay/checkout/redirect"),
    #         "secure_url": data['paymentUrl']
    #     }


class TransactionPicPay(models.Model):
    _inherit = "payment.transaction"

    picpay_url = fields.Char(string="Fatura PicPay", size=300)
    picpay_authorizarion = fields.Char(string="Autorização do Pagamento")

    @api.model
    def _picpay_form_get_tx_from_data(self, data):
        acquirer_reference = data.get("data[id]")
        tx = self.search([("acquirer_reference", "=", acquirer_reference)])
        return tx[0]

    def _picpay_form_validate(self, data):
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
