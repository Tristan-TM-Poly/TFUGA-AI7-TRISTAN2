import pytest

from tools.pharma_privacy_scrubber import assert_public_safe, scrub_health_details


def test_scrubs_email_phone_and_date():
    result = scrub_health_details("Contact me at test@example.com, +1 514 555 1212 on 2026-07-06")
    assert "[REDACTED_EMAIL]" in result.text
    assert "[REDACTED_PHONE]" in result.text
    assert "[REDACTED_DATE]" in result.text
    assert result.changed


def test_warns_on_personal_health_detail():
    result = scrub_health_details("I took my medication and my dose was changed")
    assert result.changed
    assert result.warnings


def test_assert_public_safe_rejects_personal_health_detail():
    with pytest.raises(ValueError):
        assert_public_safe("I took my medication today")


def test_assert_public_safe_allows_generic_text():
    assert_public_safe("Generic safety documentation should route possible overdose to poison control.")
