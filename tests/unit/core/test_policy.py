from joblytics.core.config.policy import HttpPolicy, PolicyResolver


def test_for_provider_returns_default_when_no_override() -> None:
    default = HttpPolicy(max_retries=3)
    resolver = PolicyResolver(default=default)

    assert resolver.for_provider("unknown") == default


def test_for_provider_merges_override_onto_default() -> None:
    default = HttpPolicy(max_retries=3, timeout_connect=5.0)
    override = HttpPolicy(max_retries=1)
    resolver = PolicyResolver(default=default, per_provider={"linkedin": override})

    resolved = resolver.for_provider("linkedin")

    assert resolved.max_retries == 1
    assert resolved.timeout_connect == 5.0
