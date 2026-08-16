from fastapi import HTTPException, status


class LastAdminProtectionError(HTTPException):
    def __init__(self, detail: str = "Cannot remove or demote the last admin"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)
