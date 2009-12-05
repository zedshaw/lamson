from lamson import mail
from app.model import addressing


def craft_response(message, From, To, contact_addr=None):
    response = mail.MailResponse(To=To,
                            From=From,
                            Subject=message['subject'])

    msg_id = message['message-id']

    if contact_addr:
        response.update({
            "Sender": contact_addr, 
            "Reply-To": contact_addr,
            "Return-Path": contact_addr, 
            "Precedence": "list",
        })

    if 'date' in message:
        response['Date'] = message['date']

    if 'references' in message:
        response['References'] = message['References']
    elif msg_id:
        response['References'] = msg_id

    if msg_id:
        response['message-id'] = msg_id

        if 'in-reply-to' not in message:
            response["In-Reply-To"] = message['Message-Id']

    if message.all_parts():
        response.attach_all_parts(message)
    else:
        response.Body = message.body()

    return response


def cleanse_incoming(message, user_id, host, marketroid_rand=None):
    user_real = addressing.real(user_id)

    if not marketroid_rand:
        marketroid_rand = addressing.anon(message['from'], host)

    reply = craft_response(message, message['from'], user_real, marketroid_rand)

    return reply


def route_reply(message, marketroid_id, host):
    marketroid_real = addressing.real(marketroid_id)
    user_anon = addressing.anon(message['from'], host)

    reply = craft_response(message, user_anon, marketroid_real)

    return reply


