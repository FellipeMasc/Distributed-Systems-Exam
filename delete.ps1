# cleanup-lab.ps1

Write-Host "============================================" -ForegroundColor Red
Write-Host "   LIMPEZA TOTAL DO LAB KUBERNETES (CSC-27) " -ForegroundColor Red
Write-Host "============================================"

# 1. REMOVER FERRAMENTAS DE CAOS (Versão Monkey e Robot para garantir)
Write-Host ">> [1/6] Removendo Agentes do Caos..." -ForegroundColor Yellow
# Deleta CronJobs
kubectl delete cronjob chaos-robot --ignore-not-found=true
# Deleta Jobs criados pelos CronJobs
kubectl delete job -l job-name=chaos-robot --ignore-not-found=true
# Deleta Permissões (RBAC)
kubectl delete sa  chaos-robot-sa --ignore-not-found=true
kubectl delete role chaos-robot-role --ignore-not-found=true
kubectl delete rolebinding chaos-robot-rolebinding --ignore-not-found=true

# 2. REMOVER APLICAÇÕES (php-apache E nginx-app)
Write-Host ">> [2/6] Removendo Aplicações e Serviços..." -ForegroundColor Yellow
# Deleta Deployments
kubectl delete deploy php-apache nginx-app --ignore-not-found=true
# Deleta Services
kubectl delete svc php-apache nginx-app --ignore-not-found=true
# Deleta HPA (Autoscaler)
kubectl delete hpa php-apache nginx-app --ignore-not-found=true

# 3. REMOVER GERADOR DE CARGA
Write-Host ">> [3/6] Parando Load Generator..." -ForegroundColor Yellow
kubectl delete pod load-generator --ignore-not-found=true

# 4. LIMPEZA FINAL VIA ARQUIVOS (REDE DE SEGURANÇA)
Write-Host ">> [4/6] Varredura final por arquivos..." -ForegroundColor Yellow
# Tenta deletar baseado nos arquivos caso algo tenha escapado pelos nomes
kubectl delete -f app-kubernetes.yaml --ignore-not-found=true
kubectl delete -f chaos-robot.yaml --ignore-not-found=true

# 5. REMOVER RÉPLICAS ÓRFÃS
Write-Host ">> [5/6] Removendo ReplicaSets órfãos..." -ForegroundColor Yellow
kubectl delete rs -l run=php-apache --ignore-not-found=true
kubectl delete rs -l app=nginx-app --ignore-not-found=true

# 6. VERIFICAÇÃO
Write-Host ">> [6/6] Aguardando o cluster limpar (8s)..." -ForegroundColor Cyan
Start-Sleep -Seconds 8

Write-Host "============================================" -ForegroundColor Green
Write-Host "   ESTADO FINAL (Deve estar vazio abaixo)   " -ForegroundColor Green
Write-Host "============================================"
# Mostra tudo, exceto o serviço padrão do kubernetes
kubectl get all
Write-Host "============================================" -ForegroundColor Green
Write-Host "AMBIENTE LIMPO! Pronto para rodar 'reset-simulation.ps1'"


