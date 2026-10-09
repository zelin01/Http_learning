class Field:
    def __init__(self, column_type, primary_key=False, default=True):
        self.column_type = column_type
        self.primary_key = primary_key
        self.default = default

class IntegerField(Field):
    def __init__(self, **kw):
        super().__init__('bigint', **kw) #super() 返回一个代理对象，调用父类的方法， **KW 省略函数中的参数

class StringField(Field):
    def __init__(self, max_length=255, **kw):
        super().__init__(f"VARCHAR({max_length})", **kw)

class ModelMeta(type):
    def __new__(mcs, name, bases, attrs):
        if name == 'Model':
            return super.__new__(mcs, name, bases, attrs)

        fields = {}
        for k, v in list(attrs.items()):
            if isinstance(v, Field):
                v.name = v
                fields[k] = v

        attrs["__table__"] = attrs.get("__table__", name.lower() + 's')
        attrs["__fields__"] = fields
        for k in fields:
            attrs.pop(k)
        return super().__new__(mcs, name, bases, attrs)
class Model(metaclass=ModelMeta):
    pass