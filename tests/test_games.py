import pytest
from fastapi import status

from gamelib.schemas import UserRole

BASE_URL = '/games'


async def test_anon_can_read_game_catalog(client, make_game):
    game = await make_game()

    response = await client.get(BASE_URL)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    game_data = data[0]
    assert game_data['id'] == game.id
    assert game_data['title'] == game.title


async def test_anon_can_read_game(client, make_game):
    game = await make_game()

    response = await client.get(f'{BASE_URL}/{game.id}')

    assert response.status_code == status.HTTP_200_OK
    game_data = response.json()
    assert game_data['id'] == game.id
    assert game_data['title'] == game.title


@pytest.mark.parametrize(
    'role, expected_status',
    [
        ('anon', status.HTTP_401_UNAUTHORIZED),
        ('user', status.HTTP_403_FORBIDDEN)
    ]
)
@pytest.mark.parametrize(
    'method',
    ['POST', 'PATCH', 'DELETE']
)
async def test_non_admin_cant_modify_game_catalog(
    client, role, method, expected_status, make_user, make_game
):
    headers = {}
    if role == 'user':
        _, headers = await make_user(UserRole.USER)

    url = BASE_URL

    if method != 'POST':
        game = await make_game()
        original_title = game.title
        original_genre = game.genre
        url += f'/{game.id}'

    kwargs = {'headers': headers}
    payload = {'title': 'Postal', 'genre': 'comedy'}

    if method != 'DELETE':
        kwargs['json'] = payload

    response = await client.request(
        method,
        url,
        **kwargs
    )

    assert response.status_code == expected_status


async def test_admin_can_create_game(client, make_user):
    _, headers = await make_user(UserRole.ADMIN)
    game_data = {'title': 'Postal', 'genre': 'comedy'}

    kwargs = {
        'headers': headers,
        'json': game_data
    }

    response = await client.post(BASE_URL, **kwargs)

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data['title'] == game_data['title']
    assert data['genre'] == game_data['genre']

    response = await client.get(f"{BASE_URL}/{data['id']}")
    assert response.status_code == status.HTTP_200_OK
    saved_data = response.json()
    assert saved_data['id'] == data['id']
    assert saved_data['title'] == game_data['title']
    assert saved_data['genre'] == game_data['genre']


async def test_admin_can_delete_game(client, make_user, make_game):
    _, headers = await make_user(UserRole.ADMIN)
    game = await make_game()
    url = BASE_URL + f'/{game.id}'

    response = await client.delete(url, headers=headers)

    assert response.status_code == status.HTTP_204_NO_CONTENT

    response = await client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_admin_can_update_game(client, make_user, make_game):
    _, headers = await make_user(UserRole.ADMIN)
    game = await make_game()
    url = BASE_URL + f'/{game.id}'
    updated_game_data = {'title': 'Postal', 'genre': 'comedy'}

    kwargs = {
        'headers': headers,
        'json': updated_game_data
    }

    response = await client.patch(url, **kwargs)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['title'] == updated_game_data['title']
    assert data['genre'] == updated_game_data['genre']

    response = await client.get(url)
    assert response.status_code == status.HTTP_200_OK
    saved_data = response.json()
    assert saved_data['id'] == game.id
    assert saved_data['title'] == updated_game_data['title']
    assert saved_data['genre'] == updated_game_data['genre']


@pytest.mark.parametrize(
    'payload',
    [{'title': 'Portal'}, {'title': 'Portal', 'genre': None}]
)
async def test_create_game_without_genre(client, make_user, payload):
    _, headers = await make_user(UserRole.ADMIN)

    response = await client.post(
        BASE_URL,
        json=payload,
        headers=headers,
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    response = await client.get(BASE_URL)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


@pytest.mark.parametrize('field', ['title', 'genre'])
async def test_cant_nullify_game_field(client, make_user, make_game, field):
    _, headers = await make_user(UserRole.ADMIN)
    game = await make_game()
    original_title = game.title
    original_genre = game.genre

    response = await client.patch(
        f'{BASE_URL}/{game.id}',
        json={field: None},
        headers=headers,
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    response = await client.get(f'{BASE_URL}/{game.id}')
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['title'] == original_title
    assert data['genre'] == original_genre


async def test_game_without_genre_included_in_game_catalog(client, make_game):
    game = await make_game(genre=None)

    response = await client.get(BASE_URL)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    game_data = data[0]
    assert game_data['title'] == game.title
    assert game_data['genre'] is None
