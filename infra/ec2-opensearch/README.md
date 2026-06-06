# EC2 OpenSearch Host

This folder contains a minimal self-hosted OpenSearch setup for Encuentra. It runs a single OpenSearch node in Docker on EC2 and lets the backend connect through the non-SigV4 OpenSearch client path.

## Files

- `docker-compose.yml`: persistent single-node OpenSearch container.
- `user-data.sh`: EC2 bootstrap script that installs Docker and starts OpenSearch.
- `.env.example`: backend environment values for connecting the API to this EC2 node.

## EC2 Setup

1. Launch an EC2 instance with enough memory for OpenSearch. Start with at least 2 vCPU, 4 GiB RAM, and an EBS volume sized for the corpus and index growth.
2. Put the instance in the same VPC as the backend/API runtime when possible.
3. Attach a security group that allows inbound TCP `9200` only from the backend/API security group. Do not expose `9200` publicly.
4. Paste `user-data.sh` into the EC2 user data field, or copy this folder to the instance and run:

   ```bash
   cd /opt/encuentra-opensearch
   docker compose up -d
   ```

5. Configure the backend with the EC2 private address:

   ```env
   SEARCH_BACKEND=opensearch
   OPENSEARCH_HOSTS=http://<ec2-private-ip-or-dns>:9200
   OPENSEARCH_SIGV4=false
   OPENSEARCH_VERIFY_CERTS=false
   OPENSEARCH_INDEX_PREFIX=encuentra-stg
   SKIP_REINDEX_ON_STARTUP=true
   FORCE_REINDEX_ON_STARTUP=false
   ```

## Smoke Checks

From the EC2 instance:

```bash
docker ps
curl http://localhost:9200
```

From the backend/API network:

```bash
curl http://<ec2-private-ip-or-dns>:9200
curl http://<backend-host>/ping
```

On backend startup, the app checks whether the `supreme_court` search space exists. With `SKIP_REINDEX_ON_STARTUP=true`, it builds the index only when missing. Set `FORCE_REINDEX_ON_STARTUP=true` for a one-time rebuild, then switch it back to `false`.

## Security Notes

The compose file disables OpenSearch's built-in security plugin. That is only acceptable when the EC2 node is reachable through private networking and strict security groups. For broader exposure, put OpenSearch behind TLS/auth or use AWS-managed OpenSearch/AOSS with `OPENSEARCH_SIGV4=true`.
