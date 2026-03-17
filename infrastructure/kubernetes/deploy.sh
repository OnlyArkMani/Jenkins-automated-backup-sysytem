
set -e

K8S_DIR="$(dirname "$0")"
APP=weather-dashboard

case "$1" in

  up)
    echo "==> Loading image into minikube (if built locally)"
    minikube image load devopsproject/${APP}:latest 2>/dev/null || true

    echo "==> Creating secret (if not exists)"
    kubectl create secret generic weather-dashboard-secret \
      --from-literal=OPENWEATHER_API_KEY="${OPENWEATHER_API_KEY:-changeme}" \
      --dry-run=client -o yaml | kubectl apply -f -

    echo "==> Applying manifests"
    kubectl apply -f "${K8S_DIR}/configmap.yaml"
    kubectl apply -f "${K8S_DIR}/deployment.yaml"
    kubectl apply -f "${K8S_DIR}/service.yaml"

    echo "==> Waiting for rollout..."
    kubectl rollout status deployment/${APP} --timeout=120s

    echo ""
    echo "✅ Deployed! Access URL:"
    minikube service weather-dashboard-service --url
    ;;

  down)
    echo "==> Removing all resources"
    kubectl delete -f "${K8S_DIR}/service.yaml"    --ignore-not-found
    kubectl delete -f "${K8S_DIR}/deployment.yaml" --ignore-not-found
    kubectl delete -f "${K8S_DIR}/configmap.yaml"  --ignore-not-found
    kubectl delete secret weather-dashboard-secret --ignore-not-found
    echo "✅ Cleaned up."
    ;;

  status)
    echo "==> Pods"
    kubectl get pods -l app=${APP} -o wide
    echo ""
    echo "==> Service"
    kubectl get svc weather-dashboard-service
    echo ""
    echo "==> Deployment"
    kubectl get deployment ${APP}
    ;;

  url)
    minikube service weather-dashboard-service --url
    ;;

  *)
    echo "Usage: $0 {up|down|status|url}"
    exit 1
    ;;
esac