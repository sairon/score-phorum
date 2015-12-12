#!/usr/bin/env bash

# use Czech mirror for APT
sudo sed -i 's;/archive.ubuntu;/cz.archive.ubuntu;g' /etc/apt/sources.list

# install required packages
sudo apt-get update
sudo apt-get install -y --no-install-recommends postgresql virtualenvwrapper \
    libfreetype6-dev libjpeg62-dev libpng12-dev postgresql-server-dev-9.3 python-dev

# prepare virtualenv
sudo mkdir /opt/virtualenv
chown vagrant:vagrant /opt/virtualenv
export WORKON_HOME=/opt/virtualenv
. /usr/share/virtualenvwrapper/virtualenvwrapper_lazy.sh
mkvirtualenv score-phorum
pip install -r /vagrant/requirements/debug.txt
echo "export DJANGO_SETTINGS_MODULE=score.settings.debug" >> "/opt/virtualenv/score-phorum/bin/postactivate"

# add venvwrapper init to bashrc
echo "export WORKON_HOME=/opt/virtualenv" >> /home/vagrant/.bashrc
echo ". /usr/share/virtualenvwrapper/virtualenvwrapper_lazy.sh" >> /home/vagrant/.bashrc
echo "workon score-phorum" >> /home/vagrant/.bashrc

# create database
sudo su postgres -c "createuser -DRS score"
sudo su postgres -c "psql -c \"ALTER USER score WITH PASSWORD 'score'\""
sudo su postgres -c "createdb -O score score"

# create local settings (do not rewrite current)
SECRET_KEY=$(openssl rand -base64 64 | tr -d '\n')
LOCAL_SETTINGS=/vagrant/score/settings/local_settings.json
[ -f ${LOCAL_SETTINGS} ] || cat > ${LOCAL_SETTINGS} <<JSON
{
  "SECRET_KEY": "${SECRET_KEY}",
  "DB_HOST": "localhost",
  "DB_NAME": "score",
  "DB_USER": "score",
  "DB_PASSWORD": "score"
}
JSON
