import asyncio
import datetime
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

import database as db

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def format_task_board(tasks):
    if not tasks:
        return "📋 **TEAM TASK BOARD**\n\n🎉 *No active tasks! Everything is complete.*"

    text = "📋 **TEAM TASK BOARD**\n\n"
    for t in tasks:
        due_str = t.due_date.strftime("%Y-%m-%d %H:%M")
        text += (
            f"📌 **[#{t.id}] {t.description}**\n"
            f"   ├ Assigned to : {t.assignee}\n"
            f"   ├ Due Date: `{due_str}`\n"
            f"   └ Created by: @{t.created_by}\n\n"
        )
    return text

@dp.message(Command("add"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_add(message: types.Message):
    try:
        args = message.text.split()[1:]
        if len(args) < 3:
            await message.reply(
                "⚠️ **Usage:** `/add <description> @username YYYY-MM-DD HH:MM`\n"
                "Example: `/add Fix database bug @alex_dev 2026-10-07 18:00`",
                parse_mode="Markdown"
            )
            return

        date_str = args[-2]
        time_str = args[-1]
        assignee = args[-3] if args[-3].startswith("@") else "Unassigned"
        
        desc_words = args[:-3] if args[-3].startswith("@") else args[:-2]
        description = " ".join(desc_words)
        
        due_date = datetime.datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")

        task = await db.add_task(
            chat_id=message.chat.id,
            created_by=message.from_user.username or message.from_user.first_name,
            assignee=assignee,
            description=description,
            due_date=due_date
        )

        builder = InlineKeyboardBuilder()
        builder.button(text="✅ Complete", callback_data=f"done:{task.id}")

        await message.reply(
            f"📌 **New Team Task [# {task.id}] Added!**\n\n"
            f"• **Task:** {description}\n"
            f"• **Assigned to:** {assignee}\n"
            f"• **Due:** `{date_str} {time_str}`",
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
    except Exception as e:
        await message.reply("❌ **Error parsing command.** Make sure date format is `YYYY-MM-DD HH:MM`.")

@dp.message(Command("board", "tasks"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_board(message: types.Message):
    tasks = await db.get_active_tasks(message.chat.id)
    board_text = format_task_board(tasks)
    await message.answer(board_text, parse_mode="Markdown")

@dp.callback_query(F.data.startswith("done:"))
async def handle_complete(callback: types.CallbackQuery):
    task_id = int(callback.data.split(":")[1])
    user = callback.from_user.username or callback.from_user.first_name

    task = await db.complete_task(task_id, completed_by=user)
    if task:
        await callback.message.edit_text(
            f"✅ **Task [#{task.id}] Completed!**\n"
            f"• **Task:** {task.description}\n"
            f"• **Completed by:** @{user}",
            parse_mode="Markdown"
        )
        await callback.answer("Task completed!")
    else:
        await callback.answer("Task not found or already completed.", show_alert=True)

async def main():
    print("Initializing database...")
    await db.init_db()
    print("Bot starting polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())