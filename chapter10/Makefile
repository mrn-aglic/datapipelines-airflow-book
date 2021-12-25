build-wttr:
	docker build --tag airflowbook/wttr-example fetch_weather

run-wttr:
	docker run --rm --volume `pwd`/data:/data airflowbook/wttr-example Amsterdam --output_path /data/amsterdam.json
