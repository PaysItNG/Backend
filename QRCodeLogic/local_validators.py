import re

def validate_number(number):# validate a phone number
    regex = r'^\+?\d{8,15}$'  # Allows optional '+' and 8-15 digits
    if not re.match(regex, number):
        raise ValueError("Invalid phone number")
    return number

def validate_email(email):# validate an email.
    regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if not re.match(regex, email):
        raise ValueError("Invalid email address")
    return email

def validate_text(text):
    """
    Validates a text field for alphanumeric characters, spaces, and basic punctuation.
    """
    regex = r'^[a-zA-Z0-9\s.,!?\-()]+$'
    if not re.match(regex, text):
        raise ValueError("Invalid characters in text field")
    return text

def validate_password(password):
    """
    Validates a password for security requirements.
    """
    if len(password) < 6:
        raise ValueError("Password must be at least 8 characters long")
    if not re.search(r'[A-Z]', password):
        raise ValueError("Password must contain at least one uppercase letter")
    # if not re.search(r'[a-z]', password):
    #     raise ValueError("Password must contain at least one lowercase letter")
    if not re.search(r'[0-9]', password):
        raise ValueError("Password must contain at least one digit")
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise ValueError("Password must contain at least one special character")
    return password

def validate_file_extension(filename, allowed_extensions):
    """
    Validates a file extension against a list of allowed extensions.
    """
    if not any(filename.lower().endswith(ext) for ext in allowed_extensions):
        raise ValueError(f"Invalid file extension. Allowed extensions: {', '.join(allowed_extensions)}")
    return filename

def validate_amount(amount):
    """
    Validates a monetary amount (positive number with up to 2 decimal places).
    """
    regex = r'^\d+(\.\d{1,2})?$'
    if not re.match(regex, str(amount)):
        raise ValueError("Invalid amount. Must be a positive number with up to 2 decimal places")
    return float(amount)
