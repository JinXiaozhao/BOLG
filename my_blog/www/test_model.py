import orm
import asyncio
from models import User, Blog, Comment
import aiomysql
import hashlib


def md5(num):
    md5_pwd = hashlib.md5(bytes("靳", encoding="utf8"))
    md5_pwd.update(bytes(num, encoding="utf8"))
    return md5_pwd.hexdigest()
    

async def test(loop):
    await orm.create_pool(loop=loop)
    u = User(name='Test', email='test@qq.com', passwd=md5("123456"), image='about:blank')
    await u.save()
    
    orm.__pool.close()
    await orm.__pool.wait_closed()
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test(loop))
    loop.close()
