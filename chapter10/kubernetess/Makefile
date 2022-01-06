kube-create-namespace:
	kubectl create namespace airflowbook

kube-apply-data-volume:
	kubectl --namespace airflowbook apply -f resources/data-volume.yml

kube-apply-deployment:
	kubectl --namespace airflowbook apply -f resources/deployment.yml

get-pods:
	kubectl --namespace airflowbook get pods

kube-delete-all:
	kubectl --namespace airflowbook delete all --all && kubectl --namespace airflowbook delete pv --all && make kube-delete-namespace

kube-delete-namespace:
	kubectl delete namespace airflowbook

kube-create-all:
	make kube-create-namespace && make kube-apply-data-volume && make kube-apply-deployment

kube-bind-movielens:
	kubectl --namespace airflowbook port-forward svc/movielens 8000:80

build-images:
	docker build --tag airflowbook/movielens-fetch:k8s ../docker/images/movielens-fetch-reqs && docker build --tag airflowbook/movielens-rank:k8s ../docker/images/movielens-rank
