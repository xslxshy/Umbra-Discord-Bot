import abc

class BaseGame(abc.ABC):
    @abc.abstractmethod
    async def start(self, bot, guild, challenger, opponent, bet):
        pass