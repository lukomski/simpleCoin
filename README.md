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
czasami należy poprzedzić powyższe polecenie:
```
docker network rm $(docker network ls -q)
```

## Wyświetlenie drzewa bloków
http://localhost:5000/blocks:tree

## Dodanie kolejnego węzła

Należy uruchomić docker z podaną nazwą sieci do której chcemy się podłączyć oraz adresem węzła pod który chcemy się podłączyć.
Nazwa sieci oraz obrazu została ustawiona na podstawie docker-compose'a, więc nie należy jej zmieniać. Adres referencyjny należy wybrać z listy dostępnych węzłów.
Przykładowe uruchomienie kolejnego węzła:

```
docker run --env REFERENCE_ADDRESS=192.19.0.2:5000 --network scnetwork simplecoin_node0
```

## Endpointy każdego węzła

GET /blocks - Pozwala pobrać listę bloków w sieci

GET /nodes - Pozwala pobrać bazę dostępnych węzłów

POST /connect-node - Pozwala dodać nowy węzeł

GET /public-key - Pozwala pobrać klucz publiczny

POST /update-pub-list - Pozwala zaktualizować listę dostępnych węzłów

POST /message - Pozwala odebrać wiadomość od innego węzła

POST /transaction - Pozwala dodać transakcję do najbliższego bloku

---

POST /message:invoke?message={message}&public_key={public_key} - Pozwala zainicjować wysłanie wiadomości do innego węzła

### Postman

Dostępna jest kolekcja dla postmana znajdująca się w [postman.json](postman.json)

# Wiadomości

Wiadomości wysyłane pomiędzy węzłami składają się pola 'payload' oraz 'hash'. Treść wiadomości jest jawna.

```
{
    payload: {
        type: 'message',
        message: <MESSAGE>,
    },
    signature: <SIGNATURE>,
}
```

Wysyłane bloki są wysyłane w postaci:

```
{
    payload: {
        type: 'add_block',
        block: {
            header: {
                prev_block_hash: <PREV_HASH>,
                nonce: <NONCE>,
                hash_prev_nonce: <HASH OF COMBINED 'nonce' AND 'prev_block_hash' VALUES>
                miner_pub_key: <PUBLIC KEY OF THE MINER>,
            },
            data: <DATA>
        }
    },
    signature: <SIGNATURE>,
}
```

# Pliki z wydobytymi blokami

Pliki zapisywana są na maszynach węzłów. Podejrzeć plik można przy użyciu poniższego polecenia

```
docker exec -it sc_node0 cat blockchain.json
```

Aby usunąć plik należy wykonać polecenie:

```
docker exec -it sc_node0 rm blockchain.json
```

W celu ręcznej edycji pliku blockchaina (np w celu sprawdzenia czy weryfikowana jest poprawność łańcucha) należy wykonać poniższe polecenia

```
docker exec -it sc_node0 bash
apt update && apt install -y vim
vim blockchain.json
```
