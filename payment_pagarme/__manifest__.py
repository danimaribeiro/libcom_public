{
    "name": "Método de Pagamento PagarMe",
    "summary": "Payment Acquirer: PagarMe",
    "description": """PagarMe payment gateway for Odoo.""",
    "category": "Accounting",
    "license": "Other OSI approved licence",
    "version": "13.0.1.0.0",
    "author": "Code 137",
    "website": "http://www.code137.com.br",
    "contributors": ["Danimar Ribeiro <danimaribeiro@gmail.com>"],
    "depends": ["account", "payment", "sale"],
    "data": [
        "views/payment_views.xml",
        "views/pagarme.xml",
        "data/pagarme.xml",
    ],
    "application": True,
}
