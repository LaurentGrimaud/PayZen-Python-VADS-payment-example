import uuid
import hmac
import base64
from datetime import datetime
import hashlib
import logging
import json


class PayZenFormToolBox:
  # PayZen platform data
  platform = {
    'url'           : 'https://secure.payzen.eu/vads-payment/'
  }

  shop_platform = {
    'ipn_url':    None,
    'return_url': None
  }

  # PayZen account data
  def __init__(self, site_id, cert_test, cert_prod, mode = 'TEST'):
    self.logger = logging.getLogger()
    self.account = {
     'site_id': site_id,
     'cert': {
      'TEST': cert_test,
      'PRODUCTION': cert_prod
     },
     'mode': mode
    } 

  def form(self,trans_id, amount, currency):
    return {
      "form" : {
	"action"         : self.platform['url'],
	"method"         : "POST",
	"accept-charset" : "UTF-8",
	"enctype"        : "multipart/form-data"
      },
      "fields" : self.fields(self.account['site_id'], trans_id, amount, currency)
    }


  def fields(self, site_id, trans_id, amount, currency):
    fields =  {
     "vads_site_id"         : site_id,
     "vads_ctx_mode"        : self.account['mode'],
     "vads_trans_id"        : trans_id,
     "vads_trans_date"      : datetime.utcnow().strftime("%Y%m%d%H%M%S"),
     "vads_amount"          : amount,
     "vads_currency"        : currency,
     "vads_action_mode"     : "INTERACTIVE",
     "vads_page_action"     : "PAYMENT",
     "vads_version"         : "V2",
     "vads_payment_config"  : "SINGLE",
     "vads_capture_delay"   : "0",
     "vads_validation_mode" : "0"
    }

    if self.shop_platform['ipn_url']:
      fields['vads_url_check'] = self.shop_platform['ipn_url']

    if self.shop_platform['return_url']:
      fields['vads_url_return'] = self.shop_platform['return_url']

    fields['signature'] = self.sign(fields)
    return fields


  def sign(self, fields):
    data = []
    for key in sorted(fields):
      data.append(str(fields[key]))
    data.append(self.account['cert'][self.account['mode']])
    return hashlib.sha1('+'.join(data)).hexdigest()


  def ipn_pay(self, fields):
    if fields['vads_operation_type'] != 'DEBIT':
      raise Exception("Unhandled operation type "+fields['vads_operation_type'])
    if fields['vads_trans_status'] in ['AUTHORISED', 'AUTHORISED_TO_VALIDATE']:
      self.logger.info("IPN - Payment for trans_id {} is authorised!".format(fields['vads_trans_id']))
      return
    raise Exception("Payment is not authorised - Given status is " + fields['vads_trans_status'])
      


  def ipn(self, fields):
    self.logger.debug("IPN request with fields: " + json.dumps(fields))
    data = {}
    for key, value in fields.iteritems():
      if str(key).startswith('vads_'):
	data[key] = value
    self.logger.debug("IPN values retained for signature calculation:" + json.dumps(data))

    signature = self.sign(data)
    if signature != fields['signature']:
      err = 'Signature mismatch - Payment is not confirmed (received: {} / computed: {})'.format(fields['signature'], signature)
      self.logger.warning(err)
      raise Exception(err)


    if fields['vads_url_check_src'] in ['PAY', 'BATCH_AUTO']:
      return self.ipn_pay(fields)

    if fields['vads_url_check_src'] == 'BO':
      return 'Hello PayZen BO!'

    raise Exception("IPN action unhandled: " + fields['vads_url_check_src'])
