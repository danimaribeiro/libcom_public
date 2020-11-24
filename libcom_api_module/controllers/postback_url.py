# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
from werkzeug.exceptions import abort
import requests
import json

class PagarmePostbackURL(http.Controller):
    
   
    @http.route('/api/pagarme_postback', type='json', auth='none') #endopoint for authentication
    def authenticate(self, db, login, password, base_location=None):
        request.session.authenticate(db, login, password)
        return request.env['ir.http'].session_info([])