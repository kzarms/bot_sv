from unittest.mock import Mock, patch

import src.bot as test_module

test_module.save_to_local = Mock(return_value=None)


def test_get_tocken():
    # Test preparation
    expected_result = ""
    # Test execution
    result = test_module.get_tocken()
    # Test validation
    assert expected_result in result


class TestAddSvSession:

    def test_add_session_simple(self):
        # Test preparation
        test_module.SUPERVISORS = {
            "111": {"FullName": "aaa", "Sessions": 0, "Total": 0},
            "222": {"FullName": "bbb", "Sessions": 2, "Total": 0},
        }
        expected_result = 1
        # Test execution
        test_module.add_sv_session("111")
        # Test validation
        assert expected_result == test_module.SUPERVISORS["111"]["Sessions"]
        assert expected_result == test_module.SUPERVISORS["111"]["Total"]

    def test_add_session_reset(self):
        # Test preparation
        expected_result = 0
        test_module.SUPERVISORS["222"]["Sessions"] = 2
        # Test execution
        test_module.add_sv_session("222")
        # Test validation
        assert expected_result == test_module.SUPERVISORS["222"]["Sessions"]


class TestSvRequests:

    def test_add_sv_request(self):
        test_module.SUPERVISORS = {
            "111": {
                "FullName": "aaa",
                "Sessions": 0,
                "Requests": [{"id": "888", "FullName": "User888"}],
            },
            "222": {
                "FullName": "bbb",
                "Sessions": 1,
                "Requests": [{"id": "777", "FullName": "User777"}],
            },
        }
        test_module.SUPERVISORS_QEUE = ["111", "222"]
        # Test preparation
        expected_result = True
        expected_update = 2
        # Test execution
        result = test_module.add_sv_request("111", "999", "User999")
        # Test validation
        assert expected_result == result
        assert expected_update == len(test_module.SUPERVISORS["111"]["Requests"])

    def test_decline_sv_request(self):
        # Test preparation
        expected_result = [{"id": "777", "FullName": "User777"}]
        expected_update = 0
        # Test execution
        result = test_module.decline_sv_requests("222")
        # Test validation
        assert expected_result == result
        assert expected_update == len(test_module.SUPERVISORS["222"]["Requests"])

    def test_del_sv_request(self):
        # Test preparation
        expected_result = True
        expected_update = 1
        # Test execution
        result = test_module.del_sv_request("111", "999")
        # Test validation
        assert expected_result == result
        assert expected_update == len(test_module.SUPERVISORS["111"]["Requests"])


class TestCreateSVListFromDB:

    def test_create_sv_list_from_db(self):
        # Test preparation
        expected_result = ["111", "222"]
        test_module.SUPERVISORS = {
            "111": {"FullName": "aaa", "Sessions": 0},
            "222": {"FullName": "bbb", "Sessions": 1},
        }
        test_module.SUPERVISORS_QEUE = []
        # Test execution
        print(test_module.SUPERVISORS)
        print(test_module.SUPERVISORS_QEUE)
        result = test_module.create_sv_list_from_db()
        # Test validation
        assert expected_result == result


def tearDown():
    # Stop patching after each test method
    patcher.stop()
