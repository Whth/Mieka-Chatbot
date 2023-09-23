from graia.broadcast import DispatcherInterface
from graia.broadcast.entities.dispatcher import BaseDispatcher
from graia.broadcast.entities.event import Dispatchable


class AllExtensionsInstalledEvent(Dispatchable):
    class Dispatcher(BaseDispatcher):
        async def catch(self, interface: DispatcherInterface):
            """
            just to let other apps know the extensions is all installed
            Args:
                interface ():

            Returns:
                None
            """
