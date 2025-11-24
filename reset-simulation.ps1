# reset-simulation.ps1

Write-Host "--------------------------------------------"
Write-Host "  REINICIANDO SIMULACAO KUBERNETES (CSC-27) " -ForegroundColor Cyan
Write-Host "--------------------------------------------"

# 1. LIMPEZA DE RECURSOS ANTIGOS
Write-Host "[1/6] Limpando recursos antigos..." -ForegroundColor Yellow

kubectl delete -f chaos-robot.yaml --ignore-not-found=true
kubectl delete -f app-kubernetes.yaml --ignore-not-found=true
kubectl delete pod load-generator --ignore-not-found=true

Write-Host "      Aguardando remocao dos pods (8s)..." -ForegroundColor DarkGray
Start-Sleep -Seconds 8

# 2. APLICAR APLICACAO (DEPLOYMENT + SERVICE + HPA)
Write-Host "[2/6] Aplicando manifestos da aplicacao..." -ForegroundColor Yellow
kubectl apply -f app-kubernetes.yaml

Write-Host "      Aguardando rollout do Deployment php-apache..." -ForegroundColor DarkGray
kubectl rollout status deployment/php-apache --timeout=90s

# 3. ESTADO INICIAL
Write-Host "[3/6] Estado inicial da aplicacao:" -ForegroundColor Yellow
kubectl get deploy,svc,hpa,pods

# 4. GERADOR DE CARGA (EXPERIMENTO 1)
Write-Host "[4/6] Iniciando Gerador de Carga (load-generator)..." -ForegroundColor Cyan

# Gera trafego continuo para o Service php

# kubectl run  -i --tty load-generator -rm `
#   --image=curlimages/curl:latest `
#   --restart=Never `
#   -- /bin/sh -c "while true; do wget -q -O- http://php; done"
kubectl run load-generator --image=busybox:1.28 --restart=Never -- /bin/sh -c "while true; do wget -q -O- http://php-apache; done" > $null

Write-Host "      Aguardando a carga comecar a bater (10s)..." -ForegroundColor DarkGray
Start-Sleep -Seconds 10

# 5. CHAOS ROBOT (EXPERIMENTO 2)
Write-Host "[5/6] Iniciando Chaos Robot (CronJob)..." -ForegroundColor Magenta
kubectl apply -f chaos-robot.yaml

Write-Host "      Chaos Robot agendado! Ele vai deletar pods periodicamente." -ForegroundColor DarkGray

# 6. MONITORAR A SIMULACAO AO VIVO
Write-Host "--------------------------------------------" -ForegroundColor Cyan
Write-Host "[6/6] MONITORANDO PODS, DEPLOY E HPA (CTRL+C para sair)" -ForegroundColor Green
Write-Host "Veja os pods sendo recriados enquanto o Chaos Robot ataca." -ForegroundColor Green
Write-Host "--------------------------------------------" -ForegroundColor Cyan

# Abre três janelas paralelas de monitoramento
Start-Job { kubectl get pods -w }
Start-Job { kubectl get deployment php -w }
Start-Job { kubectl get hpa php -w }

Write-Host "`n>> Watchers iniciados em jobs paralelos." -ForegroundColor Yellow
Write-Host "Use 'Get-Job' para listar e 'Receive-Job <id>' para ver logs." -ForegroundColor DarkGray
Write-Host "Ou abra outro terminal e rode manualmente:" -ForegroundColor DarkGray
Write-Host "  kubectl get pods -w" -ForegroundColor DarkGray
Write-Host "  kubectl get hpa php -w" -ForegroundColor DarkGray
Write-Host "--------------------------------------------" -ForegroundColor Cyan

