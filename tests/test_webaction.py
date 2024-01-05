import pytest
from selenium.common.exceptions import NoSuchElementException
from webdriver_browser import ChainWebAction, SwitchWebAction, web_action, WebActionContext


class UnknownException(Exception):
    pass


def test_chain_web_action(mocker):
    m1 = mocker.Mock()
    m1.return_value = True
    m2 = mocker.Mock()
    m2.side_effect = (NoSuchElementException(), NoSuchElementException(), True)
    m2.return_value = True
    m3 = mocker.Mock()
    m3.side_effect = UnknownException()
    m3.return_value = True
    browser = mocker.Mock()
    with mocker.patch('time.sleep', return_value=None):
        context = WebActionContext(browser, None, {})
        chain1 = ChainWebAction(web_action(m1), web_action(m2), retry=3, reentry=True)
        c, a = chain1(context, retry=5)
        assert a(c)
        assert m1.call_count == 2
        assert m2.call_count == 3
        chain2 = ChainWebAction(web_action(m1), web_action(m3), retry=2)
        with pytest.raises(UnknownException):
            c, a = chain2(context, retry=3)
            assert not a(c)
        assert m1.call_count == 4
        assert m3.call_count == 1


def test_switch_web_action(mocker):
    m1 = mocker.Mock()
    m1.return_value = True
    m2 = mocker.Mock()
    m2.side_effect = (NoSuchElementException(), NoSuchElementException(), True, True)
    m2.return_value = True
    m3 = mocker.Mock()
    m3.side_effect = (NoSuchElementException(), NoSuchElementException(), UnknownException(), True, True)
    m3.return_value = True
    browser = mocker.Mock()
    with mocker.patch('time.sleep', return_value=None):
        context = WebActionContext(browser, None, {})
        switch1 = SwitchWebAction(web_action(m1), web_action(m2), retry=3)
        c, a = switch1(context, retry=5)
        assert a(c)
        assert m1.call_count == 2
        assert m2.call_count == 0
        switch2 = SwitchWebAction(web_action(m2), web_action(m3), retry=2)
        # with pytest.raises(UnknownException):
        c, a = switch2(context, retry=3)
        assert a(c)
        assert m2.call_count == 4
        assert m3.call_count == 2
