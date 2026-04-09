import sqlite3

con = sqlite3.connect(':memory:', check_same_thread=False)
cursor = con.cursor()

def log_sql(query, params=None):
    if params:
        formatted_query = query
        for p in params:
            val = f"'{p}'" if isinstance(p, str) else str(p)
            formatted_query = formatted_query.replace('?', val, 1)
        print(f"SQL: {formatted_query};")
    else:
        print(f"SQL: {query};")

class QuerySet:
    def __init__(self, model):
        self.model = model
        self.filters = {}
        self.order = None
        self.operators = {
            'gte': '>=', 'lte': '<=', 'gt': '>', 'lt': '<', 'exact': '='
        }

    def filter(self, **kwargs):
        self.filters.update(kwargs)
        return self

    def order_by(self, field):
        self.order = field
        return self

    def _build_sql(self):
        table_name = self.model.__name__.lower()
        query = f"SELECT * FROM {table_name}"
        params = []

        if self.filters:
            conditions = []
            for key, value in self.filters.items():
                if "__" in key:
                    field, op = key.split("__")
                    sql_op = self.operators.get(op, '=')
                else:
                    field, sql_op = key, '='
                
                column = f"{field}_id" if field in self.model.fields and isinstance(self.model.fields[field], ForeignKey) else field
                conditions.append(f"{column} {sql_op} ?")
                params.append(value)
            query += f" WHERE {' AND '.join(conditions)}"

        if self.order:
            direction = "DESC" if self.order.startswith("-") else "ASC"
            field = self.order.lstrip("-")
            query += f" ORDER BY {field} {direction}"

        return query, params

    def all(self):
        query, params = self._build_sql()
        log_sql(query, params)
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [self.model._from_row(row) for row in rows]

    def __repr__(self):
        return str(self.all())

class RelatedManager:
    def __init__(self, source_model, foreign_key_name):
        self.source_model = source_model
        self.foreign_key_name = foreign_key_name

    def __get__(self, instance, owner):
        if instance is None: return self
        return self.source_model.filter(**{self.foreign_key_name: instance.id})

class Model:
    def __init__(self, **kwargs):
        self.id = None
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __init_subclass__(cls):
        cls.fields = {}
        for name, value in cls.__dict__.items():
            if isinstance(value, Field):
                cls.fields[name] = value

    @classmethod
    def _from_row(cls, row):
        if not row: return None
        instance = cls()
        instance.id = row[0]
        for i, name in enumerate(cls.fields.keys(), 1):
            instance.__dict__[name] = row[i]
        return instance

    @classmethod
    def create_table(cls):
        table_name = cls.__name__.lower()
        cols = ["id INTEGER PRIMARY KEY AUTOINCREMENT"]
        for name, field in cls.fields.items():
            col_name = f"{name}_id" if isinstance(field, ForeignKey) else name
            sql = f"{col_name} {field.sql_type}"
            if not field.nullable: sql += " NOT NULL"
            if field.unique: sql += " UNIQUE"
            cols.append(sql)
            if isinstance(field, ForeignKey):
                ref_table = field.reference_model.__name__.lower()
                cols.append(f"FOREIGN KEY ({col_name}) REFERENCES {ref_table}(id)")
        
        query = f"CREATE TABLE IF NOT EXISTS {table_name} (\n    {',\n    '.join(cols)}\n);"
        log_sql(query)
        cursor.execute(query)
        con.commit()
        print(f"Table '{table_name}' created.\n")

    def save(self):
        table_name = self.__class__.__name__.lower()
        field_names = []
        values = []
        for name, field in self.fields.items():
            col_name = f"{name}_id" if isinstance(field, ForeignKey) else name
            field_names.append(col_name)
            val = getattr(self, name)
            values.append(val.id if hasattr(val, 'id') and val.id else val)

        qs = ", ".join(field_names)
        placeholders = ", ".join(["?"] * len(values))
        query = f"INSERT INTO {table_name} ({qs}) VALUES ({placeholders})"
        log_sql(query, values)
        cursor.execute(query, values)
        self.id = cursor.lastrowid
        con.commit()
        print(f"Record saved: {self}\n")

    @classmethod
    def filter(cls, **kwargs):
        return QuerySet(cls).filter(**kwargs)

    def __repr__(self):
        attrs = ", ".join([f"{k}={v!r}" for k, v in self.__dict__.items() if not k.startswith('_')])
        return f"{self.__class__.__name__}({attrs})"

class Field:
    def __init__(self, data_type, sql_type, nullable=False, max_length=None, unique=False):
        self.data_type = data_type
        self.sql_type = sql_type
        self.nullable = nullable
        self.unique = unique

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner):
        if instance is None: return self
        return instance.__dict__.get(self.name)

    def __set__(self, instance, value):
        instance.__dict__[self.name] = value

class CharField(Field):
    def __init__(self, max_length=255, **kwargs):
        super().__init__(str, f"VARCHAR({max_length})", **kwargs)

class IntegerField(Field):
    def __init__(self, **kwargs):
        super().__init__(int, "INTEGER", **kwargs)

class ForeignKey(Field):
    def __init__(self, reference_model, related_name=None, **kwargs):
        super().__init__(int, "INTEGER", **kwargs)
        self.reference_model = reference_model
        self.related_name = related_name

    def __set_name__(self, owner, name):
        self.name = name
        if self.related_name:
            setattr(self.reference_model, self.related_name, RelatedManager(owner, self.name))

    def __get__(self, instance, owner):
        if instance is None: return self
        val = instance.__dict__.get(self.name)
        if isinstance(val, int):
            table = self.reference_model.__name__.lower()
            query = f"SELECT * FROM {table} WHERE id = ?"
            cursor.execute(query, (val,))
            return self.reference_model._from_row(cursor.fetchone())
        return val

class User(Model):
    name = CharField(max_length=100)
    email = CharField(max_length=255, unique=True)
    age = IntegerField(nullable=True)

class Post(Model):
    title = CharField(max_length=200)
    author = ForeignKey(User, related_name="posts")

User.create_table()
Post.create_table()

alice = User(name="Alice", email="alice@example.com", age=30)
alice.save()

users = User.filter(age__gte=25).order_by("-name").all()
print(users)
print()

p1 = Post(title="Hello World", author=alice)
p1.save()

print(alice.posts.all())