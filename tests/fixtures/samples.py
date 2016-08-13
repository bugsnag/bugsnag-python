def call_bugsnag_nested():
    chain_2()


def chain_2():
    chain_3()


def chain_3():
    import bugsnag
    bugsnag.notify(Exception('oh noooo'))
