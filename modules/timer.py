import time
import random


class Timer:
    __slots__ = ("begin", "_time")

    def __init__(self):
        self.begin: float
        self._time: float

        self.begin = time.perf_counter()
        self.mark()

    def mark(self):
        self._time = time.perf_counter()

    def sleep(self, seconds: float):
        """睡眠，单位为秒"""
        time.sleep(seconds)

    def sleepto(self, seconds: float):
        """睡眠到上一次mark后的某个时间点"""
        now = time.perf_counter()
        time_delta = seconds - (now - self._time)
        if time_delta < 0:
            return
        else:
            self.sleep(time_delta)

    def accurate_sleep(self, seconds: float) -> float:
        """精确睡眠"""
        time_begin = time.perf_counter()
        while True:
            elapsed = time.perf_counter() - time_begin
            remaining = seconds - elapsed
            if remaining <= 0:
                return remaining
            # 动态调整睡眠策略
            if remaining > 0.1:
                # 剩余时间多时，可以睡久一点
                time.sleep(min(remaining * 0.5, 0.05))
            elif remaining > 0.005:  # 5ms 以上用系统睡眠
                time.sleep(remaining * 0.9)  # 留一点余量给忙等待
            # 小于5ms时忙等待

    def accurate_sleepto(self, seconds: float) -> float:
        """精确睡眠到上一次mark后的某个时间点"""
        now = time.perf_counter()
        time_delta = seconds - (now - self._time)
        if time_delta < 0:
            return time_delta
        else:
            return self.accurate_sleep(time_delta)

    def now(self) -> float:
        return time.time()

    def count_begin(self) -> float:
        """计算从开始到现在的时间"""
        return time.perf_counter() - self.begin

    def count(self) -> float:
        """计算从上次mark到现在的时间"""
        return time.perf_counter() - self._time


def next_time(h: int, m: int, s) -> float:
    now = time.time()
    # 将当前时间转换为本地时间结构
    local_time = time.localtime(now)
    # 构造当天 h:m:s 的时间结构
    target_time = time.mktime(
        (
            local_time.tm_year,
            local_time.tm_mon,
            local_time.tm_mday,
            h,
            m,
            s,
            0,
            0,
            local_time.tm_isdst,
        )
    )
    # 如果当前时间已经超过 h:m:s，则目标时间是明天的 h:m:s
    if now >= target_time:
        target_time = time.mktime(
            (
                local_time.tm_year,
                local_time.tm_mon,
                local_time.tm_mday + 1,
                h,
                m,
                s,
                0,
                0,
                local_time.tm_isdst,
            )
        )
    # 计算时间差（秒数）
    seconds_remaining = target_time - now
    return seconds_remaining


def time_convert(t: float) -> str:
    # return time.ctime(t)
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t))


def random_second(max_seconds: float, min_seconds: float = 0.0) -> float:
    # 生成一个随机的某范围秒数
    return random.random() * (max_seconds - min_seconds) + min_seconds


if __name__ == "__main__":
    t = float(input("请输入一个时间戳: "))
    print(time_convert(t))
    t_plus = float(input("请输入给时间戳加上的时间（单位为秒）: "))
    print(t + t_plus)
    print(f"时间: {time_convert(t + t_plus)}")
