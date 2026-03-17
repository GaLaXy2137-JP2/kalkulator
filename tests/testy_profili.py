import app
import random

profile = list(app.profile.keys())
policz = app.policz

print("\nLOSOWY TEST SILNIKA\n")

testy = 2000
bledy = 0

for i in range(testy):

    profil1 = random.choice(profile)

    # czasem drugi profil
    if random.random() < 0.3:
        profil2 = random.choice(profile)
    else:
        profil2 = ""

    # losowa objętość
    objetosc = random.randint(10,300)

    try:

        wynik = policz(objetosc, profil1, profil2)

        if "z_gldh" in wynik:
            zakres = wynik["z_gldh"]
        else:
            zakres = wynik["bez_gldh"]

        min_b, max_b = map(int, zakres.split("-"))

        # TEST 1
        if min_b > max_b:
            print("BŁĄD zakresu:", profil1, profil2, objetosc, zakres)
            bledy += 1

        # TEST 2
        if min_b < 0 or max_b < 0:
            print("BŁĄD wartości:", profil1, profil2, objetosc, zakres)
            bledy += 1

    except Exception as e:

        print("CRASH:", profil1, profil2, objetosc, e)
        bledy += 1

print("\nTEST ZAKOŃCZONY")
print("Testów:", testy)
print("Błędów:", bledy)
