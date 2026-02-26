import asyncio
from typing import AsyncIterator


def play_dict():
    adict = {"book": "man", "type": "read"}
    bdict = {1: 100, "2": 3000}

    print(f"bdict looks like:{bdict.items()}")

    adict.update({str(k): str(v) for k, v in bdict.items()})
    print(adict)

    print("----")
    print("if you dont't need to transformat the type of result, just use")
    # adict.update({k: v for k, v in bdict.items()}) equals
    adict.update(bdict)
    print(adict)


def play_hasattr():
    class Coordinate:
        x = 10
        y = -5
        z = 0

    point1 = Coordinate()
    print(hasattr(point1, 'x'))
    print(hasattr(point1, 'y'))
    print(hasattr(point1, 'z'))
    print(hasattr(point1, 'no'))


# 异步生成器async def不能带值 return
def play_async_yield(numlist: list):
    for n in numlist:
        if n == 3:
            yield numlist[len(numlist) - n]
    yield {"Hello": "World"}


if __name__ == '__main__':
    nums = [1, 2, 3, 4, 5]
    # play_dict()
    # play_hasattr()
    data = tuple(play_async_yield(nums))
    print(data)
