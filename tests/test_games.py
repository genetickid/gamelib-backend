import pytest
from fastapi import status

from gamelib.schemas import UserRole

BASE_URL = '/games'


@pytest.mark.skip(reason='TODO')
async def test_anon_cant_create_game(client, make_user):
    pass


@pytest.mark.skip(reason='TODO')
async def test_anon_cant_delete_game(client, make_user):
    pass


@pytest.mark.skip(reason='TODO')
async def test_anon_cant_update_game(client, make_user):
    pass


@pytest.mark.skip(reason='TODO')
async def test_admin_can_create_game(client, make_user):
    pass


@pytest.mark.skip(reason='TODO')
async def test_admin_can_delete_game(client, make_user):
    pass


@pytest.mark.skip(reason='TODO')
async def test_admin_can_update_game(client, make_user):
    pass


@pytest.mark.skip(reason='TODO')
async def test_user_cant_create_game(client, make_user):
    pass


@pytest.mark.skip(reason='TODO')
async def test_user_cant_delete_game(client, make_user):
    pass


@pytest.mark.skip(reason='TODO')
async def test_user_cant_update_game(client, make_user):
    pass


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


async def test_game_without_genre_included_in_games_list(client, make_game):
    game = await make_game(genre=None)

    response = await client.get(BASE_URL)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    game_data = data[0]
    assert game_data['title'] == game.title
    assert game_data['genre'] is None
