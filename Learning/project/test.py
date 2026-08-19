from utils.password import hash_password, verify_password

password = "secret123"

hashed = hash_password(password=password)
hashed2 = hash_password(password=password)


print("Original:", password)
print("Hash:", hashed)
print("Hash2:", hashed2)
print(hashed == hashed2)

print(verify_password(password=password, hashed_password=hashed))
print(verify_password(password="wrongsecret123", hashed_password=hashed))
