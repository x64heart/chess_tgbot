
import asyncio
import time
from aiogram import Bot
from aiogram.types import Message
import chess.engine
from CpuMatch import CpuMatch

class MatchSystem:
    async def _ainit(self):
        transport, engine = await chess.engine.popen_uci('stockfish-windows-x86-64-modern.exe')
        self.engine=engine
        self.ready=True
    def __get_loop(self):
        try:
            self.loop=asyncio.get_running_loop()
            self.loop.create_task(self._ainit())
        except:
            raise RuntimeError("No loop is running")
    def __init__(self,bot:Bot,executor) -> None:
        self.__get_loop()
        self.bot=bot
        self.executor=executor
        self.ready=False       
        self.pending_id=None
        self.matches={}
        self.cpu_matches={}

    async def on_play_selected(self,message:Message):
        if self.pending_id is None:
            print("No matches right now, waiting...")
            self.pending_id=message.from_user.id
            await message.answer("No users are waiting for a game currently.\nYou will be notified when your game is ready")
        else:
            _id=time.time_ns()
            #self.matches[_id]=Match(self.bot,self.executor,)
        
    async def on_play_cpu(self,message:Message):
        match=CpuMatch(self.engine,self.bot,self.executor,message)
        self.cpu_matches[message.from_user.id]=match
        match.task=asyncio.create_task(match._loop(self,message.from_user.id))
        await message.answer("Play with CPU using UCI notation (ex e2e4)")