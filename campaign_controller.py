from fastapi import FastAPI
from pydantic import BaseModel
from kubernetes import client, config
import base64
import json
import uuid

app = FastAPI()

# Load Kubernetes config
try:
    config.load_incluster_config()  # For when running inside a cluster
except:
    config.load_kube_config()  # Use when running locally

batch_v1 = client.BatchV1Api()

# Request Model
class CampaignRequest(BaseModel):
    name: str
    schedule: Optional[str] = "0 0 * * *"  # Default: daily at 12AM
    target_api_url: str
    payload: Optional[dict] = {}


def create_cronjob(campaign: CampaignRequest):
    job_name = f"{campaign.name}-{uuid.uuid4().hex[:6]}"  # Unique job name

    encoded_payload = base64.b64encode(json.dumps(campaign.payload).encode()).decode()

    cronjob = client.V1CronJob(
        metadata=client.V1ObjectMeta(name=job_name),
        spec=client.V1CronJobSpec(
            schedule=campaign.schedule,
            job_template=client.V1JobTemplateSpec(
                spec=client.V1JobSpec(
                    template=client.V1PodTemplateSpec(
                        spec=client.V1PodSpec(
                            restart_policy="Never",
                            containers=[
                                client.V1Container(
                                    name="campaign-job",
                                    image="curlimages/curl:latest",
                                    command=[
                                        "sh", "-c",
                                        f'echo {encoded_payload} | base64 -d > /tmp/payload.json && '
                                        f'curl -X POST -H "Content-Type: application/json" '
                                        f'-H "x-api-key: $API_KEY" '
                                        f'-d @/tmp/payload.json "{campaign.target_api_url}"'
                                    ],
                                    env=[
                                        client.V1EnvVar(name="API_KEY", value=os.getenv("BACK_END_API_KEY", "changeme"))
                                    ]
                                )
                            ]
                        )
                    )
                )
            )
        )
    )

    batch_v1.create_namespaced_cron_job(namespace="default", body=cronjob)
    return job_name

@app.post("/create_campaign")
def create_campaign(campaign: CampaignRequest):
    try:
        job_name = create_cronjob(campaign)
        return {"message": "Campaign scheduled successfully", "job_name": job_name}
    except Exception as e:
        return {"error": str(e)}

