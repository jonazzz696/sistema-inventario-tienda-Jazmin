
import hashlib
import hmac
import secrets

ITERACIONES = 260_000


def generar_hash(password):
    
    sal = secrets.token_hex(16)  

    hash_bytes = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),  
        sal.encode("utf-8"),
        ITERACIONES,
    )
    hash_hex = hash_bytes.hex()

    return f"pbkdf2_sha256${ITERACIONES}${sal}${hash_hex}"


def verificar_password(password, hash_guardado):
    
    try:
        algoritmo, iteraciones_texto, sal, hash_esperado = hash_guardado.split("$")
    except ValueError:
        
        return False

    iteraciones = int(iteraciones_texto)

    hash_calculado = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        sal.encode("utf-8"),
        iteraciones,
    ).hex()

    return hmac.compare_digest(hash_calculado, hash_esperado)


if __name__ == "__main__":

    prueba_hash = generar_hash("MiClaveSegura123")
    print("Hash generado:", prueba_hash)

    print("Verificar con clave correcta:", verificar_password("MiClaveSegura123", prueba_hash))
    print("Verificar con clave incorrecta:", verificar_password("ClaveEquivocada", prueba_hash))
