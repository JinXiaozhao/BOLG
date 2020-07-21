import time, uuid
from www.orm import Model, StringField, BooleanField, FloatField, TextField, IntegerField

def next_id():
    ' 根据时间和uuid随机生成主键，如果主键是自增不会用到 '
    return '%015d%s000' % (int(time.time() * 1000), uuid.uuid4().hex)

class User(Model):
    # 定义表名，要和数据库表名一致
    __table__ = 'blog_user'
    # 设置字段对应的类型，字段名和类型需要和数据库中数据类型一致
    id = IntegerField(primary_key=True, default=None)
    s_username = StringField()
    s_pwd = StringField()
    s_gender = IntegerField()
    s_age = IntegerField()

class Comment(Model):
    __table__ = 'comments'

    id = IntegerField(primary_key=True, default=None)
    user_id = IntegerField()
    content = StringField()
    create_time = FloatField(default=time.time())
