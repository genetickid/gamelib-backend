import re


def process_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # Add async to def test_
    content = re.sub(r'^def test_', 'async def test_', content, flags=re.MULTILINE)

    # Add await to client.get, client.post, etc.
    content = re.sub(r'(\s+.*?= |^\s*)client\.(get|post|put|patch|delete)\(', r'\1await client.\2(', content, flags=re.MULTILINE)

    # Add await to make_user
    content = re.sub(r'(\s+.*?= |^\s*)make_user\(', r'\1await make_user(', content, flags=re.MULTILINE)

    # Process specific test_is_user_last_admin_lock in test_users.py
    if 'test_is_user_last_admin_lock' in content:
        # replace Session with AsyncSession
        content = content.replace('from sqlalchemy.orm import Session', 'from sqlalchemy.ext.asyncio import AsyncSession')
        content = content.replace('Session(bind=engine', 'AsyncSession(bind=engine')
        # with -> async with
        content = content.replace('with (\n', 'async with (\n')
        # session.commit() -> await session.commit()
        content = re.sub(r'(\s+)session(\d)\.commit\(\)', r'\1await session\2.commit()', content)
        # session.execute -> await session.execute
        content = re.sub(r'(\s+)session(\d)\.execute\(', r'\1await session\2.execute(', content)
        # is_user_last_admin -> await is_user_last_admin
        content = re.sub(r'(\s+.*?= |^\s*)is_user_last_admin\(', r'\1await is_user_last_admin(', content)

    with open(filepath, 'w') as f:
        f.write(content)

process_file('tests/test_auth.py')
process_file('tests/test_users.py')
