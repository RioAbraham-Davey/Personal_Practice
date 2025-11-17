def decorator_ignore_if_held(func):
    def wrapper(var):
        try:
            func(var)
        except Exception as e:
            print(f'handle exception {e}')

    return wrapper

# @decorator_ignore_if_held
def test(foo:str):
    print('hi' + foo)


test("str")