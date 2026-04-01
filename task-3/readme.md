## 3. Custom ORM (Object-Relational Mapper)

**Description:** Design a lightweight ORM from scratch using Python metaclasses and descriptors. Support model definition, field validation, query building, relationships, and lazy loading.

**Prerequisites:**

- Python metaclasses (`__new__`, `__init_subclass__`)
- Descriptor protocol (`__get__`, `__set__`, `__set_name__`)
- Decorators and class decorators
- SQL syntax (DDL + DML)
- `sqlite3` standard library module
- Method chaining pattern

**Use-Case:**

- Define database tables as Python classes with typed fields
- Auto-generate `CREATE TABLE` SQL from class definitions
- CRUD operations via `.save()`, `.delete()`, `.filter()`
- Support `ForeignKey` relationships with lazy-loaded access
- Chain queries: `User.filter(age__gte=25).order_by("-name").all()`

**Expected Output:**

```python
# --- Developer Usage ---
class User(Model):
    name = CharField(max_length=100)
    email = CharField(max_length=255, unique=True)
    age = IntegerField(nullable=True)

class Post(Model):
    title = CharField(max_length=200)
    author = ForeignKey(User, related_name="posts")

# --- Runtime Output ---
>>> User.create_table()
SQL: CREATE TABLE IF NOT EXISTS user (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       name VARCHAR(100) NOT NULL,
       email VARCHAR(255) NOT NULL UNIQUE,
       age INTEGER
     );
Table 'user' created.

>>> alice = User(name="Alice", email="alice@example.com", age=30)
>>> alice.save()
SQL: INSERT INTO user (name, email, age) VALUES ('Alice', 'alice@example.com', 30);
Record saved: User(id=1)

>>> users = User.filter(age__gte=25).order_by("-name").all()
SQL: SELECT * FROM user WHERE age >= 25 ORDER BY name DESC;
[User(id=1, name='Alice', email='alice@example.com', age=30)]

>>> alice.posts  # lazy-loaded relationship
SQL: SELECT * FROM post WHERE author_id = 1;
[Post(id=1, title='Hello World', author_id=1)]
```