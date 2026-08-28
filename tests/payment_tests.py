from __future__ import absolute_import, unicode_literals
from flittpayments import Api, Payment, Pcidss
from .tests_helper import TestCase


class PaymentTest(TestCase):
    def setUp(self):
        self.api = self.get_api()
        self.payment = Payment(api=self.api)
        self.pcidss = Pcidss(api=self.api)

    def test_recurring_payment(self):
        token = self.create_order().get('rectoken')
        data = {
            "rectoken": token
        }
        data.update(self.data['checkout_data'])
        response = self.payment.recurring(data)
        self.assertEqual(response.get('response_status'), 'success')
        self.assertIn('order_status', response)
        self.assertEqual(response.get('order_status'), 'approved')

    def test_p2pcredit(self):
        api = Api(merchant_id=1549901, secret_key='testcredit')
        payment = Payment(api=api)
        response = payment.p2pcredit(self.data['payment_p2p'])
        self.assertEqual(response.get('response_status'), 'success')
        self.assertIn('order_status', response)

    def test_p2pcredit_with_rectoken(self):
        # Mirrors the README's P2P credit example: obtain a rectoken from a
        # purchase, then credit that same card without a card number.
        purchase_data = {'required_rectoken': 'Y'}
        purchase_data.update(self.data['payment_pcidss_non3ds'])
        rectoken = self.pcidss.step_one(purchase_data).get('rectoken')
        self.assertTrue(rectoken)

        api = Api(merchant_id=1549901, secret_key='testcredit')
        payment = Payment(api=api)
        data = {
            'receiver_rectoken': rectoken
        }
        data.update(self.data['checkout_data'])
        response = payment.p2pcredit(data)
        self.assertEqual(response.get('response_status'), 'success')
        self.assertEqual(response.get('order_status'), 'approved')

    def test_ibancredit(self):
        api = Api(merchant_id=1549901, secret_key='testcredit')
        payment = Payment(api=api)
        response = payment.ibancredit(self.data['payment_iban'])
        self.assertEqual(response.get('response_status'), 'success')
        self.assertIn('order_status', response)

    def test_non3dpcidss_step_one(self):
        data = self.data['payment_pcidss_non3ds']
        response = self.pcidss.step_one(data)
        self.assertEqual(response.get('response_status'), 'success')
        self.assertIn('order_status', response)
        self.assertEqual(response.get('order_status'), 'approved')

    def test_3dspcidss_step_one(self):
        data = self.data['payment_pcidss_3ds']
        response = self.pcidss.step_one(data)
        self.assertEqual(response.get('response_status'), 'success')
        self.assertIn('acs_url', response)
        self.assertIn('pareq', response)
