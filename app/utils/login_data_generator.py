import random
import string


async def generate_3proxy_credentials() -> dict:
    safe_chars = (
            string.ascii_letters +  # A-Z, a-z
            string.digits +  # 0-9
            "_-!@#$%^&*()+={}|',.?/~"
    )

    login = random.choice(string.ascii_letters)
    login += ''.join(random.choice(string.ascii_letters + string.digits + '_-.')
                     for _ in range(13))

    password = ''.join(random.choice(safe_chars) for _ in range(13))

    return {
        'login': login,
        'password': password
    }