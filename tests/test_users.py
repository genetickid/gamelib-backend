import pytest
from fastapi import status
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from gamelib.models import User
from gamelib.schemas import UserRole
from gamelib.utils.db import is_user_last_admin

BASE_URL = '/users'
TEST_STEAM_ID = '76561198087654321'
OTHER_STEAM_ID = '76561198012345678'
STEAM_ID_UPDATE_CASES = [
    pytest.param(None, TEST_STEAM_ID, id='set_valid_id'),
    pytest.param(TEST_STEAM_ID, OTHER_STEAM_ID, id='replace_id'),
    pytest.param(TEST_STEAM_ID, None, id='remove_id'),
]


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


@pytest.mark.parametrize('old_steam_id, new_steam_id', STEAM_ID_UPDATE_CASES)
async def test_user_can_update_own_steam_id(
    client, make_user, old_steam_id, new_steam_id
):
    user_id, headers = await make_user(
        UserRole.USER, steam_id=old_steam_id
    )
    url = f'{BASE_URL}/{user_id}'

    response = await client.patch(
        url,
        headers=headers,
        json={'steam_id': new_steam_id}
    )

    assert response.status_code == status.HTTP_200_OK, response.text
    assert response.json()['id'] == user_id
    assert response.json()['steam_id'] == new_steam_id

    response = await client.get(url, headers=headers)

    assert response.status_code == status.HTTP_200_OK, response.text
    assert response.json()['steam_id'] == new_steam_id


@pytest.mark.parametrize('old_steam_id, new_steam_id', STEAM_ID_UPDATE_CASES)
async def test_user_cant_update_other_user_steam_id(
    client, make_user, old_steam_id, new_steam_id
):
    _, headers = await make_user(UserRole.USER)
    user_id, user_headers = await make_user(
        UserRole.USER, steam_id=old_steam_id
    )
    url = f'{BASE_URL}/{user_id}'

    response = await client.patch(
        url,
        headers=headers,
        json={'steam_id': new_steam_id}
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND, response.text

    response = await client.get(url, headers=user_headers)

    assert response.status_code == status.HTTP_200_OK, response.text
    assert response.json()['steam_id'] == old_steam_id


@pytest.mark.parametrize('old_steam_id, new_steam_id', STEAM_ID_UPDATE_CASES)
async def test_admin_can_update_other_user_steam_id(
    client, make_user, old_steam_id, new_steam_id
):
    _, admin_headers = await make_user(UserRole.ADMIN)
    user_id, user_headers = await make_user(
        UserRole.USER, steam_id=old_steam_id
    )
    url = f'{BASE_URL}/{user_id}'

    response = await client.patch(
        url,
        headers=admin_headers,
        json={'steam_id': new_steam_id}
    )

    assert response.status_code == status.HTTP_200_OK, response.text
    assert response.json()['id'] == user_id
    assert response.json()['steam_id'] == new_steam_id

    response = await client.get(url, headers=user_headers)

    assert response.status_code == status.HTTP_200_OK, response.text
    assert response.json()['steam_id'] == new_steam_id

    response = await client.get(f'{BASE_URL}/me', headers=admin_headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()['steam_id'] is None


@pytest.mark.parametrize('old_steam_id, new_steam_id', STEAM_ID_UPDATE_CASES)
async def test_anon_cant_update_steam_id(
    client, make_user, old_steam_id, new_steam_id
):
    user_id, headers = await make_user(
        UserRole.USER, steam_id=old_steam_id
    )
    url = f'{BASE_URL}/{user_id}'

    response = await client.patch(url, json={'steam_id': new_steam_id})

    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    response = await client.get(url, headers=headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()['steam_id'] == old_steam_id


@pytest.mark.parametrize(
    'invalid_steam_id',
    [
        pytest.param('', id='empty'),
        pytest.param(TEST_STEAM_ID[:-1], id='too_short'),
        pytest.param(TEST_STEAM_ID + '1', id='too_long'),
        pytest.param('86561191111111111', id='wrong_prefix'),
        pytest.param('76561211111111111', id='wrong_prefix_2'),
        pytest.param(TEST_STEAM_ID[:-1] + 'a', id='contains_letter'),
        pytest.param(' ' + TEST_STEAM_ID, id='leading_space'),
        pytest.param(TEST_STEAM_ID + '\n', id='trailing_newline'),
        pytest.param(76561198012345678, id='number_instead_of_string')
    ]
)
async def test_user_cant_set_invalid_steam_id(client, make_user, invalid_steam_id):
    user_id, headers = await make_user(UserRole.USER, steam_id=TEST_STEAM_ID)
    url = f'{BASE_URL}/{user_id}'

    response = await client.patch(
        url,
        headers=headers,
        json={'steam_id': invalid_steam_id}
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    response = await client.get(url, headers=headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()['steam_id'] == TEST_STEAM_ID


async def test_users_can_set_same_steam_id(client, make_user):
    users = [
        await make_user(UserRole.USER),
        await make_user(UserRole.USER),
    ]

    for user_id, headers in users:
        response = await client.patch(
            f'{BASE_URL}/{user_id}',
            headers=headers,
            json={'steam_id': TEST_STEAM_ID}
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['id'] == user_id
        assert response.json()['steam_id'] == TEST_STEAM_ID

    for user_id, headers in users:
        response = await client.get(f'{BASE_URL}/{user_id}', headers=headers)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['id'] == user_id
        assert response.json()['steam_id'] == TEST_STEAM_ID


@pytest.mark.parametrize(
    'payload, expected_name',
    [
        pytest.param({}, None, id='empty_patch'),
        pytest.param({'name': 'Vasya'}, 'Vasya', id='update_other_field'),
    ]
)
async def test_user_update_without_new_steam_id_preserves_old_one(
    client, make_user, payload, expected_name
):
    user_id, headers = await make_user(UserRole.USER, steam_id=TEST_STEAM_ID)
    url = f'{BASE_URL}/{user_id}'

    response = await client.patch(url, headers=headers, json=payload)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()['steam_id'] == TEST_STEAM_ID
    assert response.json()['name'] == expected_name

    response = await client.get(url, headers=headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()['steam_id'] == TEST_STEAM_ID
    assert response.json()['name'] == expected_name
