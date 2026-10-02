class Field:
    def __init__(self, column_type, primary_key=False, default=True):
        self.column_type = column_type
        self.primary_key = primary_key
        self.default = default

class IntegerField(Field):
    def __init__(self, **kw):
        super().__init__('bigint', **kw)

class StringField(Field):
    def __init__(self, max_length=255, **kw):
        super().__init__(f"VARCHAR({max_length})", **kw)
