# Simple Coin

### Autorzy:

- Jan Łukomski

- Adrian Bączek

## Stack technologiczny

Flask + docker

## Uruchomienie

Aby sieć waluty istniała musi być uruchomiony co najmniej jeden węzeł. Aby uruchomić sieć wystarczy wykonać poniższe polecenie.

```
docker-compose up --build
```

## Dodanie kolejnego węzła

Należy uruchomić docker z podaną nazwą sieci do której chcemy się podłączyć oraz adresem węzła pod który chcemy się podłączyć.
Nazwa sieci oraz obrazu została ustawiona na podstawie docker-compose'a, więc nie należy jej zmieniać. Adres referencyjny należy wybrać z listy dostępnych węzłów.
Przykładowe uruchomienie kolejnego węzła:

```
docker run --env REFERENCE_ADDRESS=192.19.0.2:5000 --network scnetwork simplecoin_node0
```

## Endpointy każdego węzła

GET /nodes - Pozwala pobrać bazę dostępnych węzłów.

POST /connect-node - Pozwala dodać nowy węzeł

GET /publicKey - Pozwala pobrać klucz publiczny

POST /update-pub-list - Pozwala zaktualizować listę dostępnych węzłów

POST /message - Pozwala odebrać wiadomość od innego węzła

--

POST /message:invoke?message={message}&address={destination_address} - Pozwala zainicjować wysłanie wiadomości do innego węzła

# Widomości

Wiadomości wysyłane pomiędzy węzłami składają się pola 'payload' oraz 'hash'. Treść wiadomości jest jawna.

```V
{
    payload: {
        type: 'message',
        message: <MESSAGE>,
    },
    hash: <HASH>,
}
```
