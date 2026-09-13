from time import sleep as wait
import os
import utils
from random import randint as rand
dataset = [rand(-1000, 1000) for i in range(2000)]
t = b = -868
l44 = 0
def sort_vibor(dataset):
    N = len(dataset)
    for a in range(N - 1):
        m = dataset[a]
        p = a
        for b in range(a + 1, N):
            if m < dataset[b]:
                m = dataset[b]
                p = b
        if p != a:
            t = dataset[a]
            dataset[a] = dataset[p]
            dataset[p] = t
    return(dataset)
sort1 = sort_vibor(dataset)


def sort_bingo(dataset):
    max = len(dataset)- 1
    next = dataset[max]
    for i in range(max - 1, -1, -1):
        if dataset[i] > next:
            next = dataset[i]
    while max and next == dataset[max]:
        max -= 1
    while max:
        value = next
        next = dataset[max]
        for i in range(max - 1, -1, -1):
            if dataset[i] == value:
                dataset[i], dataset[max] = dataset[max], dataset[i]
                max -= 1
            elif dataset[i] > next:
                next = dataset[i]
        while max and dataset[max] == next:
            max -= 1
    return(dataset)
sort2 = sort_bingo(dataset)

def pancake_sort(dataset):
    if len(dataset) > 1:
        for size in range(len(dataset), 1, -1):
            maxindex = max(range(size), key=dataset.__getitem__)
            if maxindex+1 != size:
                if maxindex != 0:
                    dataset[:maxindex+1] = reversed(dataset[:maxindex+1])
                dataset[:size] = reversed(dataset[:size])
    return(dataset)
sort3 = pancake_sort(dataset)

def sort_vstavka(dataset):
    N = len(dataset)
    for i in range(1, N):
        for j in range(i, 0, -1):
            if dataset[j] < dataset[j-1]:
                dataset[j], dataset[j-1] = dataset[j-1], dataset[j]
            else:
                break
    return(dataset)
sort4 = sort_vstavka(dataset)

def sort_bin(dataset):
    N = len(dataset)
    for i in range(1, N):
        key = dataset[i]
        low = 0
        high = i-1
        while low <= high:
            mid = (low + high) // 2
            if key < dataset[mid]:
                high = mid - 1
            else:
                low = mid + 1
        for j in range(i, low, -1):
            dataset[j] = dataset[j-1]
        dataset[low] = key
    return(dataset)
sort5 = sort_bin(dataset)
def sort_puz(dataset):
    N = len(dataset)
    for i in range(N - 1):
        for j in range(N - 1 - i):
            if dataset[j] > dataset[j+1]:
                dataset[j], dataset[j+1] = dataset[j+1], dataset[j]
    return(dataset)
sort6 = sort_puz(dataset)
def sort_slian(dataset):
    N = len(dataset) // 2
    a, b = dataset[:N], dataset[N:]
    if len(a) > 1:
        a = sort_slian(a)
    if len(b) > 1:
        b = sort_slian(b)
    return utils.merge_list(a, b)
sort7 = sort_slian(dataset)

def quick_sort(dataset):
    if len(dataset) > 1:
        x = dataset[rand(0, len(dataset)-1)]
        lower = [u for u in dataset if u < x]
        cent = [u for u in dataset if u == x]
        upper = [u for u in dataset if u > x]
        dataset = quick_sort(lower) + cent + quick_sort(upper)
    return(dataset)
sort8 = quick_sort(dataset)
while True:
    os.system('cls')
    print('Привет!' if l44 == 0 else 'Привет еще раз!')
    print('Выберите сортировку:')
    print('1. Сортировка выбором')
    print('2. Сортировка бинго')
    print('3. Сортировка панкейк')
    print('4. Сортировка вставками')
    print('5. Бинарный поиск')
    print('6. Сортировка пузырем')
    print('7. Сортировка слиянием')
    m1 = int(input('Введите число: '))
    if m1 == 1:
        print(sort1)
    elif m1 == 2:
        print(sort2)
    elif m1 == 3:
        print(sort3)
    elif m1 == 4:
        print(sort4)
    elif m1 == 5:
        print(sort5)
    elif m1 == 6:
        print(sort6)
    elif m1 == 7:
        print(sort7)
    elif m1 == 8:
        print(sort8)
    else:
        l44 += 1
        wait(1)
        continue
    wait(1)
    print('Продолжаем?\n 1. Да\n 2. Нет')
    n2 = int(input('Введите число: '))
    if n2 == 1:
        l44 += 1
        print('Секунду!')
        wait(1.5)
        continue
    else:
        print('Пока!')
        wait(1.5)
        break