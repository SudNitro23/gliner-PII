from __future__ import annotations

from collections.abc import Iterable


GLINER_TO_NITRO: dict[str, str] = {
    "person": "PERSON_NAME",
    "name": "PERSON_NAME",
    "full_name": "PERSON_NAME",
    "email": "EMAIL_ADDRESS",
    "email_address": "EMAIL_ADDRESS",
    "phone": "PHONE_NUMBER",
    "phone_number": "PHONE_NUMBER",
    "mobile_phone": "PHONE_NUMBER",
    "address": "POSTAL_ADDRESS",
    "street_address": "POSTAL_ADDRESS",
    "date_of_birth": "DATE_OF_BIRTH",
    "dob": "DATE_OF_BIRTH",
    "ssn": "NATIONAL_ID",
    "social_security_number": "NATIONAL_ID",
    "national_id": "NATIONAL_ID",
    "passport": "PASSPORT_NUMBER",
    "passport_number": "PASSPORT_NUMBER",
    "driver_license": "DRIVER_LICENSE",
    "drivers_license": "DRIVER_LICENSE",
    "credit_card": "PAYMENT_CARD",
    "credit_card_number": "PAYMENT_CARD",
    "account_number": "ACCOUNT_NUMBER",
    "bank_account": "ACCOUNT_NUMBER",
    "ip": "IP_ADDRESS",
    "ip_address": "IP_ADDRESS",
    "url": "URL",
    "username": "USERNAME",
    "organization": "ORGANIZATION",
    "company": "ORGANIZATION",
    "location": "LOCATION",
}

NITRO_LABELS: tuple[str, ...] = tuple(sorted(set(GLINER_TO_NITRO.values())))


def normalize_label(label: str) -> str:
    return label.strip().lower().replace(" ", "_").replace("-", "_")


def map_to_nitro(label: str) -> str:
    normalized = normalize_label(label)
    if normalized.upper() in NITRO_LABELS:
        return normalized.upper()
    return GLINER_TO_NITRO.get(normalized, normalized.upper() or "OTHER_PII")


def model_labels() -> list[str]:
    return sorted(GLINER_TO_NITRO.keys())


def unique_taxonomy_labels(labels: Iterable[str]) -> list[str]:
    return sorted({map_to_nitro(label) for label in labels})

