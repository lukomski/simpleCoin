# Real shit coin

## Stack technologiczny

Flask + docker

## Uruchomienie

Aby sieć waluty istniała musi być uruchomiony co najmniej jeden węzeł. Aby uruchomić sieć wystarczy wykonać poniższe polecenie.

```
docker-compose up --build
```

## Dodanie kolejnego węzła

Przygotowany jest niewielki skrypt pozwalający uruchomić kolejny węzeł w tej samej sieci w której znajduje się węzeł 0.

```
bash scripts/addNode
```

## Endpointy każdego węzła

GET /nodes - Pozwala pobrać bazę dostępnych węzłów.
POST /nodes - Pozwala dodać nowy węzeł
GET /publicKey - Pozwala pobrać klucz publiczny
GET /sign?message=foo - Pozwala wygenerować hash przy użyciu klucza prywatnego do wiadomości
