import app
import itertools
import random

profile = app.profile
parametry = app.parametry
policz = app.policz

print("\nWALIDACJA MATEMATYCZNA\n")

bledy = 0
testy = 0

# objętości testowe
objetosci = [40,50,60,70,80,100,120,150,200]

for profil in profile:

    lista = profile[profil]

    # usuwamy jony z listy kombinacji
    param_list = [
        p for p in lista
        if p in parametry and parametry[p]["jon"] == 0
    ]

    ul_list = [parametry[p]["ul"] for p in param_list]

    for obj in objetosci:

        wynik = policz(obj, profil, "")

        if "z_gldh" in wynik:
            zakres = wynik["z_gldh"]
        else:
            zakres = wynik["bez_gldh"]

        min_alg, max_alg = map(int, zakres.split("-"))

        # realna matematyka
        real_min = 999
        real_max = 0

        dostepna = obj - 50

        if dostepna <= 0:
            real_min = 0
            real_max = 0
        else:

            for r in range(len(ul_list)+1):

                for combo in itertools.combinations(ul_list, r):

                    suma = sum(combo)

                    if suma <= dostepna:

                        n = len(combo)

                        real_min = min(real_min, n)
                        real_max = max(real_max, n)

        if real_min == 999:
            real_min = 0

        if real_min != min_alg or real_max != max_alg:

            print(
                "BŁĄD:",
                profil,
                obj,
                "alg:", min_alg, max_alg,
                "real:", real_min, real_max
            )

            bledy += 1

        testy += 1


print("\nTESTY:", testy)
print("BŁĘDY:", bledy)