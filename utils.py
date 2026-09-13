def merge_list(a , b):
    C = []
    N = len(a)
    M = len(b)
    i = 0
    j = 0
    while i < N and j < M:
        if a[i] < b[j]:
            C.append(a[i])
            i+=1
        else:
            C.append(b[j])
            j+=1
    C += a[i:]+b[j:]
    return C