#!/bin/bash
# Kafka ACL Setup Script for Kebos AI
# Creates SCRAM-SHA-256 users and enforces strict topic-level permissions

set -e

KAFKA="kafka:9092"
KAFKA_CONTAINER="kafka"

# Wait for Kafka to be ready
echo "Waiting for Kafka to be ready..."
until docker exec $KAFKA_CONTAINER kafka-broker-api-versions --bootstrap-server $KAFKA &>/dev/null; do
  echo "Kafka not ready yet, sleeping 5 seconds..."
  sleep 5
done
echo "Kafka is ready."

# Create SCRAM-SHA-256 users
echo "Creating SCRAM-SHA-256 users..."

docker exec $KAFKA_CONTAINER kafka-configs --bootstrap-server $KAFKA --alter --add-config 'SCRAM-SHA-256=[password=kebos_backend_secret]' --entity-type users --entity-name kebos-backend
docker exec $KAFKA_CONTAINER kafka-configs --bootstrap-server $KAFKA --alter --add-config 'SCRAM-SHA-256=[password=qmind_secret]' --entity-type users --entity-name qmind
docker exec $KAFKA_CONTAINER kafka-configs --bootstrap-server $KAFKA --alter --add-config 'SCRAM-SHA-256=[password=honeygrid_secret]' --entity-type users --entity-name honeygrid
docker exec $KAFKA_CONTAINER kafka-configs --bootstrap-server $KAFKA --alter --add-config 'SCRAM-SHA-256=[password=crawler_secret]' --entity-type users --entity-name crawler

echo "SCRAM-SHA-256 users created."

# Create topics
echo "Creating Kafka topics..."

docker exec $KAFKA_CONTAINER kafka-topics --bootstrap-server $KAFKA --create --topic threat.indicators --partitions 3 --replication-factor 1 --if-not-exists
docker exec $KAFKA_CONTAINER kafka-topics --bootstrap-server $KAFKA --create --topic analyst.feedback --partitions 3 --replication-factor 1 --if-not-exists
docker exec $KAFKA_CONTAINER kafka-topics --bootstrap-server $KAFKA --create --topic qmind.results --partitions 3 --replication-factor 1 --if-not-exists
docker exec $KAFKA_CONTAINER kafka-topics --bootstrap-server $KAFKA --create --topic crawler.discoveries --partitions 3 --replication-factor 1 --if-not-exists
docker exec $KAFKA_CONTAINER kafka-topics --bootstrap-server $KAFKA --create --topic honeypot.interactions --partitions 3 --replication-factor 1 --if-not-exists

echo "Kafka topics created."

# Set ACLs for kebos-backend
# WRITE: threat.indicators, analyst.feedback
# READ: qmind.results
echo "Setting ACLs for kebos-backend..."
docker exec $KAFKA_CONTAINER kafka-acls --bootstrap-server $KAFKA --add --allow-principal User:kebos-backend --operation WRITE --topic threat.indicators
docker exec $KAFKA_CONTAINER kafka-acls --bootstrap-server $KAFKA --add --allow-principal User:kebos-backend --operation WRITE --topic analyst.feedback
docker exec $KAFKA_CONTAINER kafka-acls --bootstrap-server $KAFKA --add --allow-principal User:kebos-backend --operation READ --topic qmind.results

# Set ACLs for qmind
# WRITE: qmind.results
# READ: threat.indicators, crawler.discoveries, honeypot.interactions
echo "Setting ACLs for qmind..."
docker exec $KAFKA_CONTAINER kafka-acls --bootstrap-server $KAFKA --add --allow-principal User:qmind --operation WRITE --topic qmind.results
docker exec $KAFKA_CONTAINER kafka-acls --bootstrap-server $KAFKA --add --allow-principal User:qmind --operation READ --topic threat.indicators
docker exec $KAFKA_CONTAINER kafka-acls --bootstrap-server $KAFKA --add --allow-principal User:qmind --operation READ --topic crawler.discoveries
docker exec $KAFKA_CONTAINER kafka-acls --bootstrap-server $KAFKA --add --allow-principal User:qmind --operation READ --topic honeypot.interactions

# Set ACLs for honeygrid
# WRITE: honeypot.interactions ONLY
echo "Setting ACLs for honeygrid..."
docker exec $KAFKA_CONTAINER kafka-acls --bootstrap-server $KAFKA --add --allow-principal User:honeygrid --operation WRITE --topic honeypot.interactions

# Set ACLs for crawler
# WRITE: crawler.discoveries ONLY
echo "Setting ACLs for crawler..."
docker exec $KAFKA_CONTAINER kafka-acls --bootstrap-server $KAFKA --add --allow-principal User:crawler --operation WRITE --topic crawler.discoveries

echo "Kafka ACLs configured successfully."

# List ACLs for verification
echo "Current ACLs:"
docker exec $KAFKA_CONTAINER kafka-acls --bootstrap-server $KAFKA --list
