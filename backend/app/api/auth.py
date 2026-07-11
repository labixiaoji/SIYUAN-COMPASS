from fastapi import APIRouter, Depends, HTTPException

from app.schemas.auth import AuthResult, AuthUser, ChangePasswordInput, LoginInput, RegisterInput
from app.services.auth import (
    create_access_token,
    hash_password,
    normalize_username,
    public_user,
    require_user,
    verify_password,
)
from app.storage.json_db import create_account, find_user_by_username, update_user_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResult)
def register(input_data: RegisterInput) -> AuthResult:
    username = normalize_username(input_data.username)
    if not username.replace("_", "").replace("-", "").isalnum():
        raise HTTPException(status_code=400, detail={"error": "用户名只能包含字母、数字、下划线和连字符"})
    if find_user_by_username(username):
        raise HTTPException(status_code=409, detail={"error": "用户名已存在"})

    user = create_account(
        username=username,
        display_name=input_data.displayName.strip(),
        password_hash=hash_password(input_data.password),
        role="student",
    )
    return AuthResult(token=create_access_token(user), user=public_user(user))


@router.post("/login", response_model=AuthResult)
def login(input_data: LoginInput) -> AuthResult:
    user = find_user_by_username(normalize_username(input_data.username))
    if not user or not verify_password(input_data.password, user.get("passwordHash", "")):
        raise HTTPException(status_code=401, detail={"error": "用户名或密码错误"})
    return AuthResult(token=create_access_token(user), user=public_user(user))


@router.get("/me", response_model=AuthUser)
def me(user=Depends(require_user)) -> AuthUser:
    return public_user(user)


@router.post("/change-password")
def change_password(input_data: ChangePasswordInput, user=Depends(require_user)) -> dict[str, str]:
    if not verify_password(input_data.currentPassword, user.get("passwordHash", "")):
        raise HTTPException(status_code=400, detail={"error": "当前密码不正确"})
    if input_data.currentPassword == input_data.newPassword:
        raise HTTPException(status_code=400, detail={"error": "新密码不能与当前密码相同"})
    if not update_user_password(user["id"], hash_password(input_data.newPassword)):
        raise HTTPException(status_code=404, detail={"error": "用户不存在"})
    return {"message": "密码修改成功"}
