#C:
#cd C:/Users/Administrator/Documents/edi_energy_mirror/
git pull
rm edi_energy_de/*.html
rm edi_energy_de/future/*.pdf
rm edi_energy_de/current/*.pdf
rm edi_energy_de/past/*.pdf

python download_and_post_process.py
git add edi_energy_de/*.html
git add --no-ignore-removal edi_energy_de/future/*.pdf
git add --no-ignore-removal edi_energy_de/current/*.pdf
git add --no-ignore-removal edi_energy_de/past/*.pdf
git commit -m "edi energy mirror cronjob"
git push
