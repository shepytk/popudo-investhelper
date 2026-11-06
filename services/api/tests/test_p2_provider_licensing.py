import pytest
from fastapi import HTTPException

from app.licensing import PublicDataPolicy


def test_production_denies_sources_without_explicit_licence_approval():
    policy = PublicDataPolicy.from_configuration("production", "")
    assert policy.production
    assert not policy.is_permitted("sec_edgar")
    with pytest.raises(HTTPException) as err:
        policy.require_all(["sec_edgar"])
    assert err.value.status_code == 403
    assert err.value.detail["code"] == "provider_license_restricted"


def test_approval_is_provider_specific_and_rejects_mixed_sources():
    policy = PublicDataPolicy.from_configuration("production", "sec_edgar,ecb_fx")
    policy.require_all(["sec_edgar", "ecb_fx"])
    with pytest.raises(HTTPException):
        policy.require_all(["sec_edgar", "unlicensed_vendor"])
    with pytest.raises(HTTPException):
        policy.require_all(["sec_edgar", None])


@pytest.mark.parametrize("configured", ["*", "sec_edgar,*", "sec edgar", "sec_edgar;other"])
def test_wildcards_and_malformed_allowlists_fail_closed(configured):
    policy = PublicDataPolicy.from_configuration("production", configured)
    assert not policy.is_permitted("sec_edgar")


def test_development_and_test_do_not_require_production_licences():
    for env in ("development", "test"):
        policy = PublicDataPolicy.from_configuration(env, "")
        policy.require_all(["unlicensed_vendor", None])
        assert not policy.production


def test_provider_names_are_normalized_without_wildcard():
    policy = PublicDataPolicy.from_configuration("production", " SEC_EDGAR ")
    assert policy.is_permitted("sec_edgar")
    assert not policy.is_permitted("sec_edgar_test")
