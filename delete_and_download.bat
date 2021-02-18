C:
cd C:/Users/Administrator/Documents/edi_energy_mirror/
git pull
python download_and_post_process.py
git add edi_energy_de/*.html
git add --no-ignore-removal edi_energy_de/future/*
git add --no-ignore-removal edi_energy_de/current/*
git add --no-ignore-removal edi_energy_de/past/*
git commit -m "edi energy mirror cronjob"
git push
