
from passlib.context import CryptContext
import bcrypt

print(f"Bcrypt version: {getattr(bcrypt, '__version__', 'unknown')}")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
RAW_TEST_PASSWORD = "testpassword"
try:
    hashed = pwd_context.hash(RAW_TEST_PASSWORD)
    print(f"Hash successful: {hashed[:10]}...")
    verified = pwd_context.verify(RAW_TEST_PASSWORD, hashed)
    print(f"Verify successful: {verified}")
except Exception as e:
    print(f"Hashing failed: {e}")
