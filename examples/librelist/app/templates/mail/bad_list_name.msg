Hi,

Sorry to tell you, but the list name you gave:

{{ bad_list }}@{{ host }}

is not a valid name for a list at librelist.com.

You probably put a '-' character in it, but that character is used by
librelist to separate list names from commands.


WHAT IS VALID

List names can only have characters, numbers, and the '.' (period)
character.  You can't have any other special characters.


{% if similar_lists -%}
SIMILAR LISTS

Maybe you got the name wrong, so make sure you didn't mean one of these
similarly named lists:

{% for possible in similar_lists[0:10] -%}
* {{ possible.name }}
{% endfor %}

{% endif -%}

TRYING AGAIN

Simply just try again with a valid list name and we'll get to work on
making the list you want.


Thank you,

      librelist.com

