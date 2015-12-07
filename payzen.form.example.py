from flask import render_template
from flask import Flask
from flask import request
from flask_cors import cross_origin

from PayZenFormToolBox import PayZenFormToolBox
import calendar
import time
import logging


logging.basicConfig(filename="payzen_form.log", level=logging.INFO)



payzen = Flask(__name__)

#Account data
shopId   = '[***CHANGE-ME***]'
certTest = '[***CHANGE-ME***]'
certProd = '[***CHANGE-ME***]'
ipn_url  = '[***CHANGE-ME***]'
mode     = 'TEST'

payzenTB = PayZenFormToolBox(shopId, certTest, certProd, mode)
payzenTB.shop_platform['ipn_url'] = ipn_url


@payzen.route('/form_payment', methods=['GET'])
@cross_origin()
def form_payment():

  #Payment data
  amount           = 1000
  currency         = 978
  trans_id = str(calendar.timegm(time.gmtime()))[-6:]

  form = payzenTB.form(trans_id, amount, currency)
  print form

  return render_template('./form_payment.html', form = form)


@payzen.route('/form_ipn', methods=['POST'])
@cross_origin()
def form_ipn():
  response = payzenTB.ipn(request.form)
  return 'Notification processed!'
 


if __name__ == '__main__':
    payzen.debug = True
    payzen.run(host='0.0.0.0')
