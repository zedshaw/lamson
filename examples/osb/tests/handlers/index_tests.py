from nose.tools import *
from lamson.testing import *
from handlers import post_tests
import os

index = "app/data/index.html"

def reset_index():
    clear_queue("run/indexed")
    assert queue("run/indexed").count() == 0

    clear_queue("run/posts")
    assert queue("run/posts").count() == 0
    if os.path.exists(index):
        os.unlink(index)

def setup():
    reset_index()

def test_index_updated_after_post():
    post_tests.test_new_user_subscribes()
    assert os.path.exists(index)
    contents = open(index).read()

    post_tests.test_existing_user_posts()
    assert os.path.exists(index)
    updated = open(index).read()

    assert contents != updated, "The index should change."

def test_comment_added_to_list():
    pass

