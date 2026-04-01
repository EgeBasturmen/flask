from passlib.hash import sha256_crypt

# Şifrenizi hash'leyin
hashed_password = sha256_crypt.hash("admin123")
print(hashed_password)