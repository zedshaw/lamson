Hi,

It looks like the list "{{ list_name }}" doesn't exist,
so let's figure out what you meant to do.

{% if similar_lists -%}
First, maybe you got the name wrong, so make sure you didn't mean one of
these similarly named lists:

{% for possible in similar_lists[0:10] -%}
* {{ possible.name }}
{% endfor -%}

{% else -%}
First, it looks like there aren't any lists similar to "{{list_name}}".
{% endif %}


CONFIRM BY REPLYING

If you really do want to make a list named "{{ list_name }}" then all
you have to do is reply to this email and we'll make the list, subscribe
you, and send your original email as the first email.


Thank You,

      librelist.com

