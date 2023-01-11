from pyhap.iid_manager import IIDManager
from pyhap.service import Service


class CustomIIDManager(IIDManager):
    """A custom IIDManager that makes use of unique_ids IIDs."""

    def __init__(self):
        super().__init__()

    def get_iid_for_obj(self, obj):
        """Assign an IID to an object."""
        if isinstance(obj, Service):
            if obj.unique_id is not None:
                return obj.unique_id
        return super().get_iid_for_obj(obj)
