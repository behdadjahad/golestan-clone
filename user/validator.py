from django.core.exceptions import ValidationError

def validate_password_length(value):
    if len(value) < 8:
        raise ValidationError("Password must contain at least 8 characters.")