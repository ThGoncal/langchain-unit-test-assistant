def moyenne(nombres):
    total = 0

    for nombre in nombres:
        total += nombre

    return total / len(nombres)


def est_pair(nombre):
    if nombre % 2 == 0:
        return True
    else:
        return False