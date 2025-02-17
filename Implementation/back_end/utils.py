import bcrypt

def hash_password(password):
    """Generate a bcrypt hash for a given password."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(stored_password, provided_password):
    """Verify a password against a stored hash."""
    return bcrypt.checkpw(provided_password.encode("utf-8"), stored_password.encode("utf-8"))