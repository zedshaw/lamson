from lamson import queue


def attach_headers(message, user_id, post_name, domain):
    """Headers are used later by the index.py handler to figure out where
    the message finally goes."""
    message['X-Post-Name'] = post_name
    message['X-Post-User-ID'] = user_id
    message['X-Post-Domain'] = domain


def defer_to_queue(message):
    index_q = queue.Queue("run/posts")  # use a diff queue?
    index_q.push(message)
    print "run/posts count after dever", index_q.count()
