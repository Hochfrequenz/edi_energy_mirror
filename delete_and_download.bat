C:
cd C:/Users/Administrator/Documents/edi_energy_mirror/
git pull
cd edi_energy_de/future
del *.pdf
cd ../current/
del *.pdf
cd ../past/
del *.pdf
cd ../../
python download_and_post_process.py
git add edi_energy_de/*.html
git add --no-ignore-removal edi_energy_de/future/*.pdf
git add --no-ignore-removal edi_energy_de/current/*.pdf
git add --no-ignore-removal edi_energy_de/past/*.pdf
git commit -m "edi energy mirror cronjob"
git push
