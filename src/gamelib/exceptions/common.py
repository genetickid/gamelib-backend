class GamelibError(Exception):
    pass


class ObjAlreadyExistsError(GamelibError):
    def __init__(self, message: str = 'Resource already exists.'):
        super().__init__(message)


class UserAlreadyExistsError(ObjAlreadyExistsError):
    def __init__(self, message: str = 'This username is already taken.'):
        super().__init__(message)


class LibraryEntryAlreadyExistsError(ObjAlreadyExistsError):
    def __init__(self, message: str = 'This library already contains this game.'):
        super().__init__(message)


class ObjNotFoundError(GamelibError):
    def __init__(self, message: str = 'Object not found.'):
        super().__init__(message)
