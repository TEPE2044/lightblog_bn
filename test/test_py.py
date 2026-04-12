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


def play_dynamic_list():
    num = 1
    f = [num == 2, "helloworld"]
    print(type(f))
    f.append(num == 3)
    print(f)


# 原理：字典的键天然唯一
# dict.fromkeys(['a', 'b', 'a', 'c'])
# # → {'a': None, 'b': None, 'c': None}  重复的'a'被自动去重
#
# # 再转回列表
# list(dict.fromkeys(['a', 'b', 'a', 'c']))
# → ['a', 'b', 'c']

def cut_diff():
    # 优雅去重，不丢排序
    man = list(dict.fromkeys('tags', 'hei'))
    print(man)


def identify_type():
    is_the_same = isinstance('man', int)
    print(f"same type? : {is_the_same}")


if __name__ == '__main__':
    play_dynamic_list()
    identify_type()
    # nums = [1, 2, 3, 4, 5]
    # play_dict()
    # play_hasattr()
    # data = tuple(play_async_yield(nums))
    # print(data)
