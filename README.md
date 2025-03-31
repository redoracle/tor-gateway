<div style="display: flex; align-items: center;">
  <img src="static/Logo.png" alt="Tor Gateway Logo" style="height: 50px; margin-right: 20px;">
  <h1>Tor Gateway</h1>
</div>

![Tor Gateway](static/TorGateway.png)

The **Tor Gateway** project is a lightweight, containerized solution that provides a secure and configurable entry point to the Tor network. Built on Alpine Linux with Privoxy and runit, it allows you to control Tor’s configuration via environment variables, making it ideal for professional and production-grade deployments.

## Overview

**Tor Gateway** leverages:

- **Alpine Linux** for a minimal and secure base.
- **Privoxy** as an HTTP proxy routing traffic through Tor.
- **runit** for process supervision, ensuring high reliability.
- **Environment Variables** (prefixed with `TOR_`) to configure the Tor daemon without manual file edits.

The project also includes a simple web user interface (UI) for viewing current Tor exit node details and updating configuration settings dynamically. Changes trigger an automatic container restart, reloading the updated settings from the `.env` file.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Standalone Deployment](#standalone-deployment)
  - [Building the Image](#building-the-image)
  - [Configuring the Environment](#configuring-the-environment)
  - [Running the Container](#running-the-container)
  - [Verifying the Proxy](#verifying-the-proxy)
- [Docker Compose Integration](#docker-compose-integration)
  - [Sample Docker Compose Configuration](#sample-docker-compose-configuration)
  - [How It Works](#how-it-works)
  - [Deploying the Stack](#deploying-the-stack)
- [Additional Considerations](#additional-considerations)
  - [Troubleshooting](#troubleshooting)
  - [Security Recommendations](#security-recommendations)
- [F.A.Q](#faq)
- [References](#references)

## Prerequisites

Before you begin, ensure that you have the following installed:

- **Docker Engine**
- **Docker Compose**

Familiarity with basic Docker commands and networking concepts is assumed.

## Standalone Deployment

### Building the Image

Clone the repository and build the Docker image locally:

```bash
git clone https://github.com/redoracle/tor-gateway.git
cd tor-gateway
docker build -t tor-gateway .
```

This sequence clones the repository, changes into the project directory, and builds the image tagged as `tor-gateway`.

### Configuring the Environment

Customize the provided `.env` file to match your preferred Tor configuration. For example:

```ini
TOR_ExitNodes="{de},{nl},{fr},{se}"
TOR_StrictNodes="1"
TOR_MaxCircuitDirtiness=36000
TOR_Log="notice file /tmp/tor.log"
TOR_ControlPort=9052
TOR_SocksPort=9050
TOR_CookieAuthentication=1
TOR_HashedControlPassword="your-hashed-password" (create it: `tor --hash-password your_password`)
```

Ensure the settings meet your operational requirements.

### Running the Container

Deploy the container in detached mode with the proper environment injection and volume mounting:

```bash
docker run -d \
  --restart unless-stopped \
  --name Tor-Gateway \
  -p 8118:8118 \
  -p 8080:5000 \
  --env-file "$(pwd)/.env" \
  -v "$(pwd)/.env:/home/dockeruser/.env" \
  tor-gateway:latest
```

This command starts the container with automatic restart, exposes the necessary ports, and ensures configuration updates are available at runtime. See [Docker.md](Docker.md) for further docker tips.

### Verifying the Proxy

To verify that the proxy is operational, run:

```bash
curl --proxy http://localhost:8118 http://api.ipify.org/?format=json
```

Alternatively, open your web browser and navigate to [http://localhost:8080](http://localhost:8080) to access the UI.

## Docker Compose Integration

For more complex deployments that involve multiple services (such as Pi-hole, WireGuard, or AI crawling tools), you can integrate **Tor Gateway** into your Docker Compose configuration.

### Sample Docker Compose Configuration

Here an example [docker-compose.yml](examples/docker-compose.yml) file that incorporates several services:

### How It Works

- **Defined IP Range:** Each container is assigned a fixed IP within the `red_net` network, facilitating smooth inter-container communication.
- **Environment Configuration:** The `tor-gateway` service uses an external `.env` file for both startup configuration and dynamic runtime updates.
- **Port Exposure:** The proxy service (Privoxy on port 8118) and the web interface (port 8080) can be exposed through Docker or managed with a reverse proxy.
- **Service Chaining:** Other services, such as Pi-hole, can be configured to route DNS requests so you can filter dad IPs and ads while using the Tor Gateway (port 8118) you can leverage the anonymity network. All this by using a Wireguard VPN that act as access to your private services without sacrifing security.
- **Health Checks:** Each container includes health checks to ensure services are running as expected and automatically restart if necessary.

### Deploying the Stack

Launch the multi-service stack with the following command:

```bash
docker compose -f docker-compose.yml up -d
```

To monitor the deployment in real time, use:

```bash
docker compose logs -f
```

This command displays real-time logs, helping you promptly detect and resolve any issues.

## Additional Considerations

### Troubleshooting

- **Container Startup:** Verify that the `.env` file is correctly configured and properly mounted.
- **Network Connectivity:** Ensure that the Docker network (`red_net`) is correctly defined and that containers can communicate.
- **Logs:** Use `docker compose logs` to review error messages or warnings that might indicate misconfiguration.

### Security Recommendations

- **Password Management:** Generate (using: `tor --hash-password your_password`) and store `TOR_HashedControlPassword` securely.
- **Sensitive Data:** Avoid exposing sensitive environment variables in public repositories; consider using Docker secrets.
- **Port Exposure:** Limit port exposure to trusted networks or use reverse proxies to manage external access.

## Dockerfile and Scripts

### Dockerfile

- [Dockerfile](Dockerfile)


### torvariables.sh Script

- [torvariables.sh](torvariables.sh)

## F.A.Q

**Q: I configured my Tor Gateway with `TOR_ExitNodes="{uk}"`, but it doesn’t connect using a United Kingdom IP. Why?**  
**A:** Tor uses the ISO 3166-1 alpha-2 country code for the United Kingdom, which is `{gb}` rather than `{uk}`. Update your configuration accordingly.

**Q: How do I force a runtime environment reload after updating the `.env` file?**  
**A:** The container’s environment is set at startup. To reload, restart the container. The web UI writes the updated configuration to `.env` and triggers a full restart via SIGTERM on PID 1.

**Q: Why are the runtime environment variables different from those in the `.env` file?**  
**A:** Docker only injects environment variables at startup from the `--env-file`. Any changes require a container restart to take effect.

**Q: My Tor circuit doesn’t change even after updating configuration. What’s wrong?**  
**A:** Ensure the environment variables are valid and that `torvariables.sh` writes the new configuration correctly to `/etc/tor/torrc`. Also, note that Tor may cache circuits for the duration specified by `TOR_MaxCircuitDirtiness`.

**Q: Can I run this container as a non-root user?**  
**A:** Yes, the container runs as a non-root user for enhanced security. However, certain operations (like sending SIGTERM to PID 1) may require root privileges. Advanced users can adjust privileges with tools like `gosu` or `su-exec`.

## References

- **Docker Hub:** `redoracle/tor-gateway`
- **Tor Project FAQ:** [Tor Usage](https://www.torproject.org/docs/faq)

The **Tor Gateway** project offers a secure, efficient, and configurable gateway to the Tor network. By leveraging environment variables, process supervision, and a dynamic web UI, it provides a robust solution for both isolated and integrated deployments. Contributions, issue reports, and pull requests are welcome—please refer to the repository guidelines for further details.

For any further inquiries or contributions, open an issue or submit a pull request on the project’s GitHub repository.