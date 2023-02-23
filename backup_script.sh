#!/bin/bash

## registrarsi via ssh al QNAP come utente di default 'admin'
## salire sul container e scegliere la cartella temporanea di salvataggio del backup(eg tmp)
# docker exec -it postgres-db bash

## setup crontab per esecuzione script
## rendere eseguibile il file
# chmod +x ../share/Multimedia/05_Documenti/Flask/syd_erp/backup_script.sh

## aggiungere riga a crontab
# vi /etc/config/crontab
# 0 13 * * * /share/Multimedia/05_Documenti/Flask/syd_erp/backup_script.sh > /share/Multimedia/BK_PostgresDB/syd_erp/backup_log.txt 2>&1

## riavviare il servizio crontab
# crontab /etc/config/crontab && /etc/init.d/crond.sh restart

## Define the maximum number of backups to keep
max_backups=14

## Define the path to the backup directory
backup_dir="/share/Multimedia/BK_PostgresDB/syd_erp"

## Count the number of backups in the directory
num_backups=$(find $backup_dir | wc -l)
wait

## If the number of backups exceeds the maximum, delete the oldest
if [ "$num_backups" -gt $max_backups ]; then
  oldest_backup=$(find -t $backup_dir | tail -1)
  rm "$backup_dir/$oldest_backup"
fi
wait

## print current folder
# sudo pwd

## Run the backup command inside container
sudo docker exec postgres-db pg_dump -U "postgres" -F t -f "tmp/dump.tar" syd_erp_db
wait

## copy from container and save in folder backup
sudo docker cp postgres-db:/tmp/dump.tar "$backup_dir/db_syd_erp_$(date +%Y%m%d_%H%M).tar"
wait
