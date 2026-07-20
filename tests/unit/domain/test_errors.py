from pydantic import HttpUrl

from joblytics.domain.exceptions.errors import DomainError, NoOffersFoundError


def test_no_offers_found_error_is_a_domain_error() -> None:
    error = NoOffersFoundError(
        title="Data Engineer",
        location="Paris",
        time_posted="day",
        work_modality="onsite",
    )
    assert isinstance(error, DomainError)
    assert isinstance(error, Exception)


def test_no_offers_found_error_message_without_url() -> None:
    error = NoOffersFoundError(
        title="Data Engineer",
        location="Paris",
        time_posted="day",
        work_modality="onsite",
    )
    message = str(error)
    assert 'title="Data Engineer"' in message
    assert 'location="Paris"' in message
    assert "time posted=day" in message
    assert "remote mode=onsite" in message
    assert "URL:" not in message


def test_no_offers_found_error_message_with_url() -> None:
    error = NoOffersFoundError(
        title="Data Engineer",
        location="Paris",
        time_posted="day",
        work_modality="onsite",
        url=HttpUrl("https://www.linkedin.com/jobs/search"),
    )
    assert "URL: https://www.linkedin.com/jobs/search" in str(error)


def test_no_offers_found_error_stores_attributes() -> None:
    error = NoOffersFoundError(
        title="Data Engineer",
        location="Paris",
        time_posted="day",
        work_modality="onsite",
    )
    assert error.title == "Data Engineer"
    assert error.location == "Paris"
    assert error.time_posted == "day"
    assert error.work_modality == "onsite"
    assert error.url is None
