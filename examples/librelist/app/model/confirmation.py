from webapp.librelist.models import Confirmation

class DjangoConfirmStorage():
    def clear(self):
        Confirmation.objects.all().delete()

    def get(self, target, from_address):
        confirmations = Confirmation.objects.filter(from_address=from_address, 
                                                list_name=target)
        if confirmations:
            return confirmations[0].expected_secret, confirmations[0].pending_message_id
        else:
            return None, None

    def delete(self, target, from_address):
        Confirmation.objects.filter(from_address=from_address, 
                                                list_name=target).delete()

    def store(self, target, from_address, expected_secret, pending_message_id):
        conf = Confirmation(from_address=from_address,
                            expected_secret = expected_secret,
                            pending_message_id = pending_message_id,
                            list_name=target)
        conf.save()

