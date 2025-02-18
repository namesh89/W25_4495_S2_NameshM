import bcrypt

# Generate a bcrypt hash for a given password
def hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

# Verify a password against a stored hash
def verify_password(stored_password, provided_password):
    return bcrypt.checkpw(provided_password.encode("utf-8"), stored_password.encode("utf-8"))