import hmac
import secrets
from urllib.parse import urlencode, urljoin, urlsplit

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse

from app.core.config import get_settings
from app.schemas.auth import AuthResult, AuthUser, ChangePasswordInput, LoginInput, RegisterInput
from app.services.auth import (
    create_access_token,
    hash_password,
    normalize_username,
    public_user,
    require_user,
    verify_password,
)
from app.services.jaccount_oauth import (
    JAccountOAuthError,
    build_authorization_url,
    decode_identity_token,
    exchange_authorization_code,
)
from app.storage.json_db import (
    create_account,
    find_user_by_username,
    update_user_password,
    upsert_jaccount_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])
OAUTH_COOKIE_MAX_AGE_SECONDS = 10 * 60
OAUTH_STATE_COOKIE = "siyuan_oauth_state"
OAUTH_NONCE_COOKIE = "siyuan_oauth_nonce"
OAUTH_NEXT_COOKIE = "siyuan_oauth_next"


@router.post("/register", response_model=AuthResult)
def register(input_data: RegisterInput) -> AuthResult:
    if not get_settings().local_auth_enabled:
        raise HTTPException(status_code=404, detail={"error": "本地账号注册已关闭"})
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
    if not get_settings().local_auth_enabled:
        raise HTTPException(status_code=404, detail={"error": "请使用 jAccount 登录"})
    user = find_user_by_username(normalize_username(input_data.username))
    if not user or not verify_password(input_data.password, user.get("passwordHash", "")):
        raise HTTPException(status_code=401, detail={"error": "用户名或密码错误"})
    return AuthResult(token=create_access_token(user), user=public_user(user))


@router.get("/me", response_model=AuthUser)
def me(user=Depends(require_user)) -> AuthUser:
    return public_user(user)


@router.post("/change-password")
def change_password(input_data: ChangePasswordInput, user=Depends(require_user)) -> dict[str, str]:
    if user.get("authSource") != "local" or not get_settings().local_auth_enabled:
        raise HTTPException(status_code=400, detail={"error": "jAccount 密码请在学校统一身份平台修改"})
    if not verify_password(input_data.currentPassword, user.get("passwordHash", "")):
        raise HTTPException(status_code=400, detail={"error": "当前密码不正确"})
    if input_data.currentPassword == input_data.newPassword:
        raise HTTPException(status_code=400, detail={"error": "新密码不能与当前密码相同"})
    if not update_user_password(user["id"], hash_password(input_data.newPassword)):
        raise HTTPException(status_code=404, detail={"error": "用户不存在"})
    return {"message": "密码修改成功"}


def _safe_app_path(value: str | None, fallback: str = "/assessment") -> str:
    settings = get_settings()
    base_path = settings.app_base_path.rstrip("/") or ""
    candidate = (value or "").strip()
    if not candidate.startswith("/") or candidate.startswith("//"):
        candidate = fallback
    if base_path and not candidate.startswith(f"{base_path}/") and candidate != base_path:
        candidate = f"{base_path}{candidate}"
    return candidate


def _absolute_app_url(path: str) -> str:
    return urljoin(get_settings().public_app_url.rstrip("/") + "/", path.lstrip("/"))


def _oauth_cookie_path() -> str:
    base_path = get_settings().app_base_path.rstrip("/")
    return f"{base_path}/api/auth/jaccount"


def _session_cookie_path() -> str:
    return get_settings().app_base_path.rstrip("/") or "/"


def _secure_cookies() -> bool:
    return urlsplit(get_settings().public_app_url).scheme == "https"


def _clear_oauth_cookies(response: RedirectResponse) -> None:
    for name in (OAUTH_STATE_COOKIE, OAUTH_NONCE_COOKIE, OAUTH_NEXT_COOKIE):
        response.delete_cookie(name, path=_oauth_cookie_path())


def _oauth_failure(message: str) -> RedirectResponse:
    login_path = _safe_app_path("/login", fallback="/login")
    separator = "&" if "?" in login_path else "?"
    response = RedirectResponse(
        url=_absolute_app_url(f"{login_path}{separator}{urlencode({'jaccount_error': message})}"),
        status_code=302,
    )
    _clear_oauth_cookies(response)
    return response


@router.get("/jaccount/login")
def jaccount_login(next_path: str | None = Query(default=None, alias="next")):
    settings = get_settings()
    if not settings.jaccount_enabled:
        raise HTTPException(status_code=503, detail={"error": "jAccount 登录尚未配置"})

    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)
    try:
        authorize_url = build_authorization_url(state=state, nonce=nonce)
    except JAccountOAuthError as exc:
        raise HTTPException(status_code=500, detail={"error": "jAccount OAuth 地址配置错误"}) from exc

    response = RedirectResponse(url=authorize_url, status_code=302)
    cookie_options = {
        "max_age": OAUTH_COOKIE_MAX_AGE_SECONDS,
        "httponly": True,
        "secure": _secure_cookies(),
        "samesite": "lax",
        "path": _oauth_cookie_path(),
    }
    response.set_cookie(OAUTH_STATE_COOKIE, state, **cookie_options)
    response.set_cookie(OAUTH_NONCE_COOKIE, nonce, **cookie_options)
    response.set_cookie(OAUTH_NEXT_COOKIE, _safe_app_path(next_path), **cookie_options)
    return response


@router.get("/jaccount/callback")
async def jaccount_callback(
    request: Request,
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    oauth_error: str | None = Query(default=None, alias="error"),
):
    if oauth_error:
        return _oauth_failure("jAccount 授权未完成，请重试。")

    expected_state = request.cookies.get(OAUTH_STATE_COOKIE)
    expected_nonce = request.cookies.get(OAUTH_NONCE_COOKIE)
    if (
        not code
        or not state
        or not expected_state
        or not expected_nonce
        or not hmac.compare_digest(state, expected_state)
    ):
        return _oauth_failure("登录状态校验失败，请重新发起登录。")

    try:
        token_payload = await exchange_authorization_code(code)
        identity = decode_identity_token(
            token_payload["id_token"],
            expected_nonce=expected_nonce,
        )
        user = upsert_jaccount_user(
            username=identity.username,
            display_name=identity.display_name,
        )
    except JAccountOAuthError:
        return _oauth_failure("jAccount 身份验证失败，请重新登录。")
    except RuntimeError:
        return _oauth_failure("该 jAccount 无法创建本地账号，请联系管理员。")

    target = _safe_app_path(request.cookies.get(OAUTH_NEXT_COOKIE))
    response = RedirectResponse(url=_absolute_app_url(target), status_code=302)
    response.set_cookie(
        get_settings().auth_cookie_name,
        create_access_token(user),
        max_age=get_settings().auth_token_hours * 3600,
        httponly=True,
        secure=_secure_cookies(),
        samesite="lax",
        path=_session_cookie_path(),
    )
    _clear_oauth_cookies(response)
    return response


@router.get("/logout")
def logout():
    settings = get_settings()
    target = settings.jaccount_post_logout_redirect_uri or settings.public_app_url
    parsed = urlsplit(settings.jaccount_logout_url)
    if parsed.scheme != "https" or urlsplit(target).scheme not in {"http", "https"}:
        raise HTTPException(status_code=500, detail={"error": "退出地址配置错误"})
    separator = "&" if parsed.query else "?"
    response = RedirectResponse(
        url=f"{settings.jaccount_logout_url}{separator}{urlencode({
            'client_id': settings.jaccount_client_id,
            'post_logout_redirect_uri': target,
            'state': secrets.token_urlsafe(24),
        })}",
        status_code=302,
    )
    response.delete_cookie(settings.auth_cookie_name, path=_session_cookie_path())
    return response
