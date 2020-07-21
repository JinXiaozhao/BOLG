import logging
import asyncio
from aiohttp import web

#日志
logging.basicConfig(level=logging.INFO)

#服务器响应请求的初始页面
async def index(request):
    return web.Response(body=b"<h1>my first website!</h1>",content_type="text/html",charset='utf-8')


def main():
    #初始化web中的web框架
    app = web.Application()
    #在路由中添加网页及响应函数
    app.router.add_get("/index.html",index)
    app.router.add_get("/",index)
    #设置网站网址及端口号
    web.run_app(app,host='127.0.0.1',port = 8888)


if __name__ == "__main__":
    main()
