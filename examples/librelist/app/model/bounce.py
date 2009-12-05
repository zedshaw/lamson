from lamson import view, encoding, queue
from config import settings


def mail_to_you_is_bouncing(message):
    reason = message.bounce.error_for_humans()

    msg = view.respond(locals(), 'mail/you_bounced.msg',
                       From='unbounce@librelist.com',
                       To=message.bounce.original['to'],
                       Subject="Email to you is bouncing.")

    if message.bounce.report:
        for report in message.bounce.report:
            msg.attach('bounce_report.msg', content_type='text/plain', data=encoding.to_string(report),
                       disposition='attachment')

    if message.bounce.notification:
        msg.attach('notification_report.msg', content_type='text/plain',
                   data=encoding.to_string(message.bounce.notification),
                   disposition='attachment')

    return msg

def you_are_now_unbounced(message):
    msg = view.respond(locals(), 'mail/you_are_unbounced.msg',
                       From='noreply@librelist.com',
                       To=message['from'],
                       Subject="You are now unbounced.")

    return msg


def archive_bounce(message):
    qu = queue.Queue(settings.BOUNCE_ARCHIVE)
    qu.push(message)

