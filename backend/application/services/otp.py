import random
import redis
import hashlib

from ...tasks.send_email import send_otp_email


class OTPService:
    def __init__(self, redis_client=None, expiry=300):
        self.r = redis_client or redis.Redis(
            host="localhost",
            port=6379,
            db=1,
            decode_responses=True
        )
        self.expiry = expiry  # OTP expiry (5 min)

    # -----------------------
    # Keys
    # -----------------------

    def _otp_key(self, email):
        return f"otp:{email}"

    # -----------------------
    # Helpers
    # -----------------------

    def _hash(self, otp):
        return hashlib.sha256(otp.encode()).hexdigest()

    def generate(self):
        return str(random.randint(100000, 999999))

    # -----------------------
    # OTP operations
    # -----------------------

    def set(self, email):
        otp = self.generate()
        hashed = self._hash(otp)

        self.r.set(self._otp_key(email), hashed, ex=self.expiry)

        return otp  # raw OTP for sending

    def verify(self, email, otp):
        stored = self.r.get(self._otp_key(email))

        if not stored:
            return False

        if stored != self._hash(otp):
            return False

        # single-use OTP
        self.delete(email)

        return True

    def delete(self, email):
        self.r.delete(self._otp_key(email))

    def send(self, email):
        otp = self.set(email)

        # Prefer async email via Celery, but fall back to inline execution
        # when broker/worker dispatch is unavailable.
        try:
            send_otp_email.delay(email, otp)
        except Exception:
            send_otp_email.apply(args=[email, otp])

        return otp  # for debugging only

class OTP:
    def __init__(self, email, service: OTPService):
        self.email = email
        self.service = service

    # send OTP
    def send(self):
        return self.service.send(self.email)

    # verify OTP
    def verify(self, otp):
        return self.service.verify(self.email, otp)