from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from MatchSystem import MatchSystem
import secrets
import chess
import asyncio
import chess.engine
from chess.engine import UciProtocol
from chess.svg import board as _render_board
from aiogram import Bot
from aiogram.types import Message,BufferedInputFile
import cairosvg
import os



def render_board(board):
    svg=_render_board(board)
    return cairosvg.svg2png(bytestring=svg.encode(), output_width=400, output_height=400)

class CpuMatch:
    def __init__(self,engine:UciProtocol,bot:Bot,executor,message:Message) -> None:
        self.board=chess.Board()
        self.event=asyncio.Event()
        self.bot=bot
        self.executor=executor
        self.engine=engine
        self.player_move=None
        self.abandoned=False
        self.task=None
        self.message=message

    async def _wait_for_player_move(self):
        if self.board.is_game_over():
            return
        await self.event.wait()
        if self.abandoned:
            return
        self.event.clear()
        move=chess.Move.from_uci(self.player_move)
        if move in self.board.legal_moves:
            self.board.push(move)
            await self._on_board_updated()
            return True
        else:
            await self.bot.send_message(self.message.chat.id,'Illegal Move!') 

    async def _on_board_updated(self):
        
        pngdata=await asyncio.get_running_loop().run_in_executor(self.executor,render_board,self.board)
        await self.bot.send_photo(self.message.chat.id,BufferedInputFile(pngdata,filename=f'{secrets.token_hex(32)}.png'))
        
    def is_over(self):
        return self.abandoned or self.board.is_game_over()

    async def _make_move(self):
        result = await self.engine.play(self.board, chess.engine.Limit(time=0.1))
        self.board.push(result.move)
        await self.bot.send_message(self.message.chat.id,f'CPU played {result.move}')
        await self._on_board_updated()

    async def _on_match_end(self):
        if self.board.is_stalemate():
            await self.bot.send_message(self.message.chat.id,"Game drawn: stalemate")
            return
        if self.board.is_repetition():
            await self.bot.send_message(self.message.chat.id,"Game drawn: repitition")
            return
        if self.board.is_insufficient_material():
            await self.bot.send_message(self.message.chat.id,"Game drawn: insufficient material")
            return
        if self.board.is_checkmate():
            if self.board.outcome().winner:
                await self.bot.send_message(self.message.chat.id,"You won.")
                return
            else:
                await self.bot.send_message(self.message.chat.id,"CPU won")

    async def _loop(self,match_system:MatchSystem,uid:int):
        while not self.is_over():
            if not await self._wait_for_player_move():
                continue
            await self._make_move()
        del match_system.cpu_matches[uid]
        return await self._on_match_end()