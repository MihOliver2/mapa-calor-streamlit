@echo off
cd /d "C:\CMapaCalorStreamlit"
echo 🔄 Atualizando app do Streamlit...
git add .
git commit -m "Atualização automática - %date% %time%"
git push
echo ✅ Atualização enviada com sucesso!
pause
