#!/usr/bin/env bash
# R7: clone one act's original demo snapshot into a throwaway scratch DB, or drop it.
# Run inside the mariadb container with MYSQL_PWD set:
#   scratch_clone.sh clone <act> <db_user>   |   scratch_clone.sh drop <act>
set -euo pipefail
mode=$1 act=$2
case "$act" in [1-9]) ;; *) echo "bad act" >&2; exit 2 ;; esac
src="_2bd5b09209543e8e_a${act}_o"
dst="r7e_scratch_a${act}"
if [ "$mode" = drop ]; then
	mariadb -uroot -e "DROP DATABASE IF EXISTS \`${dst}\`"
	echo "dropped ${dst}"
	exit 0
fi
user=$3
mariadb -uroot -e "DROP DATABASE IF EXISTS \`${dst}\`; CREATE DATABASE \`${dst}\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
mariadb-dump -uroot --single-transaction --quick --routines "${src}" | mariadb -uroot "${dst}"
mariadb -uroot -e "GRANT ALL PRIVILEGES ON \`${dst}\`.* TO '${user}'@'%'; FLUSH PRIVILEGES"
echo "cloned ${src} -> ${dst}"
