from aiohttp import web


async def inicio(request):
    return web.Response(text='ok')


app = web.Application()
app.add_routes([web.get('/', inicio)])

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=8080)
