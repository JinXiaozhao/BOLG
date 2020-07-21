import logging
import aiomysql
import asyncio



#数据库sql语句日志
def log(sql,args=()):
    logging.info("SQL:%s" % sql)


#建立数据库连接池
async def create_pool(loop,**kw):
    global __pool
    logging,info("create mysql database connection pool....")
    __pool = await aiomysql.create_pool(
        host=kw.get("host",'127.0.0.1'),
        port=kw.get("port",3306),
        user=kw.get("user",'root'),
        password=kw.get("password",'109801'),
        db=kw.get("db",'blog'),
        charset=kw.get("charset","utf-8")
        autocommit=kw.get("autocommit",True),
        maxsize=kw.get("maxsize",10),
        minsize=kw.get("minsize",1),
        loop=loop
        )


#select语句??
async def select(sql, args, size=None):
    log(sql, args)
    global __pool
    
    with (await __pool) as conn:
        cur = await conn.cursor(aiomysql.DictCursor)
        await cur.execute(sql.replace('?', '%s'), args or ())
        if size:
            res = await cur.fetchmany(size)
        else:
            res = await cur.fetchall()
        await cur.close()
        logging.info('rows returned: %s' % len(res))
        return res


#insert、update、delete语句??
async def execute(sql, args):
    log(sql,args)
    global __pool
    
    with (await __pool) as conn:
        try:
            cur = await conn.cursor()
            await cur.execute(sql.replace('?', '%s'), args)
            affected = cur.rowcount
            await cur.close()
        except BaseException as e:
            raise
        return affected


#创建占位符
def create_args_string(num):
    L = []
    for _ in range(num):
        L.append('?')
    return ', '.join(L)
  

#描述字段的字段名，数据类型，键信息，默认值
class Filed():

    def __init__(self,name,column_type,primary_key,default):
        self.name = name
        self.column_type = column_type
        self.primary_key = prinmary_key
        self.default = default

    def __str__(self):
        return '<%s,%s:%s>' % (self.__class__.name,self.column_type,self.name)


class StringFiled(Filed):

    def __init__(self,name=None,column_type='varchar(100)',primary_key=False,default=None):
        super.__init__(name,column_type,primary_key,default)


class BooleanFiled(Filed):

    def __init__(self,name=None,default=False):
        super.__init__(name,'boolean',False,default)


class IntegerFiled(Filed):
    
    def __init__(self,name=None,primary_key=False,default=0):
        super.__init__(name,'bigint',primary_key,default)


class FloatFiled(Filed):
    
    def __init__(self,name=None,primary_key=False,default=0.0):
        super.__init__(name,'real',primary_key,default)


class TextFiled(Filed):
    
    def __init__(self,name=None,default=None):
        super.__init__(name,'text',False,default)


# 元类用来动态的创建类
class ModelMetaclass(type):

    def __new__(cls,name,bases,attrs):
        if name == "Model":
            return type.__new__(cls,name,bases,attrs)
        table_name = attrs.get('__table__',None) or name
        logging.info('found model: %s(table:%s)' % (name,table_name))

        mappings = dict()
        fields = list()
        primaryKey = None
        for k, v in attrs.items():
            if isinstance(v, Field):
                logging.info('found mapping: %s ==> %s' % (k, v))
                mappings[k] = v
                if v.primary_key:
                    # 找到主键:
                    if primaryKey:
                        raise RuntimeError('Duplicate primary key for field: %s' % k)
                    primaryKey = k
                else:
                    fields.append(k)

        if not primaryKey:
            raise RuntimeError('Primary key not found.')
        
        for k in mappings.keys():
            attrs.pop(k)
        
        escaped_fields = list(map(lambda f: '`%s`' % f, fields))
        attrs['__mappings__'] = mappings
        attrs['__table__'] = table_name
        attrs['__fields__'] = fields
        
        attrs['__select__'] = 'select `%s`, %s from `%s`' % (primaryKey, ', '.join(escaped_fields), tableName)
        attrs['__insert__'] = 'insert into `%s` (%s, `%s`) values (%s)' % (tableName, ', '.join(escaped_fields), primaryKey, create_args_string(len(escaped_fields) + 1))
        attrs['__update__'] = 'update `%s` set %s where `%s`=?' % (tableName, ', '.join(map(lambda f: '`%s`=?' % (mappings.get(f).name or f), fields)), primaryKey) 
        attrs['__delete__'] = 'delete from `%s` where `%s`=?' % (tableName, primaryKey)
        return type.__new__(cls,name,bases,attrs)


class Model(dict,metaclass=ModelMateclass):

    def __init__(self,**kw):
        super(Model,self).__init__(**kw)

    def __getattr__(self,key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Model' object has no attribute '%s'" % key)

    def __setattr__(self,key,value):
        self[key] = value

    def getValue(self,key):
        return getattr(self,key,None)
    
    def getValueOrDefault(self, key):
        value = getattr(self, key, None)
        if value is None:
            field = self.__mappings__[key]
            if field.default is not None:
                value = field.default() if callable(field.default) else field.default
                logging.debug('using default value for %s: %s' % (key, str(value)))
                setattr(self, key, value)
        return value

    @classmethod
    async def findAll(cls, where=None, args=None, **kw):
        ## find objects by where clause
        sql = [cls.__select__]
        if where:
            sql.append('where')
            sql.append(where)
        if args is None:
            args = []
        orderBy = kw.get('orderBy', None)
        if orderBy:
            sql.append('order by')
            sql.append(orderBy)
        limit = kw.get('limit', None)
        if limit is not None:
            sql.append('limit')
            if isinstance(limit, int):
                sql.append('?')
                args.append(limit)
            elif isinstance(limit, tuple) and len(limit) == 2:
                sql.append('?, ?')
                args.extend(limit)
            else:
                raise ValueError('Invalid limit value: %s' % str(limit))
        res = await select(' '.join(sql), args)
        return [cls(**r) for r in res]

    @classmethod
    async def findNumber(cls, selectField, where=None, args=None):
        ## find number by select and where
        sql = ['select %s _num_ from `%s`' % (selectField, cls.__table__)]
        if where:
            sql.append('where')
            sql.append(where)
        res = await select(' '.join(sql), args, 1)
        if len(res) == 0:
            return None
        return res[0]['_num_']

    @classmethod
    async def find(cls, pk):
        ## find object by primary key
        rs = await select('%s where `%s`=?' % (cls.__select__, cls.__primary_key__), [pk], 1)
        if len(rs) == 0:
            return None
        return cls(**rs[0])

    async def save(self):
        args = list(map(self.getValueOrDefault, self.__fields__))
        args.append(self.getValueOrDefault(self.__primary_key__))
        rows = await execute(self.__insert__, args)
        if rows != 1:
            logging.warning('failed to insert record: affected rows: %s' % rows)
        else:
            logging.info('succeed to insert by primary key: affected rows: %s' % rows)

    async def update(self):
        args = list(map(self.getValue, self.__fields__))
        args.append(self.getValue(self.__primary_key__))
        rows = await execute(self.__update__, args)
        if rows != 1:
            logging.warning('failed to update by primary key: affected rows: %s' % rows)
        else:
            logging.info('succeed to update by primary key: affected rows: %s' % rows)

    async def remove(self):
        args = [self.getValue(self.__primary_key__)]
        rows = await execute(self.__delete__, args)
        if rows != 1:
            logging.warning('failed to remove by primary key: affected rows: %s' % rows)
        else:
            logging.info('succeed to delete by primary key: affected rows: %s' % rows)
    









    
    
