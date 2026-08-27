from datetime import datetime, timezone

from fastapi import status

from gamelib.constants import GAME_NOT_FOUND_MSG, USER_NOT_FOUND_MSG
from gamelib.schemas import GameStatus, UserRole

BASE_URL = '/users'


async def test_create_library_entry(client, make_user, make_game, query_counter):
    user_id, headers = await make_user(UserRole.USER)
    game = await make_game()

    with query_counter() as queries:
        response = await client.post(
            f'{BASE_URL}/{user_id}/library',
            json={'game_id': game.id},
            headers=headers,
        )

    assert response.status_code == status.HTTP_201_CREATED
    assert len(queries) == 3

    data = response.json()

    added_at = datetime.fromisoformat(data['added_at'])
    now = datetime.now(timezone.utc)
    assert abs((added_at - now).total_seconds()) < 5

    assert data['status'] == GameStatus.BACKLOG
    assert data['hours_played'] == 0.0
    assert data['rating'] is None

    game_data = data['game']
    assert game_data['id'] == game.id
    assert game_data['title'] == game.title
    assert game_data['genre'] == game.genre
    expected_value = None if game.release_date is None else str(game.release_date)
    assert game_data['release_date'] == expected_value


async def test_duplicate_conflict(client, make_user, make_game):
    user_id, headers = await make_user(UserRole.USER)
    game = await make_game()

    response1 = await client.post(
        f'{BASE_URL}/{user_id}/library',
        json={'game_id': game.id},
        headers=headers,
    )
    assert response1.status_code == status.HTTP_201_CREATED

    response2 = await client.post(
        f'{BASE_URL}/{user_id}/library',
        json={'game_id': game.id},
        headers=headers,
    )
    assert response2.status_code == status.HTTP_409_CONFLICT
    assert response2.json()['detail'] == 'This library already contains this game.'


async def test_cant_create_entry_with_nonexistent_game(client, make_user, make_game):
    user_id, headers = await make_user(UserRole.USER)

    response1 = await client.post(
        f'{BASE_URL}/{user_id}/library',
        json={'game_id': 666},
        headers=headers,
    )
    assert response1.status_code == status.HTTP_404_NOT_FOUND
    assert response1.json()['detail'] == GAME_NOT_FOUND_MSG


async def test_user_cant_create_entry_for_other_user(client, make_user, make_game):
    _, headers1 = await make_user(UserRole.USER)
    user2_id, _ = await make_user(UserRole.USER)
    game = await make_game()

    response = await client.post(
        f'{BASE_URL}/{user2_id}/library',
        json={'game_id': game.id},
        headers=headers1,
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()['detail'] == USER_NOT_FOUND_MSG


async def test_admin_can_create_entry_for_other_user(client, make_user, make_game):
    _, admin_headers = await make_user(UserRole.ADMIN)
    user_id, _ = await make_user(UserRole.USER)
    game = await make_game()

    response = await client.post(
        f'{BASE_URL}/{user_id}/library',
        json={'game_id': game.id},
        headers=admin_headers,
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data['game']['id'] == game.id


async def test_user_cant_get_other_user_library(client, make_user, make_game):
    user1_id, headers1 = await make_user(UserRole.USER)
    user2_id, headers2 = await make_user(UserRole.USER)
    game = await make_game()

    response1 = await client.post(
        f'{BASE_URL}/{user1_id}/library',
        json={'game_id': game.id},
        headers=headers1,
    )
    assert response1.status_code == status.HTTP_201_CREATED

    response2 = await client.get(
        f'{BASE_URL}/{user1_id}/library',
        headers=headers2
    )
    assert response2.status_code == status.HTTP_404_NOT_FOUND


async def test_admin_can_get_other_user_library(client, make_user, make_game):
    user1_id, headers1 = await make_user(UserRole.USER)
    user2_id, headers2 = await make_user(UserRole.ADMIN)
    game = await make_game()

    response1 = await client.post(
        f'{BASE_URL}/{user1_id}/library',
        json={'game_id': game.id},
        headers=headers1,
    )
    assert response1.status_code == status.HTTP_201_CREATED

    response2 = await client.get(
        f'{BASE_URL}/{user1_id}/library',
        headers=headers2
    )
    assert response2.status_code == status.HTTP_200_OK
    data = response2.json()
    assert data[0]['game']['id'] == game.id


async def test_user_with_empty_library(client, make_user, make_game):
    user_id, headers = await make_user(UserRole.USER)

    response = await client.get(
        f'{BASE_URL}/{user_id}/library',
        headers=headers
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


async def test_different_libraries_isolated_from_each_other(client, make_user, make_game):
    user1_id, headers1 = await make_user(UserRole.USER)
    user2_id, headers2 = await make_user(UserRole.USER)

    games = [await make_game() for _ in range(3)]

    for game in games[:2]:
        res = await client.post(
            f'{BASE_URL}/{user1_id}/library',
            json={'game_id': game.id},
            headers=headers1,
        )
        assert res.status_code == status.HTTP_201_CREATED

    res = await client.post(
        f'{BASE_URL}/{user2_id}/library',
        json={'game_id': games[2].id},
        headers=headers2,
    )
    assert res.status_code == status.HTTP_201_CREATED

    response = await client.get(
        f'{BASE_URL}/{user1_id}/library',
        headers=headers1,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2

    returned_ids = {entry['game']['id'] for entry in data}
    assert returned_ids == {games[0].id, games[1].id}
    assert games[2].id not in returned_ids


async def test_library_entry_data_consistency(client, make_user, make_game):
    user_id, headers = await make_user(UserRole.USER)
    game = await make_game()

    response = await client.post(
        f'{BASE_URL}/{user_id}/library',
        json={
            'game_id': game.id,
            'hours_played': 11.0,
            'status': GameStatus.COMPLETED,
        },
        headers=headers,
    )
    assert response.status_code == status.HTTP_201_CREATED

    response = await client.get(
        f'{BASE_URL}/{user_id}/library',
        headers=headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1

    lib_entry = data[0]
    assert lib_entry['game']['id'] == game.id
    assert lib_entry['game']['title'] == game.title
    assert lib_entry['game']['genre'] == game.genre
    assert lib_entry['hours_played'] == 11.0
    assert lib_entry['status'] == GameStatus.COMPLETED


async def test_n_plus_one(client, make_user, make_game, query_counter):
    user1_id, headers1 = await make_user(UserRole.USER)
    user2_id, headers2 = await make_user(UserRole.USER)

    games = [await make_game() for _ in range(4)]

    res1 = await client.post(
        f'{BASE_URL}/{user1_id}/library',
        json={'game_id': games[0].id},
        headers=headers1,
    )
    assert res1.status_code == status.HTTP_201_CREATED

    for game in games[1:]:
        res2 = await client.post(
            f'{BASE_URL}/{user2_id}/library',
            json={'game_id': game.id},
            headers=headers2,
        )
        assert res2.status_code == status.HTTP_201_CREATED

    with query_counter() as queries1:
        response1 = await client.get(
            f'{BASE_URL}/{user1_id}/library',
            headers=headers1,
        )
        assert response1.status_code == status.HTTP_200_OK

    with query_counter() as queries2:
        response2 = await client.get(
            f'{BASE_URL}/{user2_id}/library',
            headers=headers2,
        )
        assert response2.status_code == status.HTTP_200_OK

    assert len(response1.json()) == 1
    assert len(response2.json()) == 3
    assert queries1 is not queries2
    assert len(queries1) == 3
    assert len(queries2) == 3
    assert len(queries1) == len(queries2)


