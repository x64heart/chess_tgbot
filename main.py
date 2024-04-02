import asyncio
from aiogram import F, Router, types
import aiogram
import traceback
from aiogram import Bot, Dispatcher, Router, types
from aiogram.enums import ParseMode
from aiogram import flags
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart,Command
from aiogram.types import Message
from aiogram.utils.markdown import hbold
from CpuMatch import CpuMatch
from MatchSystem import MatchSystem
import os
from concurrent.futures import ProcessPoolExecutor
async def amain():
    dp=aiogram.Dispatcher()
    executor=ProcessPoolExecutor(max_workers=os.cpu_count())
    token=os.environ.get('BOT_TOKEN')
    bot=aiogram.Bot(token=token)
    await bot.set_my_commands([
        types.BotCommand(command="start", description="Запустить бота"),
        types.BotCommand(command="play", description="Начать игру"),
        types.BotCommand(command="quit", description="Выйти из игры"),
        types.BotCommand(command="cancel", description="Отменить поиск игры"),
        types.BotCommand(command="playcpu", description="Играть с компьютером"),
    ])
    match_system=MatchSystem(bot,executor)
    @dp.message(Command("play"))
    async def _on_play_selected(message:Message):
        await match_system.on_play_selected(message)
    @dp.message(Command('quit'))
    async def _on_quit(message:Message) -> None:
        user_id=message.from_user.id
        if not user_id in match_system.cpu_matches.keys():
            return await message.answer("Can't quit because not in game currently")
        match=match_system.cpu_matches[user_id]
        match:CpuMatch
        match.abandoned=True
        match.event.set()
        #.task.cancel()
        await message.answer("You abandoned a chess game... Ha, what a chicken!")


    @dp.message(Command("playcpu"))
    async def _on_play_cpu(message:Message)->None:
        if not match_system.ready:
            await message.answer("Engine not ready yet!")
            return
        await match_system.on_play_cpu(message)

    @dp.message(CommandStart())
    async def _on_start(message:Message) -> None:
        await message.answer("""
        Hello, this is a chess bot.
        Type /play to start a game.
        """)
    @dp.message()
    async def _on_msg(message:Message) -> None:
        match=match_system.cpu_matches.get(message.from_user.id,None)
        if match is None:
            return
        move=message.text
        match:CpuMatch
        match.player_move=move
        match.event.set()
    await dp.start_polling(bot)


def main():
    asyncio.run(amain())


if __name__=="__main__":
    try:
        main()
    except:
        print(traceback.format_exc())
