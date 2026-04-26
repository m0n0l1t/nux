from . import start, menu, balance, services, instructions, invites,  cancel

def register_all_handlers(dp):
    dp.include_router(start.router)
    dp.include_router(menu.router)
    dp.include_router(balance.router)
    dp.include_router(services.router)
    dp.include_router(instructions.router)
    dp.include_router(invites.router)
    dp.include_router(cancel.router)