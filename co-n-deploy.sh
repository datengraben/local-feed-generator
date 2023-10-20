
git commit -m "Latest data $(date -u)" \
	&& git checkout -- atom.xml \
	&& rsync -avh atom.xml root@shannes.de:/var/www/vhosts/datengraben.com/httpdocs/giessen-aktuelles.atom.xml
