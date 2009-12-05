from lamson.routing import StateStorage, ROUTE_FIRST_STATE
from webapp.librelist.models import UserState

class UserStateStorage(StateStorage):

    def clear(self):
        for state in UserState.objects.all():
            state.delete()

    def _find_state(self, key, sender):
        states = UserState.objects.filter(state_key = key,
                                          from_address = sender)
        if states:
            return states[0]
        else:
            return None

    def get(self, key, sender):
        stored_state = self._find_state(key, sender)
        if stored_state:
            return stored_state.state
        else:
            return ROUTE_FIRST_STATE

    def key(self, key, sender):
        raise Exception("THIS METHOD MEANS NOTHING TO DJANGO!")

    def set(self, key, sender, to_state):
        stored_state = self._find_state(key, sender)

        if stored_state:
            if to_state == "START":
                # don't store these, they're the default when it doesn't exist
                stored_state.delete()

            stored_state.state = to_state
            stored_state.save()
        else:
            # avoid storing start states
            if to_state != "START":
                stored_state = UserState(state_key = key, from_address = sender,
                                         state=to_state)
                stored_state.save()

    def set_all(self, sender, to_state):
        """
        This isn't part of normal lamson code, it's used to 
        control the states for all of the app.handlers.admin
        lists during a bounce.
        """
        stored_states = UserState.objects.filter(from_address = sender)

        for stored in stored_states:
            stored.state = to_state
            stored.save()


