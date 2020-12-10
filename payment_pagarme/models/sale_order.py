import requests
from odoo import models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_cancel(self):
        res = super(SaleOrder, self).action_cancel()
        for order in self:
            for transaction_id in order.transaction_ids:
                if (
                    transaction_id
                    and transaction_id.acquirer_id.provider == "pagarme"
                ):
                    pass
                    # TODO Cancelar as transações do pagarME que estão vinculadas a cotação