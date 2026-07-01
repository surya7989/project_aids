from datetime import datetime, timedelta, timezone
from hashlib import sha256
from sqlalchemy.ext.asyncio import AsyncSession
from ..repositories.user_repository import UserRepository, RoleRepository, RefreshTokenRepository
from ..repositories.base import BaseRepository
from ..models.audit import AuditLog
from ..security.auth import hash_password, verify_password, create_tokens, decode_token
from ..middleware.error_handler import UnauthorizedException, ConflictException, NotFoundException
from ..config.settings import settings
from ..core.logging import get_logger

logger = get_logger(__name__)


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.role_repo = RoleRepository(session)
        self.token_repo = RefreshTokenRepository(session)
        self.audit_repo = BaseRepository(AuditLog, session)

    async def register(self, email: str, username: str, password: str, full_name: str = None) -> dict:
        existing = await self.user_repo.get_by_email(email)
        if existing:
            raise ConflictException("Email already registered")

        existing_username = await self.user_repo.get_by_username(username)
        if existing_username:
            raise ConflictException("Username already taken")

        hashed_pw = hash_password(password)
        user = await self.user_repo.create(
            email=email,
            username=username,
            hashed_password=hashed_pw,
            full_name=full_name,
        )

        viewer_role = await self.role_repo.get_by_name("viewer")
        if viewer_role:
            await self.user_repo.assign_role(str(user.id), str(viewer_role.id))

        await self._log_audit(str(user.id), "USER_REGISTER", "users", str(user.id), {"email": email})

        access_token, refresh_token = create_tokens(
            str(user.id), user.email, ["viewer"]
        )

        await self._store_refresh_token(str(user.id), refresh_token)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "is_verified": user.is_verified,
                "created_at": user.created_at,
                "roles": ["viewer"],
            },
        }

    async def login(self, username: str, password: str, ip_address: str = None) -> dict:
        user = await self.user_repo.get_by_username(username)
        if not user:
            user = await self.user_repo.get_by_email(username)

        if not user:
            raise UnauthorizedException("Invalid credentials")

        if not user.is_active:
            raise UnauthorizedException("Account is disabled")

        if user.locked_until and user.locked_until > datetime.now(timezone.utc):
            raise UnauthorizedException("Account is locked. Try again later.")

        if not verify_password(password, user.hashed_password):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0) + timedelta(hours=1)
            await self.session.flush()
            await self._log_audit(str(user.id), "LOGIN_FAILED", "users", str(user.id), {"ip": ip_address})
            raise UnauthorizedException("Invalid credentials")

        user.failed_login_attempts = 0
        user.last_login = datetime.now(timezone.utc)
        user.locked_until = None

        roles = [role.name for role in user.roles] if user.roles else ["viewer"]

        access_token, refresh_token = create_tokens(str(user.id), user.email, roles)
        await self._store_refresh_token(str(user.id), refresh_token)

        await self._log_audit(str(user.id), "LOGIN_SUCCESS", "users", str(user.id), {"ip": ip_address})

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "created_at": user.created_at,
                "roles": roles,
                "last_login": user.last_login,
            },
        }

    async def refresh_token(self, refresh_token: str) -> dict:
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise UnauthorizedException("Invalid refresh token")

        user_id = payload.get("sub")
        token_hash = sha256(refresh_token.encode()).hexdigest()

        stored_token = await self.token_repo.get_by_token_hash(token_hash)
        if not stored_token:
            raise UnauthorizedException("Refresh token has been revoked")

        user = await self.user_repo.get(user_id)
        if not user:
            raise UnauthorizedException("User not found")

        stored_token.is_revoked = True
        roles = [role.name for role in user.roles] if user.roles else ["viewer"]

        new_access, new_refresh = create_tokens(str(user.id), user.email, roles)
        await self._store_refresh_token(str(user.id), new_refresh)

        return {
            "access_token": new_access,
            "refresh_token": new_refresh,
        }

    async def logout(self, user_id: str) -> None:
        await self.token_repo.revoke_all_for_user(user_id)

    async def change_password(self, user_id: str, current_password: str, new_password: str) -> None:
        user = await self.user_repo.get(user_id)
        if not user:
            raise NotFoundException("User")

        if not verify_password(current_password, user.hashed_password):
            raise UnauthorizedException("Current password is incorrect")

        user.hashed_password = hash_password(new_password)
        await self.token_repo.revoke_all_for_user(user_id)
        await self.session.flush()

    async def get_current_user(self, user_id: str) -> dict:
        user = await self.user_repo.get(user_id)
        if not user:
            raise NotFoundException("User")

        roles = [role.name for role in user.roles] if user.roles else []
        return {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "roles": roles,
            "created_at": user.created_at,
            "last_login": user.last_login,
        }

    async def _store_refresh_token(self, user_id: str, token: str) -> None:
        token_hash = sha256(token.encode()).hexdigest()
        from datetime import timedelta
        expires = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        await self.token_repo.create(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires,
        )

    async def _log_audit(self, user_id: str, action: str, resource: str, resource_id: str, details: dict = None) -> None:
        try:
            await self.audit_repo.create(
                user_id=user_id,
                action=action,
                resource=resource,
                resource_id=resource_id,
                details=details or {},
            )
        except Exception as e:
            logger.error(f"Failed to log audit: {e}")

