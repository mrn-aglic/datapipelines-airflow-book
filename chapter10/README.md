#Chapter 10

Be sure to build all of the docker images before running the
DAGs. Especially the second one. It will fail if the images
are not pre-built.
You can check out the Makefiles in both docker and kubernetes
folders to get the idea of which commands to use to build the
images.

Also, note that the `docker-compose.yml` in kubernetes folder
needs to mount the kubeconfig from local machine.

Make sure that the movielens api is exposed as a service
while the DAG is running: `make kube-bind-movielens`.
