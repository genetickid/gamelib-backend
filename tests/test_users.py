import pytest
from fastapi import status
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from gamelib.models import User
from gamelib.schemas import UserRole
from gamelib.utils.db import is_user_last_admin

BASE_URL = '/users'


async def test_integrity_check_first_half(session):
    user = User(
        username='aboba',
        role=UserRole.USER,
        password_hash='aboba123'
    )
    session.add(user)
    await session.commit()


async def test_integrity_check_second_half(session):
    user = User(
        username='aboba',
        role=UserRole.USER,
        password_hash='aboba123'
    )
    session.add(user)
    await session.commit()


async def test_own_profile_with_no_token(client, make_user):
    user_id, _ = await make_user(UserRole.USER)
    response = await client.get(
        f'{BASE_URL}/{user_id}',
        headers={}
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_own_profile_with_invalid_token(client, make_user):
    user_id, _ = await make_user(UserRole.USER)
    response = await client.get(
        f'{BASE_URL}/{user_id}',
        headers={'Authorization': 'Bearer aboba'}
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_own_profile_availability(client, make_user):
    user_id, headers = await make_user(UserRole.USER)
    response = await client.get(f'{BASE_URL}/{user_id}', headers=headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['id'] == user_id
    assert data.get('password_hash') is None


async def test_other_profiles_unavailable_for_user(client, make_user):
    _, headers1 = await make_user(UserRole.USER)
    user2_id, _ = await make_user(UserRole.USER)

    response = await client.get(f'{BASE_URL}/{user2_id}', headers=headers1)

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_other_profiles_available_for_admin(client, make_user):
    _, headers1 = await make_user(UserRole.ADMIN)
    user2_id, _ = await make_user(UserRole.USER)

    response = await client.get(f'{BASE_URL}/{user2_id}', headers=headers1)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()['id'] == user2_id


async def test_user_cant_update_other_profiles(client, make_user):
    _, headers1 = await make_user(UserRole.USER)
    user2_id, _ = await make_user(UserRole.USER)

    response = await client.patch(
        f'{BASE_URL}/{user2_id}',
        json={'name': 'vasya'},
        headers=headers1
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_user_cant_delete_other_profiles(client, make_user):
    _, headers1 = await make_user(UserRole.USER)
    user2_id, _ = await make_user(UserRole.USER)

    response = await client.delete(f'{BASE_URL}/{user2_id}', headers=headers1)

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_admin_can_update_other_profiles(client, make_user):
    _, headers1 = await make_user(UserRole.ADMIN)
    user2_id, _ = await make_user(UserRole.USER)

    response = await client.patch(
        f'{BASE_URL}/{user2_id}',
        json={'name': 'vasya'},
        headers=headers1
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['id'] == user2_id
    assert data['name'] == 'vasya'


async def test_admin_can_delete_other_profiles(client, make_user):
    _, headers1 = await make_user(UserRole.ADMIN)
    user2_id, _ = await make_user(UserRole.USER)

    response = await client.delete(
        f'{BASE_URL}/{user2_id}',
        headers=headers1
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT


async def test_deletion_of_nonexistent_user(client, make_user):
    _, headers = await make_user(UserRole.ADMIN)
    response = await client.delete(
        f'{BASE_URL}/123456789',
        headers=headers
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_same_user_second_deletion_returns_404(client, make_user):
    _, headers = await make_user(UserRole.ADMIN)
    user_id, _ = await make_user(UserRole.USER)

    first = await client.delete(f'{BASE_URL}/{user_id}', headers=headers)
    assert first.status_code == status.HTTP_204_NO_CONTENT

    second = await client.delete(f'{BASE_URL}/{user_id}', headers=headers)
    assert second.status_code == status.HTTP_404_NOT_FOUND


async def test_user_cant_create_other_users(client, make_user):
    _, headers = await make_user(UserRole.USER)
    response = await client.post(
        BASE_URL,
        json={'username': 'vasya',
              'password': 'aboba123',
              'role': UserRole.USER},
        headers=headers
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


async def test_admin_can_create_other_users(client, make_user):
    _, headers = await make_user(UserRole.ADMIN)
    response = await client.post(
        BASE_URL,
        json={'username': 'vasya',
              'password': 'aboba123',
              'role': UserRole.USER},
        headers=headers
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()['username'] == 'vasya'
    assert response.json()['role'] == UserRole.USER


async def test_user_can_update_own_username(client, make_user):
    user_id, headers = await make_user(UserRole.USER)
    response = await client.put(
        f'{BASE_URL}/{user_id}/username',
        json={'username': 'gremlin'},
        headers=headers
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()['username'] == 'gremlin'


async def test_user_cant_update_other_usernames(client, make_user):
    _, headers = await make_user(UserRole.USER)
    user2_id, _ = await make_user(UserRole.USER)
    response = await client.put(
        f'{BASE_URL}/{user2_id}/username',
        json={'username': 'gremlin'},
        headers=headers
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_user_cant_take_already_taken_usernames(client, make_user):
    user_id, headers = await make_user(UserRole.USER)
    user2_id, headers2 = await make_user(UserRole.USER)
    user2_data = (await client.get(f'{BASE_URL}/{user2_id}', headers=headers2)).json()
    response = await client.put(
        f'{BASE_URL}/{user_id}/username',
        json={'username': user2_data['username']},
        headers=headers
    )

    assert response.status_code == status.HTTP_409_CONFLICT


async def test_admin_can_update_other_usernames(client, make_user):
    _, headers = await make_user(UserRole.ADMIN)
    user2_id, _ = await make_user(UserRole.USER)
    response = await client.put(
        f'{BASE_URL}/{user2_id}/username',
        json={'username': 'gremlin'},
        headers=headers
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()['username'] == 'gremlin'


async def test_user_cant_update_own_role(client, make_user):
    user_id, headers = await make_user(UserRole.USER)
    response = await client.put(
        f'{BASE_URL}/{user_id}/role',
        json={'role': UserRole.ADMIN},
        headers=headers
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


async def test_admin_can_update_other_roles(client, make_user):
    _, headers = await make_user(UserRole.ADMIN)
    user2_id, _ = await make_user(UserRole.USER)
    response = await client.put(
        f'{BASE_URL}/{user2_id}/role',
        json={'role': UserRole.ADMIN},
        headers=headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['id'] == user2_id
    assert data['role'] == UserRole.ADMIN


async def test_admin_can_delete_another_admin_when_not_last(client, make_user):
    _, headers1 = await make_user(UserRole.ADMIN)
    admin2_id, _ = await make_user(UserRole.ADMIN)

    response = await client.delete(
        f'{BASE_URL}/{admin2_id}',
        headers=headers1
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT


async def test_admin_can_demote_another_admin_when_not_last(client, make_user):
    _, headers1 = await make_user(UserRole.ADMIN)
    admin2_id, _ = await make_user(UserRole.ADMIN)

    response = await client.put(
        f'{BASE_URL}/{admin2_id}/role',
        json={'role': UserRole.USER},
        headers=headers1
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()['role'] == UserRole.USER


async def test_last_admin_cant_update_own_role(client, make_user):
    admin_id, headers = await make_user(UserRole.ADMIN)
    response = await client.put(
        f'{BASE_URL}/{admin_id}/role',
        json={'role': UserRole.USER},
        headers=headers
    )

    assert response.status_code == status.HTTP_409_CONFLICT


async def test_last_admin_cant_delete_himself(client, make_user):
    admin_id, headers = await make_user(UserRole.ADMIN)
    response = await client.delete(
        f'{BASE_URL}/{admin_id}',
        headers=headers
    )

    assert response.status_code == status.HTTP_409_CONFLICT


async def test_is_user_last_admin_lock(engine):
    async with (
        AsyncSession(bind=engine, expire_on_commit=False) as session1,
        AsyncSession(bind=engine, expire_on_commit=False) as session2
    ):
        admin1 = User(
            username='admin1', password_hash='sduhgsg', role=UserRole.ADMIN
        )
        admin2 = User(
            username='admin2', password_hash='ghdughd', role=UserRole.ADMIN)

        session1.add_all([admin1, admin2])
        await session1.commit()

        try:
            is_last = await is_user_last_admin(session1, admin2)

            assert is_last is False

            await session2.execute(text("SET lock_timeout = '100ms';"))

            with pytest.raises(DBAPIError) as exc:
                await is_user_last_admin(session2, admin1)

            assert exc.value.orig.sqlstate == '55P03'
        finally:
            await session1.delete(admin1)
            await session1.delete(admin2)
            await session1.commit()
