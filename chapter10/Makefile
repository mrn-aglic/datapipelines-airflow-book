build-wttr:
	docker build --tag airflowbook/wttr-example fetch_weather

run-wttr:
	docker run --rm --volume `pwd`/data:/data airflowbook/wttr-example Amsterdam --output_path /data/amsterdam.json

build-fetch:
	docker build --tag airflowbook/movielens-fetch images/movielens-fetch-reqs

run-fetch:
	docker run --rm airflowbook/movielens-fetch fetch-ratings --help

build-rank:
	docker build --tag airflowbook/movielens-rank images/movielens-rank

run-rank:
	docker run --rm airflowbook/movielens-rank rank-movies --help

build-images:
	docker build --tag airflowbook/movielens-fetch images/movielens-fetch-reqs && docker build --tag airflowbook/movielens-rank images/movielens-rank
