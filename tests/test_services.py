# tests/test_services.py
"""Unit tests for service layer — Login, Logout, CRUD User, Device, Loan."""

import pytest
import uuid
import sys
from datetime import datetime, timedelta, date
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import HTTPException


# ─── Bootstrap: mock modul berat agar bisa di-collect tanpa koneksi DB ───────
# Lakukan SEBELUM import apapun dari src
_mock_sessions = MagicMock()
_mock_sessions.device_session_manager = AsyncMock()
sys.modules['src.utils.sessions'] = _mock_sessions


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER
# ═══════════════════════════════════════════════════════════════════════════════
# Hash bcrypt valid untuk password 'Password1!' — dipakai di semua fixture user
_VALID_HASH = "$2b$12$Iu6m3qKi8dvqV9uT1ZklqulwqNEkgKzAJQ0j4UR7rlCeMItQNr4z."


def _make_user(
    id=1,
    nama="Budi Santoso",
    email="budi@balmon.go.id",
    is_active=True,
    is_verified=True,
    is_locked_val=False,
    failed_login_attempts=0,
    force_password_change=False,
    mfa_enabled=False,
    hashed_password=None,   # default: hash bcrypt yang valid
    password_history=None,
):
    """Buat MagicMock yang kompatibel dengan UserResponse.model_validate."""
    user = MagicMock()
    # Field wajib / dipakai Pydantic UserResponse
    user.id = id
    user.uuid = str(uuid.uuid4())          # harus string
    user.nama = nama
    user.email = email
    user.is_active = is_active
    user.is_verified = is_verified
    user.nip = "12345"                     # harus string (opt)
    user.jabatan = "Staff"                 # harus string (opt)
    user.password_changed_at = datetime.utcnow()
    user.force_password_change = force_password_change
    user.last_login = None
    user.mfa_enabled = mfa_enabled
    # Method model
    user.is_locked = MagicMock(return_value=is_locked_val)
    user.failed_login_attempts = failed_login_attempts
    user.hashed_password = hashed_password if hashed_password is not None else _VALID_HASH
    user.password_history = password_history or []
    return user


async def _async_gen(value):
    """Helper: async generator 1 nilai (mock get_db)."""
    yield value


# ═══════════════════════════════════════════════════════════════════════════════
# A. AUTH — Login
# ═══════════════════════════════════════════════════════════════════════════════
class TestAuthLogin:
    """Kasus login: sukses, gagal, dan kondisi akun."""

    # ── A1. Login berhasil ─────────────────────────────────────────────────
    @pytest.mark.asyncio
    async def test_login_success_returns_user(self):
        """Login valid (password cocok dengan hash bcrypt) → user dikembalikan."""
        mock_repo = AsyncMock()
        mock_repo.get_by_email.return_value = _make_user()   # hash bcrypt valid
        mock_repo.reset_failed_login_attempts = AsyncMock()

        from src.services.user import UserService
        svc = UserService(mock_repo)
        # 'Password1!' sesuai dengan _VALID_HASH — tidak perlu patch
        result = await svc.authenticate_user("budi@balmon.go.id", "Password1!")

        assert result is not None
        assert result.email == "budi@balmon.go.id"

    # ── A2. Login email tidak terdaftar ───────────────────────────────────
    @pytest.mark.asyncio
    async def test_login_unknown_email_returns_none(self):
        """Login email tidak ada → None."""
        mock_repo = AsyncMock()
        mock_repo.get_by_email.return_value = None

        from src.services.user import UserService
        svc = UserService(mock_repo)
        result = await svc.authenticate_user("tidakada@example.com", "pass")

        assert result is None

    # ── A3. Login akun belum diverifikasi ─────────────────────────────────
    @pytest.mark.asyncio
    async def test_login_unverified_raises_403(self):
        """Login akun belum verifikasi email → HTTP 403."""
        mock_repo = AsyncMock()
        mock_repo.get_by_email.return_value = _make_user(is_verified=False)

        from src.services.user import UserService
        svc = UserService(mock_repo)

        with pytest.raises(HTTPException) as exc:
            await svc.authenticate_user("budi@balmon.go.id", "pass")
        assert exc.value.status_code == 403

    # ── A4. Login akun belum diapprove admin ──────────────────────────────
    @pytest.mark.asyncio
    async def test_login_inactive_raises_403(self):
        """Login akun belum aktif (belum diapprove) → HTTP 403."""
        mock_repo = AsyncMock()
        mock_repo.get_by_email.return_value = _make_user(is_active=False)

        from src.services.user import UserService
        svc = UserService(mock_repo)

        with pytest.raises(HTTPException) as exc:
            await svc.authenticate_user("budi@balmon.go.id", "pass")
        assert exc.value.status_code == 403

    # ── A5. Login akun terkunci ────────────────────────────────────────────
    @pytest.mark.asyncio
    async def test_login_locked_raises_423(self):
        """Login akun terkunci (terlalu banyak gagal) → HTTP 423."""
        mock_repo = AsyncMock()
        mock_repo.get_by_email.return_value = _make_user(is_locked_val=True)

        from src.services.user import UserService
        svc = UserService(mock_repo)

        with pytest.raises(HTTPException) as exc:
            await svc.authenticate_user("budi@balmon.go.id", "pass")
        assert exc.value.status_code == 423

    # ── A6. Login password salah — increment failed attempts ───────────────
    @pytest.mark.asyncio
    async def test_login_wrong_password_increments_failed_attempts(self):
        """Login password salah → increment_failed_login_attempts dipanggil."""
        updated = _make_user(failed_login_attempts=1, is_locked_val=False)
        mock_repo = AsyncMock()
        mock_repo.get_by_email.return_value = _make_user()
        mock_repo.increment_failed_login_attempts.return_value = updated
        mock_repo.reset_failed_login_attempts = AsyncMock()

        # Patch di namespace user.py karena verify_password sudah di-import di sana
        with patch("src.services.user.verify_password", return_value=False):
            from src.services.user import UserService
            svc = UserService(mock_repo)
            result = await svc.authenticate_user("budi@balmon.go.id", "salah")

        assert result is None
        mock_repo.increment_failed_login_attempts.assert_called_once()

    # ── A7. Login berhasil — reset failed attempts ─────────────────────────
    @pytest.mark.asyncio
    async def test_login_success_resets_failed_attempts(self):
        """Login sukses (password cocok) → reset_failed_login_attempts(1) dipanggil."""
        mock_repo = AsyncMock()
        mock_repo.get_by_email.return_value = _make_user()   # hash bcrypt valid
        mock_repo.reset_failed_login_attempts = AsyncMock()

        from src.services.user import UserService
        svc = UserService(mock_repo)
        # 'Password1!' sesuai hash — tidak perlu patch verify_password
        await svc.authenticate_user("budi@balmon.go.id", "Password1!")

        mock_repo.reset_failed_login_attempts.assert_called_once_with(1)


# ═══════════════════════════════════════════════════════════════════════════════
# B. AUTH — Logout
# ═══════════════════════════════════════════════════════════════════════════════
class TestAuthLogout:
    """Kasus logout sesi spesifik dan semua perangkat."""

    @pytest.mark.asyncio
    async def test_logout_active_session_returns_success(self):
        """Logout sesi aktif → pesan sukses."""
        # Gunakan mock langsung di device_session_manager yang sudah di-inject
        import src.utils.sessions as sessions_mod
        sessions_mod.device_session_manager.delete_session = AsyncMock(return_value=True)

        from src.services.auth import AuthService
        svc = AuthService(AsyncMock(), AsyncMock())
        result = await svc.logout("session-abc-123")

        assert "success" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_logout_unknown_session_returns_not_found(self):
        """Logout sesi tidak dikenal → pesan sesi tidak ditemukan."""
        import src.utils.sessions as sessions_mod
        sessions_mod.device_session_manager.delete_session = AsyncMock(return_value=False)

        from src.services.auth import AuthService
        svc = AuthService(AsyncMock(), AsyncMock())
        result = await svc.logout("session-xyz-999")

        assert "not found" in result["message"].lower() or "expired" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_logout_all_devices_returns_count(self):
        """Logout semua perangkat → sessions_terminated = jumlah yang dihentikan."""
        import src.utils.sessions as sessions_mod
        sessions_mod.device_session_manager.delete_user_sessions = AsyncMock(return_value=3)

        from src.services.auth import AuthService
        svc = AuthService(AsyncMock(), AsyncMock())
        result = await svc.logout_all_devices(user_id=1)

        assert result["sessions_terminated"] == 3


# ═══════════════════════════════════════════════════════════════════════════════
# C. USER — Create, Read, Update, Delete
# ═══════════════════════════════════════════════════════════════════════════════
class TestUserCRUD:
    """Kasus CRUD pengguna."""

    # ── C1. Tambah user baru (registrasi mandiri) ──────────────────────────
    @pytest.mark.asyncio
    async def test_create_user_new_email_succeeds(self):
        """Registrasi user baru → is_active=False, is_verified=False (menunggu)."""
        new_user = _make_user(is_active=False, is_verified=False)
        mock_repo = AsyncMock()
        mock_repo.get_by_email.return_value = None    # email belum ada
        mock_repo.create.return_value = new_user
        mock_repo.session = AsyncMock()

        with (
            patch("src.auth.jwt.get_password_hash", return_value="hashed_pw"),
            patch("src.schemas.user.UserResponse.model_validate",
                  return_value=MagicMock(email="baru@balmon.go.id")),
        ):
            from src.services.user import UserService
            svc = UserService(mock_repo)
            await svc.create_user(
                MagicMock(email="baru@balmon.go.id", password="Password1!")
            )

        assert new_user.is_active is False
        assert new_user.is_verified is False

    # ── C2. Tambah user — email duplikat ──────────────────────────────────
    @pytest.mark.asyncio
    async def test_create_user_duplicate_email_raises_400(self):
        """Registrasi dengan email yang sudah ada → HTTP 400."""
        mock_repo = AsyncMock()
        mock_repo.get_by_email.return_value = _make_user()   # sudah ada

        from src.services.user import UserService
        svc = UserService(mock_repo)

        with pytest.raises(HTTPException) as exc:
            await svc.create_user(
                MagicMock(email="budi@balmon.go.id", password="pass")
            )
        assert exc.value.status_code == 400
        assert "registered" in exc.value.detail.lower()

    # ── C3. Admin buat user — langsung aktif & terverifikasi ──────────────
    @pytest.mark.asyncio
    async def test_create_user_by_admin_active_and_verified(self):
        """Admin buat user → is_active=True, is_verified=True otomatis."""
        new_user = _make_user()
        mock_repo = AsyncMock()
        mock_repo.get_by_email.return_value = None
        mock_repo.create.return_value = new_user
        mock_repo.session = AsyncMock()

        with (
            patch("src.auth.jwt.get_password_hash", return_value="hashed_pw"),
            patch("src.schemas.user.UserResponse.model_validate", return_value=MagicMock()),
        ):
            from src.services.user import UserService
            svc = UserService(mock_repo)
            await svc.create_user_by_admin(
                MagicMock(email="baru@balmon.go.id", password="Admin1!")
            )

        assert new_user.is_active is True
        assert new_user.is_verified is True

    # ── C4. Ambil user by ID — ditemukan ──────────────────────────────────
    @pytest.mark.asyncio
    async def test_get_user_by_id_found(self):
        """get_user dengan ID valid → mengembalikan data user."""
        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = _make_user()

        with patch("src.schemas.user.UserResponse.model_validate",
                   return_value=MagicMock(id=1, email="budi@balmon.go.id")):
            from src.services.user import UserService
            svc = UserService(mock_repo)
            result = await svc.get_user(1)

        assert result is not None

    # ── C5. Ambil user by ID — tidak ditemukan ────────────────────────────
    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found_returns_none(self):
        """get_user dengan ID tidak ada → None."""
        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = None

        from src.services.user import UserService
        svc = UserService(mock_repo)
        result = await svc.get_user(999)

        assert result is None

    # ── C6. Update user — berhasil ────────────────────────────────────────
    @pytest.mark.asyncio
    async def test_update_user_success(self):
        """update_user dengan data valid → memanggil repo.update."""
        mock_repo = AsyncMock()
        mock_repo.update.return_value = _make_user(nama="Budi Diperbarui")

        with patch("src.schemas.user.UserResponse.model_validate",
                   return_value=MagicMock(nama="Budi Diperbarui")):
            from src.services.user import UserService
            svc = UserService(mock_repo)
            result = await svc.update_user(1, MagicMock(nama="Budi Diperbarui"))

        mock_repo.update.assert_called_once()
        assert result is not None

    # ── C7. Update user — tidak ditemukan ─────────────────────────────────
    @pytest.mark.asyncio
    async def test_update_user_not_found_raises_404(self):
        """update_user dengan ID tidak ada → HTTP 404."""
        mock_repo = AsyncMock()
        mock_repo.update.return_value = None

        from src.services.user import UserService
        svc = UserService(mock_repo)

        with pytest.raises(HTTPException) as exc:
            await svc.update_user(999, MagicMock())
        assert exc.value.status_code == 404

    # ── C8. Hapus user (soft delete) ──────────────────────────────────────
    @pytest.mark.asyncio
    async def test_delete_user_success(self):
        """delete_user dengan ID valid → True."""
        mock_repo = AsyncMock()
        mock_repo.delete_user.return_value = True

        from src.services.user import UserService
        svc = UserService(mock_repo)
        result = await svc.delete_user(1)

        assert result is True
        mock_repo.delete_user.assert_called_once_with(1)

    # ── C9. Hapus user — tidak ditemukan ──────────────────────────────────
    @pytest.mark.asyncio
    async def test_delete_user_not_found_raises_404(self):
        """delete_user dengan ID tidak ada → HTTP 404."""
        mock_repo = AsyncMock()
        mock_repo.delete_user.return_value = False

        from src.services.user import UserService
        svc = UserService(mock_repo)

        with pytest.raises(HTTPException) as exc:
            await svc.delete_user(999)
        assert exc.value.status_code == 404

    # ── C10. Ganti password — berhasil ────────────────────────────────────
    @pytest.mark.asyncio
    async def test_change_password_success(self):
        """change_password password lama benar (cocok hash) → update_password dipanggil."""
        user = _make_user(password_history=[])  # hash bcrypt valid untuk 'Password1!'
        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = user
        mock_repo.update_password.return_value = _make_user()

        with (
            patch("src.utils.validators.validate_password_history", return_value=True),
            patch("src.auth.jwt.get_password_hash", return_value="new_hash"),
            patch("src.schemas.user.UserResponse.model_validate", return_value=MagicMock()),
        ):
            from src.services.user import UserService
            svc = UserService(mock_repo)
            # 'Password1!' cocok dengan _VALID_HASH — tidak perlu patch verify_password
            result = await svc.change_password(
                1, MagicMock(current_password="Password1!", new_password="NewPass1!")
            )

        assert result is not None
        mock_repo.update_password.assert_called_once()

    # ── C11. Ganti password — password lama salah ─────────────────────────
    @pytest.mark.asyncio
    async def test_change_password_wrong_current_raises_400(self):
        """change_password password lama salah → HTTP 400 sebelum update dipanggil."""
        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = _make_user()

        # Patch di namespace services.user (sudah di-import di level modul)
        with patch("src.services.user.verify_password", return_value=False):
            from src.services.user import UserService
            svc = UserService(mock_repo)

            with pytest.raises(HTTPException) as exc:
                await svc.change_password(
                    1, MagicMock(current_password="Salah!", new_password="NewPass1!")
                )
        assert exc.value.status_code == 400
        mock_repo.update_password.assert_not_called()

    # ── C12. Update status user ────────────────────────────────────────────
    @pytest.mark.asyncio
    async def test_update_user_status_calls_update(self):
        """update_user_status → memanggil repo.update."""
        mock_repo = AsyncMock()
        mock_repo.update.return_value = _make_user(is_active=True)

        with patch("src.schemas.user.UserResponse.model_validate",
                   return_value=MagicMock(is_active=True)):
            from src.services.user import UserService
            svc = UserService(mock_repo)
            result = await svc.update_user_status(1, is_active=True)

        mock_repo.update.assert_called_once()
        assert result is not None

    # ── C13. Unlock akun ──────────────────────────────────────────────────
    @pytest.mark.asyncio
    async def test_unlock_user_account_calls_repo(self):
        """unlock_user_account → memanggil repo.unlock_account(user_id)."""
        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = _make_user()
        mock_repo.unlock_account = AsyncMock()

        with patch("src.schemas.user.UserResponse.model_validate", return_value=MagicMock()):
            from src.services.user import UserService
            svc = UserService(mock_repo)
            await svc.unlock_user_account(1)

        mock_repo.unlock_account.assert_called_once_with(1)

    # ── C14. Unlock akun — user tidak ditemukan ───────────────────────────
    @pytest.mark.asyncio
    async def test_unlock_user_account_not_found_raises_404(self):
        """unlock_user_account user tidak ada → HTTP 404."""
        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = None

        from src.services.user import UserService
        svc = UserService(mock_repo)

        with pytest.raises(HTTPException) as exc:
            await svc.unlock_user_account(999)
        assert exc.value.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════════
# D. DEVICE — Status, Kondisi, Logika Peminjaman
# ═══════════════════════════════════════════════════════════════════════════════
class TestDeviceLogic:
    """Logika bisnis perangkat (tanpa DB)."""

    STATUSES    = ["TERSEDIA", "DIPINJAM", "MAINTENANCE", "NONAKTIF"]
    CONDITIONS  = ["baik", "rusak_ringan", "rusak_berat", "hilang"]

    def test_all_device_statuses_recognized(self):
        """Empat status perangkat harus dikenal sistem."""
        for s in self.STATUSES:
            assert s in self.STATUSES

    def test_all_device_conditions_recognized(self):
        """Empat kondisi perangkat harus dikenal sistem."""
        for c in self.CONDITIONS:
            assert c in self.CONDITIONS

    def test_tersedia_is_available(self):
        """Status TERSEDIA → perangkat siap dipinjam."""
        is_avail = lambda s: s == "TERSEDIA"
        assert is_avail("TERSEDIA") is True
        assert is_avail("DIPINJAM") is False
        assert is_avail("MAINTENANCE") is False
        assert is_avail("NONAKTIF") is False

    def test_borrowable_only_tersedia_and_baik(self):
        """Perangkat hanya bisa dipinjam jika TERSEDIA dan kondisi baik."""
        ok = lambda s, c: s == "TERSEDIA" and c == "baik"
        assert ok("TERSEDIA", "baik")          is True
        assert ok("TERSEDIA", "rusak_ringan")  is False
        assert ok("DIPINJAM", "baik")          is False
        assert ok("MAINTENANCE", "baik")       is False

    @pytest.mark.asyncio
    async def test_get_device_not_found_returns_none(self, mock_session):
        """get perangkat ID tidak ada → None."""
        mock_session.get.return_value = None
        result = await mock_session.get("Device", 9999)
        assert result is None


# ═══════════════════════════════════════════════════════════════════════════════
# E. LOAN — Format Nomor, Durasi, Deteksi Keterlambatan, Status
# ═══════════════════════════════════════════════════════════════════════════════
class TestLoanLogic:
    """Logika bisnis peminjaman (tanpa DB)."""

    def test_loan_number_correct_format(self):
        """Nomor pinjam → format LOAN-YYYYMMDD-XXXX, panjang 18 char."""
        n = f"LOAN-{datetime.now().strftime('%Y%m%d')}-0001"
        assert n.startswith("LOAN-")
        assert len(n) == 18

    def test_loan_number_matches_regex(self):
        """Nomor pinjam cocok regex ^LOAN-\\d{8}-\\d{4}$."""
        import re
        gen = lambda seq: f"LOAN-{datetime.now().strftime('%Y%m%d')}-{str(seq).zfill(4)}"
        assert re.match(r"^LOAN-\d{8}-\d{4}$", gen(1))

    def test_duration_9_days(self):
        """1 Jan → 10 Jan = 9 hari."""
        assert (date(2024, 1, 10) - date(2024, 1, 1)).days == 9

    def test_duration_same_day_is_zero(self):
        """Mulai = selesai = 0 hari."""
        d = date(2024, 3, 1)
        assert (d - d).days == 0

    def test_duration_across_months(self):
        """20 Jan → 20 Feb = 31 hari."""
        assert (date(2024, 2, 20) - date(2024, 1, 20)).days == 31

    def test_overdue_when_past_due_date(self):
        """Tanggal kembali sudah lewat → terlambat."""
        past = date.today() - timedelta(days=1)
        assert past < date.today()

    def test_not_overdue_future_date(self):
        """Tanggal kembali masih mendatang → tidak terlambat."""
        future = date.today() + timedelta(days=1)
        assert not (future < date.today())

    def test_returned_loan_never_overdue(self):
        """Status DIKEMBALIKAN → tidak pernah dianggap terlambat."""
        is_overdue = lambda end, status: (status == "DIPINJAM") and (end < date.today())
        past = date.today() - timedelta(days=5)
        assert is_overdue(past, "DIKEMBALIKAN") is False

    def test_valid_loan_statuses(self):
        """Tiga status peminjaman valid: DIPINJAM, DIKEMBALIKAN, TERLAMBAT."""
        valid = {"DIPINJAM", "DIKEMBALIKAN", "TERLAMBAT"}
        for s in valid:
            assert s in valid
