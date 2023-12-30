import pytest
from selenium.common.exceptions import NoSuchElementException
from webdriver_browser import ChainWebAction, web_action


class UnknownException(Exception):
    pass


def test_chain_web_action(mocker):
    m1 = mocker.Mock()
    m1.return_value = True
    m2 = mocker.Mock()
    m2.side_effect = (NoSuchElementException(), NoSuchElementException(), NoSuchElementException(), True)
    m3 = mocker.Mock()
    m3.side_effect = UnknownException()
    with mocker.patch('time.sleep', return_value=None):
        chain1 = ChainWebAction(web_action(m1), web_action(m2), retry=3)
        assert chain1(None, retry=5) is True
        assert m1.call_count == 2
        assert m2.call_count == 4
        chain2 = ChainWebAction(web_action(m1), web_action(m3), retry=2)
        with pytest.raises(UnknownException):
            chain2(None, retry=3)
        assert m1.call_count == 3
        assert m3.call_count == 1
