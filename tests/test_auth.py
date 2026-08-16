from fastapi import status

from gamelib.schemas import UserRole

VALID_USER = {
    'username': 'abuser',
    'password': 'trespass',
    'about': 'roundabout',
    'name': 'eman'
}

BASE_URL = '/auth'

async def test_valid_registration(client):
    response = await client.post(f'{BASE_URL}/register', json=VALID_USER)

    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()
    assert data.get('password') is None
    assert data.get('password_hash') is None
    assert data['username'] == VALID_USER['username']
    assert data['about'] == VALID_USER['about']
    assert data['name'] == VALID_USER['name']
    assert data['role'] == UserRole.USER


async def test_registration_with_taken_username(client):
    await client.post(f'{BASE_URL}/register', json=VALID_USER)
    response = await client.post(f'{BASE_URL}/register', json=VALID_USER)

    assert response.status_code == status.HTTP_409_CONFLICT


async def test_login_with_correct_credentials(client):
    await client.post(f'{BASE_URL}/register', json=VALID_USER)
    response = await client.post(f'{BASE_URL}/login', data={
        'username': VALID_USER['username'],
        'password': VALID_USER['password']
    })

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert 'access_token' in data
    assert 'token_type' in data
    assert data['token_type'] == 'bearer'


async def test_login_with_incorrect_username(client):
    await client.post(f'{BASE_URL}/register', json=VALID_USER)
    response = await client.post(f'{BASE_URL}/login', data={
        'username': 'abibos',
        'password': VALID_USER['password']
    })

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()['detail'] == 'Incorrect username or password'


async def test_login_with_incorrect_password(client):
    await client.post(f'{BASE_URL}/register', json=VALID_USER)
    response = await client.post(f'{BASE_URL}/login', data={
        'username': VALID_USER['username'],
        'password': 'sosal123'
    })

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()['detail'] == 'Incorrect username or password'
