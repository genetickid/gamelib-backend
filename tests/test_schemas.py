import pytest
from pydantic import ValidationError

from gamelib.schemas import UserAuth


def build_test_data(fields_to_remove=None, **kwargs):
    test_data = {
        'username': 'normal_user',
        'password': 'normalpassword123'
    }
    test_data.update(kwargs)
    if fields_to_remove:
        for field_name in fields_to_remove:
            test_data.pop(field_name, None)
    return test_data

@pytest.mark.parametrize(
    'valid_data', [
        pytest.param(build_test_data(name='Vasya', password='1' * 9), id="with_name"),
        pytest.param(build_test_data(username='main', about='Petya', password='1' * 9), id="with_about"),
        pytest.param(build_test_data(username='a' * 32, password='1' * 9), id="username_max_length"),
        pytest.param(build_test_data(name=None, about=None, password='1' * 9), id="explicit_none_optional_fields"),
        pytest.param(build_test_data(username='abc', password='1' * 8), id="password_min_length"),
        pytest.param(build_test_data(username='abc', password='1' * 64), id="password_max_length")
    ]
)
def test_valid_user_auth(valid_data):
    user = UserAuth(**valid_data)
    assert user.username == valid_data['username']
    assert user.password == valid_data['password']


@pytest.mark.parametrize(
    'invalid_data', [
        pytest.param(build_test_data(username='a'), id="username_too_short"),
        pytest.param(build_test_data(username=None), id="username_is_none"),
        pytest.param(build_test_data(username='a' * 33), id="username_too_long"),
        pytest.param(build_test_data(name='me', fields_to_remove=['username']), id="missing_username"),
        pytest.param(build_test_data(username=123), id="username_is_integer"),
        pytest.param(build_test_data(name=123), id="name_is_integer"),
        pytest.param(build_test_data(password='1' * 7), id="password_too_short"),
        pytest.param(build_test_data(password='1' * 65), id="password_too_long"),
        pytest.param(build_test_data(fields_to_remove=['password']), id="missing_password"),
        pytest.param(build_test_data(password=12345678), id="password_is_integer")
    ]
)
def test_invalid_user_auth(invalid_data):
    with pytest.raises(ValidationError):
        UserAuth(**invalid_data)
