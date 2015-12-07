from flask import render_template
from flask import Flask
from flask import request
from flask_cors import cross_origin

from PayZenFormToolBox import *
import calendar
import time
import logging


logging.basicConfig(filename="payzen_form.log", level=logging.INFO)

logger = logging.getLogger()

payzen = Flask(__name__)

#Account data
shopId   = '[***CHANGE-ME***]'
certTest = '[***CHANGE-ME***]'
certProd = '[***CHANGE-ME***]'
mode     = 'TEST'
certProd = '[***CHANGE-ME***]'
ipn_url  = '[***CHANGE-ME***]'

payzenTB = PayZenFormToolBox(shopId, certTest, certProd, mode)

@payzen.route('/form_payment', methods=['GET'])
@cross_origin()
def form_payment():
  payzenTB.shop_platform['ipn_url'] = ipn_url

  #Payment data
  amount   = 1000
  currency = 978
  trans_id = str(calendar.timegm(time.gmtime()))[-6:]

  form = payzenTB.form(trans_id, amount, currency)

  return render_template('./form_payment.html', form = form)


@payzen.route('/form_ipn', methods=['POST'])
@cross_origin()
def form_ipn():
  try:
    data = request.form
    response = payzenTB.ipn(data)
    # here the code for an accepted payment
    logger.info("Payment with trans_id {} is accepted, time to validate the order ".format(data['vads_trans_id']))
    return 'Notification processed!'

  except PayZenPaymentRefused:
    # here the code for a refused payment
    logger.info("Payment with trans_id {} is refused, time to close the order ".format(data['vads_trans_id']))
    return 'Notification processed!'

  except PayZenPaymentInvalidated:
    # here the code for a invalidated payment
    # ie when a customer cancels it
    logger.info("Payment with trans_id {} is invalidated, time to close the order ".format(data['vads_trans_id']))
    return 'Notification processed!'

  except PayZenPaymentPending:
    # here the code for a payment not yet validated
    # could be to mark the corresponding order to 'pending' status
    logger.info("Payment with trans_id {} is in pending zone, time to mark the order as 'pending'".format(data['vads_trans_id']))
    return 'Notification processed!'
 


if __name__ == '__main__':
    payzen.debug = True
    payzen.run(host='0.0.0.0')
