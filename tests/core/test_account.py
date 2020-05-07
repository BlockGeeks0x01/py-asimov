from asimov import AccountFactory


def test_new_account():
    AccountFactory.new()


def test_new_address():
    assert AccountFactory.generate_address(
        "bba692e559fda550d0157669b101bafddb23e7f57aeeb5cef5494e7a41a1f056") == "66c17b951f0c85b860c9f7f0d811c77ea78f2d2e3a"


def test_private2public():
    assert AccountFactory.private2public("0xbba692e559fda550d0157669b101bafddb23e7f57aeeb5cef5494e7a41a1f056") == b'043a68576342553357f042c6ede12bd3ed01cb61ad39848908883cab93f66c76016fb60b2b472d6caf316c699cb38f61d5daef3792402461ddc449a18b0fc8ee32'

