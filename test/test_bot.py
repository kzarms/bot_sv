import src.bot as test_module


def test_get_tocken():
    # Test preparation
    expected_result = ""
    # Test execution
    result = test_module.get_tocken()
    # Test validation
    assert expected_result in result
