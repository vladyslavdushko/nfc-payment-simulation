from datetime import datetime, timedelta
import ipaddress
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa

# 1) Генеруємо ключ
key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

# 2) Сертифікат self-signed з CN=127.0.0.1 і SAN: 127.0.0.1, localhost
subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, u"127.0.0.1")])
alt_names = [x509.DNSName(u"localhost"), x509.IPAddress(ipaddress.IPv4Address("127.0.0.1"))]

cert = (
    x509.CertificateBuilder()
    .subject_name(subject)
    .issuer_name(issuer)
    .public_key(key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(datetime.utcnow())
    .not_valid_after(datetime.utcnow() + timedelta(days=365))
    .add_extension(x509.SubjectAlternativeName(alt_names), critical=False)
    .sign(key, hashes.SHA256())
)

# 3) Записуємо key.pem і cert.pem
with open("key.pem", "wb") as f:
    f.write(key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    ))

with open("cert.pem", "wb") as f:
    f.write(cert.public_bytes(serialization.Encoding.PEM))

print("Wrote key.pem and cert.pem")