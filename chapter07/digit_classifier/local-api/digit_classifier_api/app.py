import json
from io import BytesIO

import boto3
import numpy as np
from chalice import Chalice, Response
from PIL import Image
from sagemaker.amazon.common import RecordSerializer

app = Chalice(app_name="number-classifier")


@app.route("/hello", methods=["GET"])
def hello():
    return Response("Hello world", status_code=200)


@app.route("/", methods=["POST"], content_types=["image/jpeg"])
def predict():
    """Provide this endpoint an image in jpeg format.

    The image should be equal in size to the training images (28x28).
    """
    img = Image.open(BytesIO(app.current_request.raw_body)).convert("L")
    img_arr = np.array(img, dtype=np.float32)

    runtime = boto3.Session().client(
        service_name="sagemaker-runtime", region_name="eu-west-1"
    )

    record_serializer = RecordSerializer()

    response = runtime.invoke_endpoint(
        EndpointName="mnistclassifier",
        ContentType="application/x-recordio-protobuf",
        Body=record_serializer.serialize(img_arr.flatten()),
    )

    result = json.loads(response["Body"].read().decode("utf-8"))

    return Response(
        result, status_code=200, headers={"Content-Type": "application/json"}
    )
