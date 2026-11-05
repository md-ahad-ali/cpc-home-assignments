"""
Subsystem 1: User & Building Management (FR1.1 - FR1.10)
Owner: Thi Ha Vu
"""

import hashlib
import os


class User:
    VALID_ROLES = ("Admin", "Manager", "Occupant")

    def __init__(self, user_id, username, password, role="Occupant"):
        self._id = user_id
        self._username = ""
        self._password_hash = ""
        self._role = "Occupant"
        self._logged_in = False
        self._failed_logins = 0
        self.initialize()
        self.set_username(username)
        self.set_password(password)
        self.set_role(role)

    def initialize(self):
        self._logged_in = False
        self._failed_logins = 0

    # ---- getters ----
    def get_id(self):
        return self._id

    def get_username(self):
        return self._username

    def get_password_hash(self):
        return self._password_hash

    def get_role(self):
        return self._role

    def is_logged_in(self):
        return self._logged_in

    # ---- setters ----
    def set_username(self, username):
        if not username or not username.strip():
            raise ValueError("username must not be empty")
        self._username = username.strip()

    def set_password(self, password):
        if len(password) < 8:
            raise ValueError("password needs at least 8 characters")
        salt = os.urandom(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)
        self._password_hash = salt.hex() + ":" + digest.hex()

    def set_role(self, role):
        if role not in User.VALID_ROLES:
            raise ValueError("role must be one of " + str(User.VALID_ROLES))
        self._role = role

    # ---- behavior ----
    def check_password(self, password):
        salt_hex, digest_hex = self._password_hash.split(":")
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt_hex), 100000
        )
        return digest.hex() == digest_hex

    def register(self, existing_users):
        """FR1.1: the username must be unique."""
        for other in existing_users:
            if other.get_username().lower() == self._username.lower():
                raise ValueError("username already exists")
        existing_users.append(self)

    def login(self, password):
        """FR1.2: return True if the password is right."""
        if self.check_password(password):
            self._logged_in = True
            self._failed_logins = 0
            return True
        self._failed_logins += 1
        return False

    def logout(self):
        self._logged_in = False

    def can_manage_buildings(self):
        """FR1.6: only Admin and Manager can change buildings."""
        return self._role in ("Admin", "Manager")
