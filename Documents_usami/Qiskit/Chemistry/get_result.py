import argparse
from enum import Enum
import grpc
import json
import qc_simulator_pb2
import qc_simulator_pb2_grpc

#SERVER_ADDRESS = "172.16.1.9"
SERVER_ADDRESS = "localhost"
SERVER_PORT = 33351
TOKEN = "eyJhbGciOiJFUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJRUGNIdThPdkg5MjJhcVZkLWlhWWwzTDVyc192SGkxaldwbHFKSkhIUjBRIn0.eyJleHAiOjE3MzcwMDc3MjYsImlhdCI6MTczNzAwNzQyNiwiYXV0aF90aW1lIjoxNzM3MDA3NDI2LCJqdGkiOiJkNDBmZWI2Zi1jN2UyLTQxMmMtOTc5Mi0zMWU2YWM5MjEwN2YiLCJpc3MiOiJodHRwczovL2lkcC5xYy5yLWNjcy5yaWtlbi5qcC9yZWFsbXMvamhwYy1xdWFudHVtIiwiYXVkIjoiYWNjb3VudCIsInN1YiI6ImRlYjI5ZjNmLTA2ODYtNDFmOC05NzVlLTA4NWVlMGIyMjg5OCIsInR5cCI6IkJlYXJlciIsImF6cCI6ImpocGNxLXJlZG1pbmUiLCJzaWQiOiJiZmIyYjc1Ny1hYTEzLTQyMWEtYTJjZi1jOWI5M2IwODg2ZmQiLCJhY3IiOiIxIiwiYWxsb3dlZC1vcmlnaW5zIjpbImh0dHBzOi8vcG9ydGFsLnFjLnItY2NzLnJpa2VuLmpwIl0sInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJvZmZsaW5lX2FjY2VzcyIsImRlZmF1bHQtcm9sZXMtamhwYy1xdWFudHVtIiwidW1hX2F1dGhvcml6YXRpb24iXX0sInJlc291cmNlX2FjY2VzcyI6eyJhY2NvdW50Ijp7InJvbGVzIjpbIm1hbmFnZS1hY2NvdW50IiwibWFuYWdlLWFjY291bnQtbGlua3MiLCJ2aWV3LXByb2ZpbGUiXX19LCJzY29wZSI6Im9wZW5pZCBwcm9maWxlIGVtYWlsIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsIm5hbWUiOiJ0YWthc2hpIHVjaGlkYSIsInByZWZlcnJlZF91c2VybmFtZSI6InRha2FzaGkudWNoaWRhIiwiZ2l2ZW5fbmFtZSI6InRha2FzaGkiLCJmYW1pbHlfbmFtZSI6InVjaGlkYSIsImVtYWlsIjoidGFrYXNoaS51Y2hpZGFAcmlrZW4uanAifQ.ezdji9V2W8trNXTr7aaLa9vNbUR98kn49tIj88KaBTZi2lcE9I9zjkNxLN07q0sESP-8ziLkiLfpBavCDc0B8Q"


class ResponseStatus(Enum):
    UNKNOWN = 0
    QUEUED = 1
    RUNNING = 2
    COMPLETED = 3
    FAILED = 4


def get_result(job_id: int):
    with grpc.insecure_channel(f"{SERVER_ADDRESS}:{SERVER_PORT}") as channel:
        stub = qc_simulator_pb2_grpc.SimulatorServiceStub(channel)

        response = stub.GetResult(
            qc_simulator_pb2.GetResultRequest(token=TOKEN, job_id=job_id)
        )

        #print(f"job_id:{response.job_id}")
        #print(f"status:{ResponseStatus(response.status).name}")
        #print(f"message:{response.message}")
        #print(f"result_json:{response.result_json}")
        status = ResponseStatus(response.status)
        result = json.loads(response.result_json) if response.result_json else None
        return status, result


